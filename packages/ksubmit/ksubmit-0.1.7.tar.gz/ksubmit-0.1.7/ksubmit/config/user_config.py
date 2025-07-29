"""
User configuration module for ksubmit.
"""
import os
import yaml
import re
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from ksubmit.config.constants import CONFIG_DIR, CONFIG_FILE, SECRETS_FILE

console = Console()


def slugify_key(key: str) -> str:
    """
    Slugify a configuration key name.

    Args:
        key: Configuration key name to slugify

    Returns:
        Slugified key name (lowercase, trimmed)
    """
    # Convert to lowercase and trim whitespace
    key = key.lower().strip()
    # Replace any space or symbol with underscore
    return re.sub(r'[^a-z0-9_]', '_', key)


def validate_email(email: str) -> bool:
    """
    Validate that the email address is in a valid format.

    Args:
        email: Email address to validate

    Returns:
        True if the email is valid, False otherwise
    """
    # Simple regex for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def normalize_email(email: str) -> str:
    """
    Normalize an email address for use as a label value.

    Args:
        email: Email address to normalize

    Returns:
        Normalized email address (e.g., john.doe@example.com -> john.doe_example.com)
    """
    # Replace @ with _ and remove any other invalid characters
    return re.sub(r'[^a-zA-Z0-9._-]', '_', email.replace('@', '_'))


def get_config() -> Dict[str, Any]:
    """
    Get the user configuration from the config file.

    Returns:
        Dict containing user configuration
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception as e:
        console.print(f"[bold yellow]Warning:[/bold yellow] Error reading configuration: {str(e)}")
        return {}


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save the user configuration to the config file.

    Args:
        config: Dict containing user configuration

    Returns:
        True if successful, False otherwise
    """
    # Ensure config directory exists
    CONFIG_DIR.mkdir(exist_ok=True)

    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f)
        return True
    except Exception as e:
        console.print(f"[bold red]Error saving configuration:[/bold red] {str(e)}")
        return False


def update_config(updates: Dict[str, Any]) -> bool:
    """
    Update the user configuration with the provided values.

    Args:
        updates: Dict containing configuration updates

    Returns:
        True if successful, False otherwise
    """
    # Validate email if it's being updated
    if 'email' in updates and not validate_email(updates['email']):
        console.print("[bold red]Invalid email format.[/bold red] Please enter a valid email address.")
        return False

    config = get_config()
    config.update(updates)
    success = save_config(config)

    # If email was updated, update the secrets.env file
    if success and 'email' in updates:
        create_secrets_env_file()

    return success


def initialize_config(namespace: Optional[str], email: Optional[str]) -> bool:
    """
    Initialize user configuration.

    Args:
        namespace: Kubernetes namespace to use
        email: User email for job identification

    Returns:
        True if successful, False otherwise
    """
    import subprocess
    from typer import prompt
    from rich.prompt import Prompt

    # Import here to avoid circular imports
    from ksubmit.kubernetes.client import (
        get_kubernetes_contexts, 
        set_kubernetes_context, 
        check_namespace_exists,
        check_namespace_label,
        check_admin_storage_transfer_pod,
        check_shared_volume_mounts
    )

    # Ensure config directory exists
    CONFIG_DIR.mkdir(exist_ok=True)

    config = get_config()
    existing_config = bool(config)

    if existing_config:
        console.print("[bold]Updating existing configuration...[/bold]")
    else:
        console.print("[bold]Creating new configuration...[/bold]")

    # Step 1: Select Kubernetes Cluster Context
    console.print("\n[bold]Step 1: Select Kubernetes Cluster Context[/bold]")

    # Get Kubernetes contexts
    contexts = get_kubernetes_contexts()
    if not contexts:
        console.print("[bold red]No Kubernetes contexts found. Please configure kubectl.[/bold red]")
        return False

    # Display available contexts
    console.print("\n[bold]Available Kubernetes contexts:[/bold]")
    for i, ctx in enumerate(contexts):
        active_marker = " [green](active)[/green]" if ctx["active"] else ""
        console.print(f"{i+1}. {ctx['name']} - Cluster: {ctx['cluster']}, User: {ctx['user']}{active_marker}")

    # Let user select a context
    default_context = next((i+1 for i, ctx in enumerate(contexts) if ctx["active"]), 1)
    context_choice = Prompt.ask(
        "Select Kubernetes cluster context",
        default=str(default_context),
        choices=[str(i+1) for i in range(len(contexts))]
    )
    selected_context = contexts[int(context_choice) - 1]

    # Set the selected context
    if not selected_context["active"]:
        console.print(f"Setting context to [cyan]{selected_context['name']}[/cyan]")
        set_kubernetes_context(selected_context["name"])
        console.print(f"[bold green]✔️[/bold green] Cluster set to: {selected_context['name']}")
    else:
        console.print(f"[bold green]✔️[/bold green] Using current cluster: {selected_context['name']}")

    # Save context information
    config['context'] = selected_context["name"]
    config['cluster'] = selected_context["cluster"]
    config['user'] = selected_context["user"]

    # Step 2: Ask for Email
    console.print("\n[bold]Step 2: Enter Your Email[/bold]")

    # Validate email
    valid_email = False
    existing_email = config.get('email', '')
    while not valid_email:
        if not email:
            prompt_text = "Enter your email"
            if existing_email and validate_email(existing_email):
                email = prompt(prompt_text, default=existing_email)
            else:
                email = prompt(prompt_text)

        if validate_email(email):
            valid_email = True
            config['email'] = email
        else:
            console.print("[bold red]Invalid email format.[/bold red] Please enter a valid email address.")
            email = None  # Reset email to prompt again

    # Normalize email for use as a label
    safe_email = normalize_email(email)
    config['safe_email'] = safe_email
    console.print(f"Email normalized to: [cyan]{safe_email}[/cyan]")

    # Step 3: Check That User Namespace Exists
    console.print("\n[bold]Step 3: Check That User Namespace Exists[/bold]")

    # Get default username using whoami
    try:
        username = subprocess.check_output(['whoami']).decode('utf-8').strip()
        console.print(f"Detected username: [cyan]{username}[/cyan]")
    except Exception:
        username = "user"
        console.print("[yellow]Could not detect username, using default[/yellow]")

    # Use provided namespace or construct default namespace
    if not namespace:
        namespace = f"{username}"
        console.print(f"Using default namespace: [cyan]{namespace}[/cyan]")
    else:
        console.print(f"Using provided namespace: [cyan]{namespace}[/cyan]")

    config['namespace'] = namespace

    # Check if namespace exists
    namespace_exists, error_message = check_namespace_exists(namespace)
    if not namespace_exists:
        console.print(f"[bold red]❌[/bold red] {error_message}")
        console.print(f"Ask your admin to create it:")
        console.print(f"kubectl create namespace {namespace}")
        return False

    # Step 4: Check Namespace Is Labeled with Email
    console.print("\n[bold]Step 4: Check Namespace Is Labeled with Email[/bold]")

    # Check if namespace has the email label
    has_label, error_message = check_namespace_label(namespace, "ksubmit/email", safe_email)
    if not has_label:
        console.print(f"[bold red]❌[/bold red] Email label mismatch.")
        console.print(f"Ask admin to fix:")
        console.print(f"kubectl label namespace {namespace} ksubmit/email={safe_email} --overwrite")
        return False

    # Step 5: Check Admin Storage Transfer Pod Exists
    console.print("\n[bold]Step 5: Check Admin Storage Transfer Pod Exists[/bold]")

    # Check if admin storage transfer pod exists
    pod_exists, error_message = check_admin_storage_transfer_pod()
    if not pod_exists:
        console.print(f"[bold red]❌[/bold red] {error_message}")
        console.print(f"Ask admin to deploy it:")
        console.print(f"kubectl apply -f ksubmit-storage-transfer.yaml -n ksubmit-admin")
        return False

    # Step 6: Check Shared Volume Mounts Exist
    console.print("\n[bold]Step 6: Check Shared Volume Mounts Exist[/bold]")

    # Check if shared volume mounts exist
    mounts_exist, error_message = check_shared_volume_mounts(namespace)
    if not mounts_exist:
        console.print(f"[bold red]❌[/bold red] {error_message}")
        console.print(f"Ask admin to run:")
        console.print(f"kubectl apply -f ksubmit-shared-cloud-pvc.yaml -n {namespace}")
        return False

    # Step 7: Save to Local Config
    console.print("\n[bold]Step 7: Save to Local Config[/bold]")

    # Add additional configuration
    config['cloud_mount'] = "/mnt/cloud"
    config['scratch_dir'] = f"/mnt/cloud/scratch/{namespace}/"

    # Set default max folder size if not already set
    if 'max_folder_size' not in config:
        config['max_folder_size'] = 200

    # Save config
    success = save_config(config)
    if success:
        console.print(f"Configuration saved to [cyan]{CONFIG_FILE}[/cyan]")
    else:
        console.print("[bold red]✗[/bold red] Failed to save configuration.")
        return False

    # Create secrets.env file
    create_secrets_env_file()

    # Final output
    console.print("\n[bold green]Success[/bold green]")
    console.print(f"[bold green]✔️[/bold green] Cluster set to: {selected_context['name']}")
    console.print(f"[bold green]✔️[/bold green] Email verified and namespace: {namespace}")
    console.print(f"[bold green]✔️[/bold green] ksubmit-storage-transfer pod is active")
    console.print(f"[bold green]✔️[/bold green] Shared volume(s) detected")
    console.print(f"[bold green]✔️[/bold green] You can read/write to your personal scratch space in: [cyan]{config['scratch_dir']}[/cyan]")
    console.print(f"[bold green]✔️[/bold green] When using [cyan]-mount samples=./example/local/folder[/cyan], your files will be in: [cyan]{config['scratch_dir']}samples/[/cyan]")
    console.print(f"[bold green]✔️[/bold green] ksubmit is ready to submit jobs")

    return True


def get_namespace() -> str:
    """
    Get the user's Kubernetes namespace from config.

    Returns:
        Namespace string or default if not configured
    """
    config = get_config()
    return config.get('namespace', 'default')


def validate_namespace() -> tuple[bool, Optional[str]]:
    """
    Validate that the configured namespace exists and is accessible.

    Returns:
        Tuple of (valid, error_message):
        - valid: True if namespace exists and is accessible, False otherwise
        - error_message: Error message if failed, None if successful
    """
    from ksubmit.kubernetes.client import check_namespace_exists

    namespace = get_namespace()
    return check_namespace_exists(namespace)


def get_email() -> Optional[str]:
    """
    Get the user's email from config.

    Returns:
        Email string or None if not configured
    """
    config = get_config()
    return config.get('email')


def get_safe_email() -> Optional[str]:
    """
    Get the user's normalized email from config.

    Returns:
        Normalized email string or None if not configured
    """
    config = get_config()
    return config.get('safe_email')


def get_image_pull_secret() -> Optional[str]:
    """
    Get the image pull secret from config.

    Returns:
        Image pull secret name or None if not configured
    """
    config = get_config()
    return config.get('imagePullSecret')


def get_context() -> Optional[str]:
    """
    Get the Kubernetes context from config.

    Returns:
        Context name or None if not configured
    """
    config = get_config()
    return config.get('context')


def get_cloud_mount() -> Optional[str]:
    """
    Get the cloud mount path from config.

    Returns:
        Cloud mount path or None if not configured
    """
    config = get_config()
    return config.get('cloud_mount')


def get_scratch_dir() -> Optional[str]:
    """
    Get the scratch directory path from config.

    Returns:
        Scratch directory path or None if not configured
    """
    config = get_config()
    return config.get('scratch_dir')


def get_max_folder_size() -> int:
    """
    Get the maximum folder size in MB from config.

    Returns:
        Maximum folder size in MB (default: 200)
    """
    config = get_config()
    return config.get('max_folder_size', 200)


def get_username() -> str:
    """
    Get the username from the config or derive it from the email.

    This is used for organizing user files in shared storage.

    Returns:
        Username string
    """
    config = get_config()

    # First check if username is explicitly set in config
    if "username" in config:
        return config["username"]

    # Otherwise derive from email
    email = get_email()
    if email:
        # Extract username part from email (before @)
        username = email.split('@')[0]
        # Remove any special characters
        username = re.sub(r'[^a-zA-Z0-9_-]', '', username)
        return username

    # Fallback to a default if no email is set
    return "default-user"


def create_secrets_env_file() -> bool:
    """
    Create a secrets.env file in the config directory.
    Sets OWNER=email in the file while preserving other environment variables.

    Returns:
        True if successful, False otherwise
    """
    # Ensure config directory exists
    CONFIG_DIR.mkdir(exist_ok=True)

    try:
        # Get the email and safe_email from config
        config = get_config()
        email = config.get('email')
        safe_email = config.get('safe_email')

        # Initialize with default header
        env_vars = {
            "# Environment variables for ksubmit": None,
            "# Format: KEY=VALUE": None
        }

        # Read existing secrets file if it exists
        if SECRETS_FILE.exists():
            with open(SECRETS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        if key != "OWNER":  # Don't preserve old OWNER value
                            env_vars[key] = value

        # Set OWNER to current email
        if email:
            env_vars["OWNER"] = email

        # Set SAFE_EMAIL to normalized email if available
        if safe_email:
            env_vars["SAFE_EMAIL"] = safe_email

        # Write updated secrets file
        with open(SECRETS_FILE, 'w') as f:
            f.write("# Environment variables for ksubmit\n")
            f.write("# Format: KEY=VALUE\n")
            for key, value in env_vars.items():
                if value is not None:  # Skip header comments
                    f.write(f"{key}={value}\n")

        console.print(f"Created/updated secrets file at [cyan]{SECRETS_FILE}[/cyan]")
        return True
    except Exception as e:
        console.print(f"[bold red]Error creating secrets file:[/bold red] {str(e)}")
        return False
