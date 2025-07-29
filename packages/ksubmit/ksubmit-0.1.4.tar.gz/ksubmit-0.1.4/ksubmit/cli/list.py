"""
List command implementation for ksub.
"""
import typer
from rich.console import Console
from typing import Optional
from pathlib import Path

app = typer.Typer(help="List resources in Kubernetes")
console = Console()


@app.callback()
def callback():
    """List resources in Kubernetes."""
    pass


@app.command()
def jobs(
    limit: int = typer.Option(
        100,
        "--limit",
        "-n",
        help="Maximum number of jobs to show"
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status (Running, Succeeded, Failed, etc.)"
    ),
    label: Optional[str] = typer.Option(
        None,
        "--label",
        "-l",
        help="Filter by label (format: key=value)"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table (default), json, yaml"
    ),
    source: str = typer.Option(
        "kubernetes",
        "--source",
        help="Source of job data: kubernetes, local, or both (default)"
    ),
    update_storage: bool = typer.Option(
        True,
        "--update-storage/--no-update-storage",
        help="Whether to update local storage with job status from Kubernetes"
    ),
):
    """
    List all Kubernetes jobs with their name, ID, and active status.

    This command displays all jobs in the current namespace. It can fetch job data from:
    - Kubernetes API (live data)
    - Local storage (historical data)
    - Both sources (default, merged with Kubernetes data taking precedence)

    If jobs have been cleared from Kubernetes but exist in local storage, they will
    still be displayed when using 'both' or 'local' as the source.

    When fetching from Kubernetes, job status is automatically updated in local storage
    to ensure historical data is preserved. This can be disabled with --no-update-storage.
    """
    from ksub.utils.storage import list_jobs as list_local_jobs
    from ksub.kubernetes.client import list_jobs as list_k8s_jobs
    from ksub.utils.formatting import format_output
    from ksub.config.user_config import get_namespace, get_email, validate_namespace

    # Validate namespace before proceeding
    namespace_valid, error_message = validate_namespace()
    if not namespace_valid:
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        console.print("[bold yellow]⚠️ ksub cannot continue without a valid namespace. Please run 'ksub init' to set up your configuration.[/bold yellow]")
        raise typer.Exit(1)

    # Get current namespace and email
    namespace = get_namespace()
    email = get_email()

    console.print(f"[bold]Listing jobs in namespace:[/bold] {namespace}")

    # Initialize empty job list
    job_list = []

    # Get jobs from Kubernetes if requested
    source_str = str(source)
    if source_str.lower() in ["kubernetes", "both"]:
        console.print("Fetching jobs from Kubernetes...")
        k8s_jobs = list_k8s_jobs(namespace=namespace, status=status, label=label, limit=limit, update_storage=update_storage)

        if k8s_jobs:
            job_list.extend(k8s_jobs)
            console.print(f"[green]Found {len(k8s_jobs)} jobs in Kubernetes[/green]")
        else:
            console.print("[yellow]No jobs found in Kubernetes[/yellow]")

    # Get jobs from local storage if requested
    if source_str.lower() in ["local", "both"]:
        console.print("Fetching jobs from local storage...")
        local_jobs = list_local_jobs(namespace=namespace, status=status, label=label, limit=limit)

        if local_jobs:
            # If we're using both sources, only add jobs from local storage that don't exist in Kubernetes
            if source_str.lower() == "both":
                k8s_job_ids = {job["job_id"] for job in job_list}
                local_jobs = [job for job in local_jobs if job["job_id"] not in k8s_job_ids]

                if local_jobs:
                    console.print(f"[green]Found {len(local_jobs)} additional jobs in local storage[/green]")
                    job_list.extend(local_jobs)
                else:
                    console.print("[yellow]No additional jobs found in local storage[/yellow]")
            else:
                console.print(f"[green]Found {len(local_jobs)} jobs in local storage[/green]")
                job_list.extend(local_jobs)
        else:
            console.print("[yellow]No jobs found in local storage[/yellow]")

    if not job_list:
        console.print("[yellow]No jobs found from any source.[/yellow]")
        return

    # Format and print jobs
    format_output(job_list, output_format=output)
