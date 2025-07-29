"""
Main CLI entry point for ksubmit.
"""
import typer
from rich.console import Console
from typing import Optional
import os
from pathlib import Path

from ksubmit import __version__
from ksubmit.cli import submit, config, logs, list, delete, status, describe, lint

# Create typer app
app = typer.Typer(
    help="ksubmit - Kubernetes Job Submission Tool",
    add_completion=True,
)

# Create rich console for colored output
console = Console()

# Add subcommands
app.add_typer(submit.app, name="submit")
app.add_typer(config.app, name="config")
app.add_typer(logs.app, name="logs")
app.add_typer(list.app, name="list")
app.add_typer(delete.app, name="delete")
app.add_typer(status.app, name="status")
app.add_typer(describe.app, name="describe")
app.add_typer(lint.app, name="lint")


@app.callback()
def callback():
    """
    ksubmit - Kubernetes Job Submission Tool

    A Python-based CLI tool that parses shell scripts with UGE-like
    #$ directives and translates them into Kubernetes jobs.
    """
    pass


@app.command("version")
def version():
    """Print the current version of ksubmit."""
    console.print(f"[bold green]ksubmit[/bold green] version: [bold]{__version__}[/bold]")


@app.command("init")
def init(
    namespace: Optional[str] = typer.Option(None, help="Kubernetes namespace to use (defaults to username)"),
    email: Optional[str] = typer.Option(None, help="User email for job identification"),
):
    """
    Initialize user config for submitting jobs via Kubernetes.

    - Selects Kubernetes cluster context from available contexts
    - Asks for email and normalizes it for use as a label
    - Checks that user namespace exists (format: <username>)
    - Verifies namespace is labeled with the email
    - Checks that admin storage transfer pod exists
    - Verifies shared volume mounts exist in the namespace
    - Saves configuration including cloud_mount and scratch_dir paths
    - Creates/updates .ksubmit/secrets.env file with environment variables
    """
    from ksubmit.config.user_config import initialize_config

    if initialize_config(namespace, email):
        console.print("[bold green]✓[/bold green] Configuration initialized successfully!")
    else:
        console.print("[bold red]✗[/bold red] Configuration initialization failed.")


@app.command("run")
def run(
    script_file: Path = typer.Argument(
        ...,
        help="Path to the job script file",
        exists=True
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Generate YAML but don't submit"
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing directories in destination"
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch job progress after submission"
    ),
    timeout: Optional[int] = typer.Option(
        None,
        help="Timeout in seconds when watching job"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: table (default), json"
    ),
):
    """
    Parse a UGER-style shell script, generate Kubernetes job specs,
    mount files/folders, and submit jobs.
    """
    # Call the submit function from the submit module
    submit.submit(
        script_file=script_file,
        dry_run=dry_run,
        overwrite=overwrite,
        watch=watch,
        timeout=timeout,
        output=output
    )


if __name__ == "__main__":
    app()
