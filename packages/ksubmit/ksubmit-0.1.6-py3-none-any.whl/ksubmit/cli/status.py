"""
Status command implementation for ksub.
"""
import typer
from rich.console import Console
from typing import Optional

app = typer.Typer(help="Get status of Kubernetes jobs")
console = Console()


@app.callback()
def callback():
    """Get status of Kubernetes jobs."""
    pass


@app.command()
def job(
    job_id: str = typer.Argument(..., help="Job ID to get status for"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table (default), json, yaml"
    ),
):
    """
    Get the status of a Kubernetes job.

    Examples:
        ksub status <job-id>
        ksub status <job-id> --output json
    """
    from ksub.kubernetes.client import get_job_status
    from ksub.utils.formatting import format_output
    from ksub.config.user_config import validate_namespace

    # Validate namespace before proceeding
    namespace_valid, error_message = validate_namespace()
    if not namespace_valid:
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        console.print("[bold yellow]⚠️ ksub cannot continue without a valid namespace. Please run 'ksub init' to set up your configuration.[/bold yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Getting status for job:[/bold] {job_id}")

    try:
        # Get the job status
        status = get_job_status(job_id)

        # Format the status based on output option
        if output:
            format_output([status], output)
        else:
            # Default table format for a single job
            from rich.table import Table

            table = Table(title=f"Status for Job: {job_id}")
            table.add_column("FIELD", style="cyan")
            table.add_column("VALUE", style="green")

            # Add rows for each status field
            # First add run_id and job_name if they exist in labels
            if "labels" in status and status["labels"]:
                if "run_id" in status["labels"]:
                    table.add_row("run_id", status["labels"]["run_id"])
                if "job_name" in status["labels"]:
                    table.add_row("job_name", status["labels"]["job_name"])

            # Then add other status fields
            for key, value in status.items():
                if key == "conditions" or key == "labels":
                    # Handle conditions and labels separately
                    continue
                table.add_row(key, str(value))

            # Add conditions if present
            if "conditions" in status and status["conditions"]:
                table.add_row("", "")
                table.add_row("CONDITIONS", "")
                for condition in status["conditions"]:
                    for cond_key, cond_value in condition.items():
                        table.add_row(f"  {cond_key}", str(cond_value))

            console.print(table)
    except Exception as e:
        error_message = str(e)
        if output == "json":
            import json
            console.print(json.dumps({"job_id": job_id, "error": error_message}))
        elif output == "yaml":
            import yaml
            console.print(yaml.dump({"job_id": job_id, "error": error_message}))
        else:
            console.print(f"[bold red]Error getting job status:[/bold red] {error_message}")
