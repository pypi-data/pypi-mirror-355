"""
Submit command implementation for ksub.
"""
import typer
from rich.console import Console
from typing import Optional, List
from pathlib import Path

app = typer.Typer(help="Submit jobs to Kubernetes")
console = Console()


@app.callback()
def callback():
    """Submit jobs to Kubernetes."""
    pass


@app.command()
def submit(
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
    callback=None,
):
    """
    Parse a UGER-style shell script, generate Kubernetes job specs,
    mount files/folders, and submit jobs.

    Args:
        script_file: Path to the job script file
        dry_run: Generate YAML but don't submit
        watch: Watch job progress after submission
        timeout: Timeout in seconds when watching job
        output: Output format (table, json)
        callback: Optional callback function to be called for each submitted job
                  with the signature callback(job_id, job_name, metadata)

    Returns:
        A dictionary containing the submitted jobs, failed jobs, and job specs
    """
    from ksub.parsers.dsl import parse_script
    from ksub.kubernetes.job import generate_job_specs, submit_jobs
    from ksub.config.user_config import validate_namespace

    # Validate namespace before proceeding
    namespace_valid, error_message = validate_namespace()
    if not namespace_valid:
        console.print(f"[bold red]Error:[/bold red] {error_message}")
        console.print("[bold yellow]⚠️ ksub cannot continue without a valid namespace. Please run 'ksub init' to set up your configuration.[/bold yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Processing script:[/bold] {script_file}")

    # Lint the script file before parsing
    from ksub.linting.lint import lint_script
    all_lint_results = lint_script(script_file)

    # Filter out informational messages (those with error_code starting with "INFO_")
    errors = [error for error in all_lint_results if not error.error_code.startswith("INFO_")]
    info_messages = [info for info in all_lint_results if info.error_code.startswith("INFO_")]

    # Display informational messages without aborting
    if info_messages:
        console.print(f"[bold blue]Found {len(info_messages)} informational message(s) in {script_file}:[/bold blue]")
        for info in info_messages:
            console.print(f"[blue]Line {info.line_number}:[/blue] [{info.rule_id}] {info.message}")

    # Display and abort for actual errors
    if errors:
        console.print(f"[bold red]Found {len(errors)} error(s) in {script_file}:[/bold red]")
        for error in errors:
            console.print(f"[red]Line {error.line_number}:[/red] [{error.rule_id}] {error.message}")

        # Exit immediately when linting errors are found
        console.print("[yellow]Aborting submission due to linting errors.[/yellow]")
        raise typer.Exit(1)

    # Parse the script file to extract job blocks
    job_blocks = parse_script(script_file)
    console.print(f"📄 Parsed {len(job_blocks)} job block(s).")

    # Generate Kubernetes YAML specs
    job_specs, mount_errors = generate_job_specs(job_blocks, dry_run=dry_run)

    # Exit early if there were mount errors
    if mount_errors:
        console.print("[bold red]Error:[/bold red] Failed to mount one or more directories. Job submission aborted.")
        raise typer.Exit(1)

    if dry_run:
        # Just print the YAML specs
        for name, spec in job_specs.items():
            console.print(f"[bold]Job: {name}[/bold]")
            console.print(spec)
        return

    # Submit the jobs to Kubernetes
    result = submit_jobs(job_specs)
    submitted_jobs = result['submitted']
    failed_jobs = result['failed']

    # Print results for successfully submitted jobs and call callback if provided
    for name, job_id in submitted_jobs.items():
        # Call the callback function if provided
        if callback:
            # Extract metadata from job_specs
            metadata = {}
            if name in job_specs:
                spec = job_specs[name]
                # Extract relevant metadata from the job spec
                if isinstance(spec, dict):
                    metadata = {
                        "image": spec.get("image", ""),
                        "cpu": spec.get("cpu", ""),
                        "memory": spec.get("memory", ""),
                        "gpu": spec.get("gpu", ""),
                    }

            # Call the callback with job_id, job_name, and metadata
            callback(job_id, name, metadata)

    # Print summary
    if failed_jobs:
        if submitted_jobs:
            console.print(f"[bold yellow]⚠️ {len(submitted_jobs)} job(s) submitted, {len(failed_jobs)} job(s) failed.[/bold yellow]")
        else:
            console.print(f"[bold red]❌ No jobs submitted. All {len(failed_jobs)} job(s) failed.[/bold red]")
    else:
        console.print(f"[bold green]✅ All {len(submitted_jobs)} job(s) have been submitted successfully.[/bold green]")

    if watch:
        console.print("[bold yellow]Watching job progress...[/bold yellow]")
        # Implementation for watching job progress would go here

    # Return the result for use by the caller
    return {
        "jobs": submitted_jobs,
        "failed": failed_jobs,
        "job_specs": job_specs
    }
