"""
Storage module for ksub - provides DuckDB interface for job tracking and file transfer utilities.
"""
import os
import time
import json
import shutil
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import duckdb
from rich.console import Console
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

from ksub.kubernetes.client import check_admin_storage_transfer_pod, initialize_kubernetes_client

console = Console()

# Define storage location
STORAGE_DIR = Path.home() / ".ksub" / "data"
DB_FILE = STORAGE_DIR / "jobs.duckdb"


def initialize_storage():
    """
    Initialize the storage system.

    Creates the storage directory and database if they don't exist.
    """
    # Ensure storage directory exists
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = duckdb.connect(str(DB_FILE))

    # Create tables if they don't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            namespace VARCHAR,
            status VARCHAR,
            created_at TIMESTAMP,
            completed_at TIMESTAMP,
            image VARCHAR,
            commands VARCHAR,
            resources VARCHAR,
            mounts VARCHAR,
            retries INTEGER,
            owner VARCHAR,
            metadata VARCHAR
        )
    """)

    conn.close()


def store_job(
    job_id: str,
    name: str,
    namespace: str,
    status: str = "Pending",
    image: str = "",
    commands: List[str] = None,
    resources: Dict[str, str] = None,
    mounts: List[str] = None,
    retries: int = 0,
    owner: str = "",
    metadata: Dict[str, Any] = None
):
    """
    Store job information in the database.

    Args:
        job_id: Unique job ID
        name: Job name
        namespace: Kubernetes namespace
        status: Job status
        image: Container image
        commands: List of commands
        resources: Resource requests
        mounts: Volume mounts
        retries: Number of retries
        owner: Job owner (email)
        metadata: Additional metadata
    """
    # Ensure storage is initialized
    initialize_storage()

    # Connect to database
    conn = duckdb.connect(str(DB_FILE))

    # Convert complex types to JSON strings
    commands_json = json.dumps(commands or [])
    resources_json = json.dumps(resources or {})
    mounts_json = json.dumps(mounts or [])
    metadata_json = json.dumps(metadata or {})

    # Insert or update job
    conn.execute("""
        INSERT OR REPLACE INTO jobs (
            job_id, name, namespace, status, created_at, completed_at,
            image, commands, resources, mounts, retries, owner, metadata
        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, NULL, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, name, namespace, status, image, commands_json,
        resources_json, mounts_json, retries, owner, metadata_json
    ))

    conn.close()


def update_job_status(job_id: str, status: str, completed: bool = False):
    """
    Update the status of a job.

    Args:
        job_id: Job ID
        status: New status
        completed: Whether the job is completed
    """
    # Ensure storage is initialized
    initialize_storage()

    # Connect to database
    conn = duckdb.connect(str(DB_FILE))

    # Update job status
    if completed:
        conn.execute("""
            UPDATE jobs
            SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        """, (status, job_id))
    else:
        conn.execute("""
            UPDATE jobs
            SET status = ?
            WHERE job_id = ?
        """, (status, job_id))

    conn.close()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job information from the database.

    Args:
        job_id: Job ID

    Returns:
        Dict containing job information or None if not found
    """
    # Ensure storage is initialized
    initialize_storage()

    # Connect to database
    conn = duckdb.connect(str(DB_FILE))

    # Query job
    result = conn.execute("""
        SELECT * FROM jobs WHERE job_id = ?
    """, (job_id,)).fetchone()

    conn.close()

    if not result:
        return None

    # Convert to dict
    columns = [
        "job_id", "name", "namespace", "status", "created_at", "completed_at",
        "image", "commands", "resources", "mounts", "retries", "owner", "metadata"
    ]
    job = dict(zip(columns, result))

    # Parse JSON strings
    job["commands"] = json.loads(job["commands"])
    job["resources"] = json.loads(job["resources"])
    job["mounts"] = json.loads(job["mounts"])
    job["metadata"] = json.loads(job["metadata"])

    # Calculate age and duration
    created_at = job["created_at"]
    completed_at = job["completed_at"]

    # Convert timestamps to local timezone
    if created_at:
        local_tz = datetime.datetime.now().astimezone().tzinfo
        created_at_local = created_at.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
        job["created_at"] = created_at_local

        if completed_at:
            completed_at_local = completed_at.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
            job["completed_at"] = completed_at_local
            duration_seconds = (completed_at_local - created_at_local).total_seconds()
            from ksub.utils.formatting import format_duration
            job["duration"] = format_duration(int(duration_seconds))

        # Calculate age from creation to now
        age_seconds = (time.time() - created_at.timestamp())
        from ksub.utils.formatting import format_duration
        job["age"] = format_duration(int(age_seconds))

    return job


def list_jobs(
    namespace: Optional[str] = None,
    status: Optional[str] = None,
    label: Optional[str] = None,
    owner: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List jobs from the database.

    Args:
        namespace: Filter by namespace
        status: Filter by status
        label: Filter by label (format: key=value)
        owner: Filter by owner
        limit: Maximum number of jobs to return

    Returns:
        List of job dictionaries
    """
    # Ensure storage is initialized
    initialize_storage()

    # Connect to database
    conn = duckdb.connect(str(DB_FILE))

    # Build query
    query = "SELECT * FROM jobs"
    params = []

    where_clauses = []
    if namespace:
        where_clauses.append("namespace = ?")
        params.append(namespace)

    if status:
        where_clauses.append("status = ?")
        params.append(status)

    if owner:
        where_clauses.append("owner = ?")
        params.append(owner)

    # Note: label filtering is done after query execution since labels are stored in metadata JSON

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    # Execute query
    results = conn.execute(query, params).fetchall()

    conn.close()

    # Convert to list of dicts
    columns = [
        "job_id", "name", "namespace", "status", "created_at", "completed_at",
        "image", "commands", "resources", "mounts", "retries", "owner", "metadata"
    ]
    jobs = []

    for result in results:
        job = dict(zip(columns, result))

        # Parse JSON strings
        job["commands"] = json.loads(job["commands"])
        job["resources"] = json.loads(job["resources"])
        job["mounts"] = json.loads(job["mounts"])
        job["metadata"] = json.loads(job["metadata"])

        # Calculate age and duration
        created_at = job["created_at"]
        completed_at = job["completed_at"]

        # Convert timestamps to local timezone
        if created_at:
            local_tz = datetime.datetime.now().astimezone().tzinfo
            created_at_local = created_at.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
            job["created_at"] = created_at_local

            if completed_at:
                completed_at_local = completed_at.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
                job["completed_at"] = completed_at_local
                duration_seconds = (completed_at_local - created_at_local).total_seconds()
                from ksub.utils.formatting import format_duration
                job["duration"] = format_duration(int(duration_seconds))

            # Calculate age from creation to now
            age_seconds = (time.time() - created_at.timestamp())
            from ksub.utils.formatting import format_duration
            job["age"] = format_duration(int(age_seconds))

        jobs.append(job)

    # Filter by label if specified
    if label and jobs:
        # Label should be in format "key=value"
        if "=" in label:
            key, value = label.split("=", 1)
            filtered_jobs = []
            for job in jobs:
                # Check if job has labels in metadata
                metadata = job.get("metadata", {})
                labels = metadata.get("labels", {})
                if labels and key in labels and labels[key] == value:
                    filtered_jobs.append(job)
            jobs = filtered_jobs
        else:
            console = Console()
            console.print(f"[bold yellow]Warning:[/bold yellow] Invalid label format: {label}. Expected format: key=value")

    return jobs


def delete_job_record(job_id: str) -> bool:
    """
    Delete a job record from the database.

    Args:
        job_id: Job ID

    Returns:
        True if successful, False otherwise
    """
    # Ensure storage is initialized
    initialize_storage()

    # Connect to database
    conn = duckdb.connect(str(DB_FILE))

    # Delete job
    conn.execute("""
        DELETE FROM jobs WHERE job_id = ?
    """, (job_id,))

    conn.close()

    return True


def get_running_storage_transfer_pod() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Get the name of a running storage transfer pod.

    Returns:
        Tuple of (success, pod_name, error_message):
        - success: True if a running pod was found, False otherwise
        - pod_name: Name of the running pod if found, None otherwise
        - error_message: Error message if failed, None if successful
    """
    # Check if storage transfer pod is running
    pod_exists, error_message = check_admin_storage_transfer_pod()
    if not pod_exists:
        return False, None, f"Storage transfer pod not available: {error_message}"

    # Initialize Kubernetes client
    initialize_kubernetes_client()
    core_api = client.CoreV1Api()

    try:
        # Get the storage transfer pod
        pods = core_api.list_namespaced_pod(
            namespace="ksub-admin",
            label_selector="app=ksub-storage-transfer"
        )

        if not pods.items:
            return False, None, "No storage transfer pod found"

        # Use the first running pod
        pod = next((p for p in pods.items if p.status.phase == "Running"), None)
        if not pod:
            return False, None, "No running storage transfer pod found"

        return True, pod.metadata.name, None

    except ApiException as e:
        error_message = str(e)
        return False, None, f"Error getting storage transfer pod: {error_message}"


def copy_to_storage_transfer_pod(source_dir: str, username: str, code_dir_name: str = "code", namespace: str = None, dry_run: bool = False, overwrite: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Copy files from a local directory to the storage transfer pod.

    This function is used to copy code files to the shared storage volume
    when a job uses the `-mount code=./path` directive.

    Args:
        source_dir: Path to the source directory to copy
        username: Username to use for the target directory
        code_dir_name: Name of the code directory (default: "code")
        namespace: Kubernetes namespace (default: None)
        dry_run: If True, only output what would be done without actually copying files
        overwrite: If True, overwrite existing directory in destination

    Returns:
        Tuple of (success, error_message):
        - success: True if successful, False otherwise
        - error_message: Error message if failed, None if successful
    """
    from ksub.config.user_config import get_max_folder_size

    # Check if source directory exists
    source_path = Path(source_dir)
    if not source_path.exists() or not source_path.is_dir():
        return False, f"Source directory {source_dir} invalid"

    # Calculate directory size in MB
    dir_size_bytes = sum(f.stat().st_size for f in source_path.glob('**/*') if f.is_file())
    dir_size_mb = dir_size_bytes / (1024 * 1024)

    # Get max folder size from config
    max_folder_size = get_max_folder_size()

    # Check if directory size exceeds limit
    if dir_size_mb > max_folder_size:
        console.print(f"[bold red]Error:[/bold red] Directory size ({dir_size_mb:.2f}MB) exceeds the maximum allowed size ({max_folder_size}MB)")
        console.print(f"[yellow]You can increase the limit by editing the 'max_folder_size' value in {Path.cwd() / '.ksub' / 'config.yaml'}[/yellow]")
        console.print(f"[yellow]Warning: Increasing the limit may result in slower processing times.[/yellow]")
        return False, f"Directory size exceeds maximum allowed size"

    # Target directory path inside the pod
    # Use namespace if provided, otherwise use username
    if namespace:
        target_dir = f"/mnt/cloud/scratch/{namespace}/{code_dir_name}"
    else:
        target_dir = f"/mnt/cloud/scratch/{username}/{code_dir_name}"

    # If dry run, just output what would be done and return
    if dry_run:
        console.print(f"[yellow]DRY RUN:[/yellow] Would copy files from [bold]{source_dir}[/bold] to storage volume at [bold]{target_dir}[/bold]")
        return True, None

    # Check if destination directory already exists
    if not overwrite:
        # Get the running storage transfer pod
        success, pod_name, error_message = get_running_storage_transfer_pod()
        if not success:
            return False, error_message

        # Check if directory exists - use a more robust approach without shell=True
        check_dir_cmd = ["kubectl", "exec", "-n", "ksub-admin", pod_name, "--", "test", "-d", target_dir]
        result = subprocess.run(check_dir_cmd, capture_output=True, text=True)

        # test -d returns 0 if directory exists, non-zero otherwise
        if result.returncode == 0:
            console.print(f"[bold blue]Info:[/bold blue] Destination directory [bold]{target_dir}[/bold] already exists")

            # Ask user if they want to continue with existing directory
            console.print(f"[yellow]Do you want to continue with the existing directory? (y/n)[/yellow]")
            user_input = input().strip().lower()

            if user_input == 'y' or user_input == 'yes':
                console.print(f"[green]Continuing with existing directory at [bold]{target_dir}[/bold][/green]")
                return True, None
            else:
                console.print(f"[yellow]Use --overwrite option to overwrite the existing directory[/yellow]")
                console.print(f"[yellow]Add '--overwrite' to your mount directive: #$ -mount {code_dir_name}={source_dir} --overwrite[/yellow]")
                return False, f"Destination directory already exists"

    # Get the running storage transfer pod
    success, pod_name, error_message = get_running_storage_transfer_pod()
    if not success:
        return False, error_message

    # Create target directory inside pod
    create_dir_cmd = ["kubectl", "exec", "-n", "ksub-admin", pod_name, "--", "mkdir", "-p", target_dir]
    result = subprocess.run(create_dir_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"Failed to create target dir in pod: {result.stderr}"

    # Copy files using kubectl cp with source_dir/. to copy contents
    copy_cmd = ["kubectl", "cp", f"{source_dir}/.", f"ksub-admin/{pod_name}:{target_dir}"]
    console.print(f"[yellow]Copying files from [bold]{source_dir}[/bold] to pod...[/yellow]")
    result = subprocess.run(copy_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"Failed to copy files to pod: {result.stderr}"

    console.print(f"[green]✓[/green] Copied files from [bold]{source_dir}[/bold] to storage volume at [bold]{target_dir}[/bold]")
    return True, None
