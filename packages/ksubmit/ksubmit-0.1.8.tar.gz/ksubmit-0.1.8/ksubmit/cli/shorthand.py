"""
Shorthand commands for ksubmit.

This module provides shorthand commands for ksubmit, following the pattern k<command>.
These commands are designed to be more concise and easier to use than the full ksubmit commands.
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from ksubmit import __version__
from ksubmit.cli import submit, config, logs, list, delete, status, describe, lint
from ksubmit.config.user_config import initialize_config
from ksubmit.kubernetes.client import get_job_status, delete_job, describe_job
from ksubmit.utils.database import (
    initialize_database,
    store_job_submission_mapping,
    get_jobs_for_submission,
    get_job_submission_info
)
from ksubmit.utils.identifiers import validate_identifier, generate_submission_id

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Create typer app
app = typer.Typer(
    help="ksubmit Shorthand Commands - Kubernetes Job Submission Tool",
    add_completion=True,
)

# Create rich console for colored output
console = Console()


@app.callback()
def callback():
    """
    ksubmit Shorthand Commands - Kubernetes Job Submission Tool

    A set of shorthand commands for ksubmit, following the pattern k<command>.
    These commands are designed to be more concise and easier to use than the full ksubmit commands.
    """
    pass


@app.command("version")
def kversion():
    """
    Shorthand for 'ksubmit version' - Print the current version of ksubmit.

    Examples:
        kversion
    """
    console.print(f"[bold green]ksubmit[/bold green] version: [bold]{__version__}[/bold]")




@app.command("run")
def krun(
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
        submission_id: Optional[str] = typer.Option(
            None,
            "--submission-id",
            help="Use a specific run ID (for advanced use cases)"
        ),
):
    """
    Shorthand for 'ksubmit run' - Parse a UGER-style shell script and submit jobs.

    Examples:
        krun my_script.sh
        krun my_script.sh --dry-run
        krun my_script.sh --watch
    """
    try:
        # Initialize database
        initialize_database()

        # Generate a submission ID if not provided
        if not submission_id:
            submission_id = generate_submission_id()
        else:
            # Validate the provided submission ID
            submission_id = validate_identifier(submission_id)
            if not submission_id.startswith("run-"):
                console.print(f"[bold red]Error:[/bold red] Invalid run ID format: {submission_id}")
                console.print(
                    "[bold yellow]Run IDs must start with 'run-' followed by at least 8 hex characters.[/bold yellow]")
                console.print("Example: run-64a7b123abcd")
                raise typer.Exit(1)

        # Call the submit function from the submit module with a custom callback
        result = submit.submit(
            script_file=script_file,
            dry_run=dry_run,
            watch=watch,
            timeout=timeout,
            output=output,
            callback=lambda job_id, job_name, metadata: store_job_submission(
                job_id, job_name, submission_id, metadata, script_file
            )
        )

        # If not dry run and jobs were submitted, print the submission ID
        if not dry_run and result and result.get("jobs"):
            console.print(f"\n[bold green]Your run {submission_id} has been stored in database.[/bold green]")
            console.print("Use this run ID to manage all jobs in this submission:")
            console.print(f"  • Check status: [bold]kstat {submission_id}[/bold]")
            console.print(f"  • View logs: [bold]klogs {submission_id}[/bold]")
            console.print(f"  • Get details: [bold]kdesc {submission_id}[/bold]")
            console.print(f"  • Delete jobs: [bold]kdel {submission_id}[/bold]")
            console.print(f"  • List all runs: [bold]klist[/bold]")

        return result
    except typer.Exit as e:
        # Handle typer.Exit exceptions gracefully
        # No need to print an error message as it should have been printed by the submit function
        # Just exit with the same code
        raise typer.Exit(e.exit_code)
    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in krun: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Check if the script file exists: [bold]ls {script_file}[/bold]")
        console.print("  • Lint your script for errors: [bold]klint {script_file}[/bold]")
        console.print("  • Run with --dry-run to debug: [bold]krun {script_file} --dry-run[/bold]")
        raise typer.Exit(1)


def store_job_submission(job_id: str, job_name: str, submission_id: str, metadata: Dict[str, Any], script_file: Path):
    """
    Store job submission information in the database.

    Args:
        job_id: The ID of the job
        job_name: The name of the job
        submission_id: The ID of the submission
        metadata: Additional metadata about the job
        script_file: The path to the script file
    """
    # Add script file path to metadata
    metadata = metadata or {}
    metadata["script_file"] = str(script_file.absolute())

    # Store in database
    store_job_submission_mapping(job_id, submission_id, job_name, metadata)


@app.command("stat")
def kstat(
        identifier: Optional[str] = typer.Argument(None, help="Job ID or Run ID to get status for"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: table (default), json, yaml"),
):
    """
    Shorthand for 'ksubmit status' - Get the status of a Kubernetes job or all jobs in a run.

    Examples:
        kstat <job-id>
        kstat <run-id>
        kstat <job-id> --output json
    """
    try:
        # Validate input
        identifier = validate_identifier(identifier, required=False)

        if identifier and identifier.startswith("run-"):
            # Handle as run ID
            handle_submission_status(identifier, output)
        else:
            # Handle as job ID
            status.job(job_id=identifier, output=output)

    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in kstat: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • To check status of a specific job: [bold]kstat <job-id>[/bold]")
        console.print("  • To check status of all jobs in a run: [bold]kstat <run-id>[/bold]")
        console.print("  • To list all runs: [bold]klist[/bold]")


def handle_submission_status(run_id: str, output: Optional[str] = None):
    """
    Handle status command for a run ID.

    Args:
        run_id: The run ID to get status for
        output: The output format (table, json, yaml)
    """
    # Get all jobs for this run
    jobs = get_jobs_for_submission(run_id)

    if not jobs:
        console.print(f"[bold red]Error:[/bold red] No jobs found for run ID {run_id}")
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Check if the run ID is correct: [bold]klist[/bold]")
        console.print("  • Submit a new job: [bold]krun <script.sh>[/bold]")
        return  # Return instead of raising an exception for graceful exit

    # Get status for each job
    statuses = []
    for job_id, job_name in jobs:
        try:
            # Get job status from Kubernetes
            job_status = get_job_status(job_id)

            # Get additional information from the database
            db_info = get_job_submission_info(job_id)
            if db_info:
                # Add job name and other metadata from database
                job_status["job_name"] = job_name
                job_status["submission_id"] = db_info.get("submission_id")

                # Add any additional metadata that might be useful
                metadata = db_info.get("metadata", {})
                for key, value in metadata.items():
                    if key not in job_status:
                        job_status[key] = value
            else:
                # Fallback to just using the job name
                job_status["job_name"] = job_name

            statuses.append(job_status)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get status for job {job_id}: {str(e)}[/yellow]")

    # Display results
    if output == "json":
        console.print(json.dumps(statuses, indent=2))
    elif output == "yaml":
        console.print(yaml.dump(statuses))
    else:
        # Format as table
        table = Table(title=f"Jobs in Run {run_id}")
        table.add_column("Run ID")
        table.add_column("Job Name")
        table.add_column("Job ID")
        table.add_column("Status")
        table.add_column("Start Time")
        table.add_column("Duration")
        table.add_column("Namespace")

        for status in statuses:
            table.add_row(
                run_id,
                status.get("job_name", "N/A"),
                status.get("job_id", "N/A"),
                status.get("status", "N/A"),
                str(status.get("start_time", "N/A")),
                status.get("duration", "N/A"),
                status.get("namespace", "N/A")
            )

        console.print(table)


@app.command("logs")
def klogs(
        identifier: str = typer.Argument(..., help="Job ID or Run ID to view logs from"),
        follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
        container: Optional[str] = typer.Option(None, "--container", "-c", help="Specific container to view logs from"),
        tail: Optional[int] = typer.Option(None, "--tail", "-n", help="Number of lines to show from the end"),
        job_name: Optional[str] = typer.Option(None, "--job-name",
                                               help="Specific job name within a run to view logs from"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: text (default), json"),
        output_file: Optional[Path] = typer.Option(None, "--output-file",
                                                   help="Path to file where logs will be written"),
):
    """
    Shorthand for 'ksubmit logs' - Show logs of a completed or running job or all jobs in a run.

    Examples:
        klogs <job-id>
        klogs <run-id>
        klogs <run-id> --job-name job1
        klogs <job-id> --follow
        klogs <job-id> --output-file logs.txt
    """
    try:
        # Validate input
        identifier = validate_identifier(identifier)

        if identifier.startswith("run-"):
            # Handle as run ID
            handle_submission_logs(identifier, follow, container, tail, job_name, output, output_file)
        else:
            # Handle as job ID
            logs.logs(job_id=identifier, follow=follow, container=container, tail=tail, output=output,
                      output_file=output_file)

    except typer.Exit as e:
        # Handle typer.Exit exceptions gracefully
        # No need to print an error message as it should have been printed by the logs function
        # Just exit with the same code
        raise typer.Exit(e.exit_code)
    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in klogs: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • To view logs of a specific job: [bold]klogs <job-id>[/bold]")
        console.print("  • To view logs of all jobs in a run: [bold]klogs <run-id>[/bold]")
        console.print("  • To list all runs: [bold]klist[/bold]")
        raise typer.Exit(1)


def handle_submission_logs(run_id: str, follow: bool = False, container: Optional[str] = None,
                           tail: Optional[int] = None, job_name: Optional[str] = None,
                           output: Optional[str] = None, output_file: Optional[Path] = None):
    """
    Handle logs command for a run ID.

    Args:
        run_id: The run ID to get logs for
        follow: Whether to follow logs in real-time
        container: Specific container to view logs from
        tail: Number of lines to show from the end
        job_name: Specific job name within the run to view logs from
        output: Output format (text, json)
        output_file: Path to file where logs will be written
    """
    # Get all jobs for this run
    jobs = get_jobs_for_submission(run_id)

    if not jobs:
        console.print(f"[bold red]Error:[/bold red] No jobs found for run ID {run_id}")
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Check if the run ID is correct: [bold]klist[/bold]")
        console.print("  • Submit a new job: [bold]krun <script.sh>[/bold]")
        return  # Return instead of raising an exception for graceful exit

    # Filter by job name if specified
    if job_name:
        jobs = [(job_id, name) for job_id, name in jobs if name == job_name]
        if not jobs:
            console.print(f"[bold red]Error:[/bold red] No job with name '{job_name}' found in run {run_id}")
            console.print("[bold yellow]Try:[/bold yellow]")
            console.print(f"  • Check available job names in this run: [bold]kstat {run_id}[/bold]")
            return  # Return instead of raising an exception for graceful exit

    # Get logs for each job
    for job_id, name in jobs:
        console.print(f"[bold cyan]===== Logs for job: {name} ({job_id}) =====\n[/bold cyan]")
        try:
            # We can't use follow=True for multiple jobs, so only use it if we're looking at a single job
            should_follow = follow and len(jobs) == 1
            logs.logs(job_id=job_id, follow=should_follow, container=container, tail=tail, output=output,
                      output_file=output_file)
            console.print("\n")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get logs for job {job_id}: {str(e)}[/yellow]\n")


@app.command("desc")
def kdesc(
        identifier: str = typer.Argument(..., help="Job ID or Run ID to describe"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: table (default), json, yaml"),
        show_yaml: bool = typer.Option(False, "--yaml", "-y", help="Show full YAML specification"),
        job_name: Optional[str] = typer.Option(None, "--job-name", help="Specific job name within a run to describe"),
):
    """
    Shorthand for 'ksubmit describe' - Show detailed information about a job or all jobs in a run.

    Examples:
        kdesc <job-id>
        kdesc <run-id>
        kdesc <run-id> --job-name job1
        kdesc <job-id> --yaml
    """
    try:
        # Validate input
        identifier = validate_identifier(identifier)

        if identifier.startswith("run-"):
            # Handle as run ID
            handle_submission_describe(identifier, output, show_yaml, job_name)
        else:
            # Handle as job ID
            describe.job(job_id=identifier, output=output, show_yaml=show_yaml)

    except typer.Exit as e:
        # Handle typer.Exit exceptions gracefully
        # No need to print an error message as it should have been printed by the describe function
        # Just exit with the same code
        raise typer.Exit(e.exit_code)
    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in kdesc: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • To describe a specific job: [bold]kdesc <job-id>[/bold]")
        console.print("  • To describe all jobs in a run: [bold]kdesc <run-id>[/bold]")
        console.print("  • To list all runs: [bold]klist[/bold]")
        raise typer.Exit(1)


def handle_submission_describe(run_id: str, output: Optional[str] = None,
                               show_yaml: bool = False, job_name: Optional[str] = None):
    """
    Handle describe command for a run ID.

    Args:
        run_id: The run ID to describe
        output: The output format (table, json, yaml)
        show_yaml: Whether to show the full YAML specification
        job_name: Specific job name within the run to describe
    """
    # Get all jobs for this run
    jobs = get_jobs_for_submission(run_id)

    if not jobs:
        console.print(f"[bold red]Error:[/bold red] No jobs found for run ID {run_id}")
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Check if the run ID is correct: [bold]klist[/bold]")
        console.print("  • Submit a new job: [bold]krun <script.sh>[/bold]")
        return  # Return instead of raising an exception for graceful exit

    # Filter by job name if specified
    if job_name:
        jobs = [(job_id, name) for job_id, name in jobs if name == job_name]
        if not jobs:
            console.print(f"[bold red]Error:[/bold red] No job with name '{job_name}' found in run {run_id}")
            console.print("[bold yellow]Try:[/bold yellow]")
            console.print(f"  • Check available job names in this run: [bold]kstat {run_id}[/bold]")
            return  # Return instead of raising an exception for graceful exit

    # Get details for each job
    details = []
    for job_id, name in jobs:
        try:
            job_details = describe_job(job_id)
            job_details["job_name"] = name  # Add job name to details
            details.append(job_details)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not describe job {job_id}: {str(e)}[/yellow]")

    # Display results
    if output == "json":
        console.print(json.dumps(details, indent=2))
    elif output == "yaml":
        console.print(yaml.dump(details))
    else:
        if show_yaml:
            # Display YAML for each job
            for i, job_details in enumerate(details):
                if i > 0:
                    console.print("\n" + "-" * 80 + "\n")
                console.print(
                    f"[bold cyan]Run/Job: {job_details.get('job_name', 'N/A')} ({job_details.get('job_id', 'N/A')})[/bold cyan]\n")
                if "yaml" in job_details:
                    console.print(job_details["yaml"])
        else:
            # Create a table with all jobs in the run
            table = Table(title=f"Jobs in Run {run_id}")

            # Add columns
            table.add_column("Run/Job Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Created", style="yellow")
            table.add_column("Image")
            table.add_column("CPU Request")
            table.add_column("Memory Request")
            table.add_column("GPU Request")
            table.add_column("Node")

            # Add rows for each job
            for job_details in details:
                status_info = job_details.get("status", {})
                status_str = status_info.get("status", "N/A")

                # Format creation time
                created_at = status_info.get("created_at", "N/A")
                if created_at != "N/A" and not isinstance(created_at, str):
                    created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")

                # Get pod information
                pods = job_details.get("pods", [])
                node = "N/A"
                if pods and len(pods) > 0:
                    node = pods[0].get("node", "N/A")

                # Get resource requests
                cpu_request = job_details.get("cpu_request", "N/A")
                memory_request = job_details.get("memory_request", "N/A")
                gpu_request = job_details.get("gpu_request", "N/A")

                # Get image
                image = job_details.get("image", "N/A")

                # Add row to table
                table.add_row(
                    job_details.get("job_name", "N/A"),
                    status_str,
                    str(created_at),
                    image,
                    str(cpu_request),
                    str(memory_request),
                    str(gpu_request),
                    node
                )

            # Display the table
            console.print(table)

            # Display detailed information for each job
            for i, job_details in enumerate(details):
                if i > 0:
                    console.print("\n" + "-" * 80 + "\n")

                console.print(
                    f"\n[bold cyan]Detailed information for {job_details.get('job_name', 'N/A')} ({job_details.get('job_id', 'N/A')}):[/bold cyan]\n")

                # Create a details table
                details_table = Table(show_header=False, box=None)
                details_table.add_column("Property", style="bold")
                details_table.add_column("Value")

                # Add status details
                status_info = job_details.get("status", {})
                details_table.add_row("Status", status_info.get("status", "N/A"))
                details_table.add_row("Namespace", status_info.get("namespace", "N/A"))

                # Format creation and completion times
                created_at = status_info.get("created_at", "N/A")
                if created_at != "N/A" and not isinstance(created_at, str):
                    created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")

                completion_time = status_info.get("completion_time", "N/A")
                if completion_time != "N/A" and not isinstance(completion_time, str) and completion_time is not None:
                    completion_time = completion_time.strftime("%Y-%m-%d %H:%M:%S")

                details_table.add_row("Created", str(created_at))
                details_table.add_row("Completed", str(completion_time))

                # Add job counts
                details_table.add_row("Active", str(status_info.get("active", 0)))
                details_table.add_row("Succeeded", str(status_info.get("succeeded", 0)))
                details_table.add_row("Failed", str(status_info.get("failed", 0)))

                # Add resource information
                details_table.add_row("Image", job_details.get("image", "N/A"))
                details_table.add_row("CPU Request", str(job_details.get("cpu_request", "N/A")))
                details_table.add_row("Memory Request", str(job_details.get("memory_request", "N/A")))
                details_table.add_row("GPU Request", str(job_details.get("gpu_request", "N/A")))

                # Display the details table
                console.print(details_table)

                # Display conditions if available
                conditions = status_info.get("conditions", [])
                if conditions:
                    console.print("\n[bold]Conditions:[/bold]")
                    conditions_table = Table(show_header=True)
                    conditions_table.add_column("Type", style="cyan")
                    conditions_table.add_column("Status", style="green")
                    conditions_table.add_column("Reason")
                    conditions_table.add_column("Message")
                    conditions_table.add_column("Last Transition")

                    for condition in conditions:
                        # Format last transition time
                        last_time = condition.get("last_transition_time", "N/A")
                        if last_time != "N/A" and not isinstance(last_time, str) and last_time is not None:
                            last_time = last_time.strftime("%Y-%m-%d %H:%M:%S")

                        conditions_table.add_row(
                            condition.get("type", "N/A"),
                            condition.get("status", "N/A"),
                            condition.get("reason", "N/A"),
                            condition.get("message", "N/A"),
                            str(last_time)
                        )

                    console.print(conditions_table)

                # Display pod information if available
                pods = job_details.get("pods", [])
                if pods:
                    console.print("\n[bold]Pods:[/bold]")
                    pods_table = Table(show_header=True)
                    pods_table.add_column("Name", style="cyan")
                    pods_table.add_column("Phase", style="green")
                    pods_table.add_column("Node")
                    pods_table.add_column("IP")
                    pods_table.add_column("Start Time")

                    for pod in pods:
                        # Format start time
                        start_time = pod.get("start_time", "N/A")
                        if start_time != "N/A" and not isinstance(start_time, str) and start_time is not None:
                            start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

                        pods_table.add_row(
                            pod.get("name", "N/A"),
                            pod.get("phase", "N/A"),
                            pod.get("node", "N/A"),
                            pod.get("ip", "N/A"),
                            str(start_time)
                        )

                    console.print(pods_table)

                    # Display advanced section with raw Kubernetes commands
                    console.print("\n[bold yellow]⚠️ Advanced Debugging Commands (Use with caution):[/bold yellow]")
                    console.print(
                        "[yellow]These commands can be used for advanced debugging but require kubectl and appropriate permissions.[/yellow]")

                    # Create a table for advanced commands
                    advanced_table = Table(show_header=True, box=None)
                    advanced_table.add_column("Purpose", style="cyan")
                    advanced_table.add_column("Command", style="green")

                    # Get the namespace and pod name for the commands
                    namespace = job_details.get("namespace", "default")
                    pod_name = pod.get("name", "pod-name")  # Using the last pod in the loop
                    job_name = job_details.get("job_id", "job-name")

                    # Add commands for logs
                    advanced_table.add_row(
                        "View pod logs",
                        f"kubectl logs {pod_name} -n {namespace}"
                    )
                    advanced_table.add_row(
                        "View previous pod logs",
                        f"kubectl logs {pod_name} -n {namespace} --previous"
                    )

                    # Add commands for events
                    advanced_table.add_row(
                        "View events for this pod",
                        f"kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}"
                    )

                    # Add commands for describing resources
                    advanced_table.add_row(
                        "Describe pod",
                        f"kubectl describe pod {pod_name} -n {namespace}"
                    )
                    advanced_table.add_row(
                        "Describe job",
                        f"kubectl describe job {job_name} -n {namespace}"
                    )

                    # Add commands for resource usage
                    advanced_table.add_row(
                        "View pod resource usage",
                        f"kubectl top pod {pod_name} -n {namespace}"
                    )

                    # Display the advanced commands table
                    console.print(advanced_table)

                    # Display resource information
                    console.print("\n[bold]Resource Information:[/bold]")
                    resource_table = Table(show_header=False, box=None)
                    resource_table.add_column("Resource", style="cyan")
                    resource_table.add_column("Value", style="green")

                    # Add resource information
                    resource_table.add_row("Image", job_details.get("image", "N/A"))
                    resource_table.add_row("CPU Request", str(job_details.get("cpu_request", "N/A")))
                    resource_table.add_row("Memory Request", str(job_details.get("memory_request", "N/A")))
                    resource_table.add_row("GPU Request", str(job_details.get("gpu_request", "N/A")))

                    console.print(resource_table)


@app.command("del")
def kdel(
        identifier: str = typer.Argument(..., help="Job ID or Run ID to delete"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: text (default), json, yaml"),
        job_name: Optional[str] = typer.Option(None, "--job-name", help="Specific job name within a run to delete"),
        force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation"),
):
    """
    Shorthand for 'ksubmit delete' - Delete a Kubernetes job or all jobs in a run.

    Examples:
        kdel <job-id>
        kdel <run-id>
        kdel <run-id> --job-name job1
        kdel <run-id> --force
    """
    try:
        # Validate input
        identifier = validate_identifier(identifier)

        if identifier.startswith("run-"):
            # Handle as run ID
            handle_submission_delete(identifier, output, job_name, force)
        else:
            # Handle as job ID
            delete.job(job_id=identifier, output=output)

    except typer.Exit as e:
        # Handle typer.Exit exceptions gracefully
        # No need to print an error message as it should have been printed by the delete function
        # Just exit with the same code
        raise typer.Exit(e.exit_code)
    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in kdel: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • To delete a specific job: [bold]kdel <job-id>[/bold]")
        console.print("  • To delete all jobs in a run: [bold]kdel <run-id>[/bold]")
        console.print("  • To list all runs: [bold]klist[/bold]")
        raise typer.Exit(1)


def handle_submission_delete(run_id: str, output: Optional[str] = None,
                             job_name: Optional[str] = None, force: bool = False):
    """
    Handle delete command for a run ID.

    Args:
        run_id: The run ID to delete
        output: The output format (text, json, yaml)
        job_name: Specific job name within the run to delete
        force: Whether to force deletion without confirmation
    """
    # Get all jobs for this run
    jobs = get_jobs_for_submission(run_id)

    if not jobs:
        console.print(f"[bold red]Error:[/bold red] No jobs found for run ID {run_id}")
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Check if the run ID is correct: [bold]klist[/bold]")
        console.print("  • Submit a new job: [bold]krun <script.sh>[/bold]")
        return  # Return instead of raising an exception for graceful exit

    # Filter by job name if specified
    if job_name:
        jobs = [(job_id, name) for job_id, name in jobs if name == job_name]
        if not jobs:
            console.print(f"[bold red]Error:[/bold red] No job with name '{job_name}' found in run {run_id}")
            console.print("[bold yellow]Try:[/bold yellow]")
            console.print(f"  • Check available job names in this run: [bold]kstat {run_id}[/bold]")
            return  # Return instead of raising an exception for graceful exit

    # Confirm deletion
    if not force:
        job_count = len(jobs)
        job_text = "job" if job_count == 1 else "jobs"
        confirm = typer.confirm(f"Are you sure you want to delete {job_count} {job_text} in run {run_id}?")
        if not confirm:
            console.print("Deletion cancelled.")
            return

    # Delete each job
    results = []
    for job_id, name in jobs:
        try:
            console.print(f"Deleting job: {name} ({job_id})...", end=" ")
            result = delete_job(job_id)
            console.print("[bold green]Done[/bold green]")
            result["job_name"] = name
            results.append(result)
        except Exception as e:
            console.print(f"[bold red]Failed[/bold red]")
            console.print(f"[yellow]Warning: Could not delete job {job_id}: {str(e)}[/yellow]")
            results.append({"job_id": job_id, "job_name": name, "status": "failed", "error": str(e)})

    # Display results
    if output == "json":
        console.print(json.dumps(results, indent=2))
    elif output == "yaml":
        console.print(yaml.dump(results))
    else:
        console.print(f"[bold green]All jobs in run {run_id} have been processed.[/bold green]")


@app.command("ls")
def kls(
        status_filter: Optional[str] = typer.Option(None, "--status", "-s",
                                                    help="Filter by job status (running, completed, failed)"),
        label: Optional[str] = typer.Option(None, "--label", "-l", help="Filter by label (format: key=value)"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: table (default), json, yaml"),
        run_id: Optional[str] = typer.Option(None, "--run", "-r", help="Filter by run ID"),
):
    """
    Shorthand for 'ksubmit list' - List all jobs or jobs in a run.

    Examples:
        kls
        kls --status running
        kls --label project=ml
        kls --run <run-id>
    """
    try:
        if run_id:
            # Validate run ID
            run_id = validate_identifier(run_id)
            if not run_id.startswith("run-"):
                console.print(f"[bold red]Error:[/bold red] Invalid run ID format: {run_id}")
                console.print(
                    "[bold yellow]Run IDs must start with 'run-' followed by at least 8 hex characters.[/bold yellow]")
                console.print("Example: run-64a7b123abcd")
                return  # Return instead of raising an exception for graceful exit

            # Handle as run ID
            handle_submission_list(run_id, status_filter, output)
        else:
            # List all jobs
            list.jobs(status=status_filter, label=label, output=output)

    except typer.Exit as e:
        # Handle typer.Exit exceptions gracefully
        # No need to print an error message as it should have been printed by the list function
        # Just exit with the same code
        raise typer.Exit(e.exit_code)
    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in kls: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • To list all jobs: [bold]kls[/bold]")
        console.print("  • To list jobs with a specific status: [bold]kls --status running[/bold]")
        console.print("  • To list jobs in a specific run: [bold]kls --run <run-id>[/bold]")
        console.print("  • To list all runs: [bold]klist[/bold]")
        raise typer.Exit(1)


def handle_submission_list(run_id: str, status_filter: Optional[str] = None, output: Optional[str] = None):
    """
    Handle list command for a run ID.

    Args:
        run_id: The run ID to list jobs for
        status_filter: Filter by job status (running, completed, failed)
        output: The output format (table, json, yaml)
    """
    # Get all jobs for this run
    jobs = get_jobs_for_submission(run_id)

    if not jobs:
        console.print(f"[bold red]Error:[/bold red] No jobs found for run ID {run_id}")
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Check if the run ID is correct: [bold]klist[/bold]")
        console.print("  • Submit a new job: [bold]krun <script.sh>[/bold]")
        return  # Return instead of raising an exception for graceful exit

    # Get details for each job
    job_details = []
    for job_id, job_name in jobs:
        try:
            # Get job status
            status_info = get_job_status(job_id)

            # Add job name to status info
            status_info["job_name"] = job_name

            # Filter by status if specified
            if status_filter and status_info.get("status", "").lower() != status_filter.lower():
                continue

            job_details.append(status_info)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get status for job {job_id}: {str(e)}[/yellow]")

    # Display results
    if output == "json":
        console.print(json.dumps(job_details, indent=2))
    elif output == "yaml":
        console.print(yaml.dump(job_details))
    else:
        # Format as table
        table = Table(title=f"Jobs in Run {run_id}")
        table.add_column("Run/Job Name")
        table.add_column("Job ID")
        table.add_column("Status")
        table.add_column("Start Time")
        table.add_column("Duration")

        for job in job_details:
            table.add_row(
                job.get("job_name", "N/A"),
                job.get("job_id", "N/A"),
                job.get("status", "N/A"),
                job.get("start_time", "N/A"),
                job.get("duration", "N/A")
            )

        console.print(table)


@app.command("list")
def klist(
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output format: table (default), json, yaml"),
        limit: Optional[int] = typer.Option(None, "--limit", "-n", help="Limit the number of runs to show"),
):
    """
    List all runs and their associated jobs.

    Examples:
        klist
        klist --output json
        klist --limit 10
    """
    try:
        # Get all submissions from the database
        from ksubmit.utils.database import get_all_submissions
        submissions = get_all_submissions()

        # Apply limit if specified
        if limit and limit > 0:
            submissions = submissions[:limit]

        # Display results
        if output == "json":
            console.print(json.dumps(submissions, indent=2))
        elif output == "yaml":
            console.print(yaml.dump(submissions))
        else:
            # Format as table
            table = Table(title="All Runs")
            table.add_column("Run ID")
            table.add_column("Job Count")
            table.add_column("Submit Time")
            table.add_column("Job Names")

            for sub in submissions:
                # Truncate job names if there are too many
                job_names = sub.get("job_names", [])
                if len(job_names) > 3:
                    job_names_display = ", ".join(job_names[:3]) + f" (+{len(job_names) - 3} more)"
                else:
                    job_names_display = ", ".join(job_names)

                table.add_row(
                    sub.get("run_id", "N/A"),
                    str(sub.get("job_count", 0)),
                    sub.get("submit_time", "N/A"),
                    job_names_display
                )

            console.print(table)

            # Show help text
            console.print("\n[bold yellow]Commands to manage runs:[/bold yellow]")
            console.print("  • Check status: [bold]kstat <run-id>[/bold]")
            console.print("  • View logs: [bold]klogs <run-id>[/bold]")
            console.print("  • Get details: [bold]kdesc <run-id>[/bold]")
            console.print("  • Delete jobs: [bold]kdel <run-id>[/bold]")

    except typer.Exit as e:
        # Handle typer.Exit exceptions gracefully
        # No need to print an error message as it should have been printed by the function
        # Just exit with the same code
        raise typer.Exit(e.exit_code)
    except Exception as e:
        # Proper error handling with helpful messages
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        # Log detailed error for debugging
        logger.error(f"Error in klist: {str(e)}", exc_info=True)
        console.print("[bold yellow]Try:[/bold yellow]")
        console.print("  • Initialize ksubmit if you haven't: [bold]kconfig init[/bold]")
        console.print("  • Submit a job first: [bold]krun <script.sh>[/bold]")
        raise typer.Exit(1)


@app.command("lint")
def klint(
        script_path: str = typer.Argument(..., help="Path to the UGER-style shell script to lint"),
        strict: bool = typer.Option(False, "--strict", help="Treat warnings as errors"),
        json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """
    Shorthand for 'ksubmit lint' - Lint job scripts for errors.

    Examples:
        klint my_script.sh
        klint my_script.sh --strict
        klint my_script.sh --json
    """
    lint.lint(script_path=script_path, strict=strict, json_output=json_output)


@app.command("config")
def kconfig(
        action: str = typer.Argument(..., help="Action to perform: get, set, list, reset, init"),
        key: Optional[str] = typer.Argument(None, help="Config key to get or set"),
        value: Optional[str] = typer.Argument(None, help="Value to set for the given key"),
        namespace: Optional[str] = typer.Option(None, help="Kubernetes namespace to use (for init)"),
        email: Optional[str] = typer.Option(None, help="User email for job identification (for init)"),
):
    """
    Shorthand for 'ksubmit config' - Manage ksubmit configuration.

    Examples:
        kconfig list
        kconfig get namespace
        kconfig set namespace my-namespace
        kconfig reset
        kconfig init
        kconfig init --namespace my-namespace --email user@example.com
    """
    if action == "list":
        config.list()
    elif action == "get":
        if not key:
            console.print("[bold red]Error:[/bold red] Key is required for 'get' action")
            raise typer.Exit(1)
        config.get(key=key)
    elif action == "set":
        if not key:
            console.print("[bold red]Error:[/bold red] Key is required for 'set' action")
            raise typer.Exit(1)
        config.set(key=key, value=value)
    elif action == "reset":
        config.reset()
    elif action == "init":
        # Call the initialize_config function from user_config module
        if initialize_config(namespace, email):
            console.print("[bold green]✓[/bold green] Configuration initialized successfully!")
        else:
            console.print("[bold red]✗[/bold red] Configuration initialization failed.")
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown action: {action}")
        console.print("Valid actions: get, set, list, reset, init")
        raise typer.Exit(1)


def main():
    """
    Main entry point for the CLI.
    Detects which command was invoked and executes the corresponding function.
    """
    import sys

    # Get the command name from the script name
    command_name = os.path.basename(sys.argv[0])

    # Map command names to functions
    command_map = {
        "krun": krun,
        "kstat": kstat,
        "klogs": klogs,
        "kdesc": kdesc,
        "kdel": kdel,
        "kls": kls,
        "klist": klist,
        "klint": klint,
        "kconfig": kconfig,
        "kversion": kversion,
    }

    # If the command is in the map, execute it directly
    if command_name in command_map:
        # Create a new Typer app just for this command
        cmd_app = typer.Typer()
        cmd_app.command()(command_map[command_name])
        cmd_app()
    else:
        # Otherwise, run the full app
        app()


if __name__ == "__main__":
    main()
