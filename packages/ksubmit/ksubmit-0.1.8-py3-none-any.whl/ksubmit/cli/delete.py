"""
Delete command implementation for ksubmit.
"""
import typer
from rich.console import Console
from typing import Optional

app = typer.Typer(help="Delete Kubernetes jobs")
console = Console()


@app.callback()
def callback():
    """Delete Kubernetes jobs."""
    pass


@app.command()
def job(
    job_id: str = typer.Argument(..., help="Job ID to delete"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: text (default), json, yaml"
    ),
):
    """
    Delete a Kubernetes job.

    Examples:
        ksubmit delete <job-id>
        ksubmit delete <job-id> --output json
    """
    from ksubmit.kubernetes.client import delete_job
    from ksubmit.utils.formatting import format_output
    from ksubmit.config.user_config import validate_namespace

    # Validate namespace before proceeding
    namespace_valid, error_message = validate_namespace()
    if not namespace_valid:
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        console.print("[bold yellow]⚠️ ksubmit cannot continue without a valid namespace. Please run 'ksubmit init' to set up your configuration.[/bold yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Deleting job:[/bold] {job_id}")

    try:
        # Delete the job
        result = delete_job(job_id)
        
        # Format the result based on output option
        if output == "json":
            import json
            formatted_result = json.dumps({"job_id": job_id, "deleted": result})
        elif output == "yaml":
            import yaml
            formatted_result = yaml.dump({"job_id": job_id, "deleted": result})
        else:
            formatted_result = f"[bold green]✓[/bold green] Job {job_id} deleted successfully"
        
        # Output the result
        console.print(formatted_result)
    except Exception as e:
        error_message = str(e)
        if output == "json":
            import json
            console.print(json.dumps({"job_id": job_id, "error": error_message}))
        elif output == "yaml":
            import yaml
            console.print(yaml.dump({"job_id": job_id, "error": error_message}))
        else:
            console.print(f"[bold red]Error deleting job:[/bold red] {error_message}")