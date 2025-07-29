"""
Describe command implementation for ksub.
"""
import typer
from rich.console import Console
from typing import Optional
from rich.panel import Panel
from rich.syntax import Syntax

app = typer.Typer(help="Describe Kubernetes jobs")
console = Console()


@app.callback()
def callback():
    """Describe Kubernetes jobs."""
    pass


@app.command()
def job(
    job_id: str = typer.Argument(..., help="Job ID to describe"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table (default), json, yaml"
    ),
    show_yaml: bool = typer.Option(
        False,
        "--yaml",
        "-y",
        help="Show full YAML specification"
    ),
):
    """
    Show detailed information about a Kubernetes job.

    Examples:
        ksub describe <job-id>
        ksub describe <job-id> --output json
        ksub describe <job-id> --yaml
    """
    from ksub.kubernetes.client import describe_job
    from ksub.utils.formatting import format_output
    from ksub.config.user_config import validate_namespace

    # Validate namespace before proceeding
    namespace_valid, error_message = validate_namespace()
    if not namespace_valid:
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        console.print("[bold yellow]⚠️ ksub cannot continue without a valid namespace. Please run 'ksub init' to set up your configuration.[/bold yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Describing job:[/bold] {job_id}")

    try:
        # Get the job description
        description = describe_job(job_id)

        # Format the description based on output option
        if output == "json":
            import json
            console.print(json.dumps(description, indent=2, default=str))
        elif output == "yaml":
            import yaml
            console.print(yaml.dump(description, default_flow_style=False, default_style=None))
        else:
            # Default rich formatted output
            from rich.table import Table

            # Job details panel
            job_details = Table.grid(padding=1)
            job_details.add_column(style="cyan", justify="right")
            job_details.add_column(style="green")

            job_details.add_row("Job ID:", description["job_id"])
            job_details.add_row("Name:", description["name"])
            job_details.add_row("Namespace:", description["namespace"])

            # Add run_id and job_name if they exist in labels
            if "labels" in description and description["labels"]:
                if "run_id" in description["labels"]:
                    job_details.add_row("Run ID:", description["labels"]["run_id"])
                if "job_name" in description["labels"]:
                    job_details.add_row("Job Name:", description["labels"]["job_name"])

            # Status information
            status = description["status"]
            job_details.add_row("Status:", status.get("status", "Unknown"))
            job_details.add_row("Active:", str(status.get("active", 0)))
            job_details.add_row("Succeeded:", str(status.get("succeeded", 0)))
            job_details.add_row("Failed:", str(status.get("failed", 0)))

            if status.get("created_at"):
                job_details.add_row("Created:", str(status.get("created_at")))
            if status.get("completion_time"):
                job_details.add_row("Completed:", str(status.get("completion_time")))

            console.print(Panel(job_details, title=f"Job: {description['name']}", expand=False))

            # Pod information
            if description["pods"]:
                pod_table = Table(title="Pods")
                pod_table.add_column("Name", style="cyan")
                pod_table.add_column("Phase", style="green")
                pod_table.add_column("Node")
                pod_table.add_column("IP")
                pod_table.add_column("Start Time")

                for pod in description["pods"]:
                    pod_table.add_row(
                        pod["name"],
                        pod["phase"],
                        pod["node"],
                        pod["ip"],
                        str(pod["start_time"])
                    )

                console.print(pod_table)

                # Container statuses for each pod
                for pod in description["pods"]:
                    if pod["container_statuses"]:
                        container_table = Table(title=f"Containers for Pod: {pod['name']}")
                        container_table.add_column("Name", style="cyan")
                        container_table.add_column("Ready", style="green")
                        container_table.add_column("Restarts")
                        container_table.add_column("State")

                        for container in pod["container_statuses"]:
                            container_table.add_row(
                                container["name"],
                                str(container["ready"]),
                                str(container["restart_count"]),
                                container["state"]
                            )

                        console.print(container_table)

            # Show YAML if requested
            if show_yaml:
                yaml_syntax = Syntax(description["yaml"], "yaml", theme="monokai", line_numbers=True)
                console.print(Panel(yaml_syntax, title="YAML Specification", expand=False))

    except Exception as e:
        error_message = str(e)
        if output == "json":
            import json
            console.print(json.dumps({"job_id": job_id, "error": error_message}))
        elif output == "yaml":
            import yaml
            console.print(yaml.dump({"job_id": job_id, "error": error_message}))
        else:
            console.print(f"[bold red]Error describing job:[/bold red] {error_message}")
