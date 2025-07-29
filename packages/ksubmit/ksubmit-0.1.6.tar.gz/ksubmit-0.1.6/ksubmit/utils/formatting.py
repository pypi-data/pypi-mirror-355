"""
Formatting utilities for ksub - handles colored output and table formatting.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.box import Box
from typing import Dict, List, Any, Optional, Union
import json

console = Console()


def format_job_status(status: str) -> Text:
    """
    Format a job status with appropriate color.

    Args:
        status: Status string (Running, Succeeded, Failed, etc.)

    Returns:
        Rich Text object with colored status
    """
    status_colors = {
        "Running": "bold blue",
        "Succeeded": "bold green",
        "Failed": "bold red",
        "Pending": "bold yellow",
        "Unknown": "dim white"
    }

    color = status_colors.get(status, "white")
    return Text(status, style=color)


def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g. "2h 15m 30s")
    """
    if seconds < 60:
        return f"{seconds}s"

    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"

    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m"

    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h"


def format_job_table(jobs: List[Dict[str, Any]]) -> Table:
    """
    Format a list of jobs as a Rich table.

    Args:
        jobs: List of job dictionaries

    Returns:
        Rich Table object
    """
    table = Table(title="Kubernetes Jobs")

    # Add columns
    table.add_column("JOB-ID", style="cyan")
    table.add_column("NAME", style="bold")
    table.add_column("STATUS")
    table.add_column("CREATED", style="green")
    table.add_column("COMPLETED", style="blue")
    table.add_column("AGE")
    table.add_column("DURATION")
    table.add_column("RETRIES")

    # Add rows
    for job in jobs:
        status_text = format_job_status(job.get("status", "Unknown"))

        # Calculate age and duration
        age = job.get("age", "")
        duration = job.get("duration", "")

        # Format timestamps
        created_at = job.get("created_at")
        completed_at = job.get("completed_at")

        created_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else ""
        completed_str = completed_at.strftime("%Y-%m-%d %H:%M:%S") if completed_at else ""

        table.add_row(
            job.get("job_id", ""),
            job.get("name", ""),
            status_text,
            created_str,
            completed_str,
            age,
            duration,
            str(job.get("retries", 0))
        )

    return table


def print_job_details(job: Dict[str, Any]):
    """
    Print detailed information about a job.

    Args:
        job: Job dictionary with details
    """
    # Create a panel with job details
    title = Text(f"Job: {job.get('name', 'Unknown')}", style="bold cyan")

    # Format content
    content = []
    content.append(f"📦 Image: {job.get('image', 'Unknown')}")

    status = job.get('status', 'Unknown')
    status_text = format_job_status(status)
    content.append(f"🚀 Status: {status_text}")

    # Add timestamps
    created_at = job.get("created_at")
    if created_at:
        created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
        content.append(f"📅 Created: {created_str}")

    completed_at = job.get("completed_at")
    if completed_at:
        completed_str = completed_at.strftime("%Y-%m-%d %H:%M:%S")
        content.append(f"✅ Completed: {completed_str}")

    resources = job.get('resources', {})
    cpu = resources.get('cpu', '?')
    memory = resources.get('memory', '?')
    content.append(f"🧠 Resources: {cpu} CPUs, {memory} RAM")

    age = job.get('age', '?')
    content.append(f"🕒 Runtime: {age}")

    retries = job.get('retries', 0)
    max_retries = job.get('max_retries', 0)
    content.append(f"🎯 Retries: {retries}/{max_retries}")

    labels = job.get('labels', {})
    labels_str = ", ".join([f"{k}={v}" for k, v in labels.items()])
    content.append(f"🏷️ Labels: {labels_str}")

    mounts = job.get('mounts', [])
    mounts_str = ", ".join(mounts) if mounts else "None"
    content.append(f"📁 Mounts: {mounts_str}")

    # Join content with newlines
    panel_content = "\n".join(content)

    # Create and print panel
    panel = Panel(panel_content, title=title, expand=False)
    console.print(panel)


def format_output(data: Any, output_format: Optional[str] = "table"):
    """
    Format and print data according to the specified output format.

    Args:
        data: Data to format and print
        output_format: Output format (json, yaml, table, or None for default)
    """
    if output_format == "json":
        # Convert to JSON and print
        if isinstance(data, (dict, list)):
            console.print(json.dumps(data, indent=2))
        else:
            console.print(json.dumps({"result": str(data)}, indent=2))

    elif output_format == "yaml":
        # Convert to YAML and print
        import yaml
        if isinstance(data, (dict, list)):
            console.print(yaml.dump(data, default_flow_style=False))
        else:
            console.print(yaml.dump({"result": str(data)}, default_flow_style=False))

    elif output_format == "table" and isinstance(data, list):
        # Format as table if it's a list of dictionaries
        if all(isinstance(item, dict) for item in data):
            table = format_job_table(data)
            console.print(table)
        else:
            # Fall back to default formatting
            console.print(data)

    else:
        # Default formatting
        console.print(data)
