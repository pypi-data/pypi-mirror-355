"""
Configuration module for ksubmit.
"""
import typer
from rich.console import Console
from typing import Optional
import os
from pathlib import Path
import yaml
from ksubmit.config.constants import CONFIG_DIR, CONFIG_FILE, SECRETS_FILE

app = typer.Typer(help="Manage ksubmit configuration")
console = Console()


@app.callback()
def callback():
    """Manage ksubmit configuration."""
    pass


@app.command("show")
def show():
    """View stored user configuration."""
    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration found. Run 'ksubmit init' to create one.[/yellow]")
        return

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)

        console.print("[bold]Current Configuration:[/bold]")
        for key, value in config.items():
            console.print(f"  [cyan]{key}[/cyan]: {value}")
    except Exception as e:
        console.print(f"[bold red]Error reading configuration:[/bold red] {str(e)}")


def list():
    """List all configuration values."""
    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration found. Run 'kconfig init' to create one.[/yellow]")
        return

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f) or {}

        console.print("[bold]Current Configuration:[/bold]")
        for key, value in config.items():
            console.print(f"  [cyan]{key}[/cyan]: {value}")
    except Exception as e:
        console.print(f"[bold red]Error reading configuration:[/bold red] {str(e)}")


def get(key: str):
    """Get a specific configuration value."""
    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration found. Run 'kconfig init' to create one.[/yellow]")
        return

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f) or {}

        if key in config:
            console.print(f"[cyan]{key}[/cyan]: {config[key]}")
        else:
            console.print(f"[yellow]Configuration key '[cyan]{key}[/cyan]' not found.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error reading configuration:[/bold red] {str(e)}")


def reset():
    """Reset all configuration to default values."""
    if not CONFIG_FILE.exists():
        console.print("[yellow]No configuration found. Nothing to reset.[/yellow]")
        return

    try:
        # Backup the existing config
        if CONFIG_FILE.exists():
            backup_file = CONFIG_FILE.with_suffix('.bak')
            import shutil
            shutil.copy(CONFIG_FILE, backup_file)
            console.print(f"[yellow]Existing configuration backed up to [cyan]{backup_file}[/cyan][/yellow]")

        # Remove the config file
        CONFIG_FILE.unlink(missing_ok=True)
        console.print("[bold green]✓[/bold green] Configuration has been reset.")
        console.print("[yellow]Run 'kconfig init' to create a new configuration.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error resetting configuration:[/bold red] {str(e)}")


@app.command("set")
def set(
    name: str = typer.Argument(..., help="Configuration key name"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """
    Update stored user configuration.

    The name will be slugified (converted to lowercase, trimmed).
    """
    from ksubmit.config.user_config import update_config, slugify_key

    # Slugify the key name
    key = slugify_key(name)

    # Update the configuration
    if update_config({key: value}):
        console.print(f"[bold green]✓[/bold green] Configuration updated successfully! Set [cyan]{key}[/cyan] to [cyan]{value}[/cyan]")
    else:
        console.print("[bold red]✗[/bold red] Failed to update configuration.")


def initialize_config(namespace: Optional[str], email: Optional[str]):
    """Initialize user configuration."""
    # Ensure config directory exists
    CONFIG_DIR.mkdir(exist_ok=True)

    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[bold yellow]Warning:[/bold yellow] {str(e)}")
            config = {}

    # Use provided values or prompt user
    if not namespace:
        namespace = typer.prompt("Enter Kubernetes namespace")
    config['namespace'] = namespace

    if not email:
        email = typer.prompt("Enter your email")
    config['email'] = email

    # Write config
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f)
        console.print(f"Configuration saved to [cyan]{CONFIG_FILE}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error saving configuration:[/bold red] {str(e)}")
