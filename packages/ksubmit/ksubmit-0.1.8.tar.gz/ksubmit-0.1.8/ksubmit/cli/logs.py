"""
Logs command implementation for ksubmit.
"""
import typer
from rich.console import Console
from typing import Optional
from pathlib import Path

app = typer.Typer(help="View logs from Kubernetes jobs")
console = Console()


@app.command("")
def logs(
    job_id: str = typer.Option(..., "--job", "-j", help="Job ID to view logs from"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
    container: Optional[str] = typer.Option(None, "--container", "-c", help="Specific container to view logs from"),
    tail: Optional[int] = typer.Option(None, "--tail", "-n", help="Number of lines to show from the end"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: text (default), json"),
    output_file: Optional[Path] = typer.Option(None, "--output-file", help="Path to file where logs will be written"),
):
    """
    Show logs of a completed or running job. Supports subcontainers.

    Examples:
        ksubmit logs -j <job-id>
        ksubmit logs --job <job-id> --follow
        ksubmit logs -j <job-id> --output-file logs.txt
    """
    from ksubmit.kubernetes.client import get_job_logs
    from ksubmit.config.user_config import validate_namespace

    # Validate namespace before proceeding
    namespace_valid, error_message = validate_namespace()
    if not namespace_valid:
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        console.print("[bold yellow]⚠️ ksubmit cannot continue without a valid namespace. Please run 'ksubmit init' to set up your configuration.[/bold yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Getting logs for job:[/bold] {job_id}")

    try:
        # Use follow option
        should_follow = follow

        logs = get_job_logs(job_id, container=container, tail=tail, follow=should_follow)

        # Format logs based on output option
        if output == "json":
            import json
            formatted_logs = json.dumps({"job_id": job_id, "logs": logs})
        else:
            formatted_logs = logs

        # Output logs to file or console
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(formatted_logs)
                console.print(f"[bold green]✓[/bold green] Logs written to [cyan]{output_file}[/cyan]")
            except Exception as file_error:
                console.print(f"[bold red]Error writing logs to file:[/bold red] {str(file_error)}")
                console.print(formatted_logs)  # Fall back to console output
        else:
            console.print(formatted_logs)
    except Exception as e:
        console.print(f"[bold red]Error getting logs:[/bold red] {str(e)}")
