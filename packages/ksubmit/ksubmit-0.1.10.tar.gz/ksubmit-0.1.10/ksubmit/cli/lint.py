"""
Lint command implementation for ksubmit.
"""
import typer
from rich.console import Console
from typing import Optional, List
from pathlib import Path

app = typer.Typer(help="Lint job scripts for errors")
console = Console()


@app.callback()
def callback():
    """Lint job scripts for errors."""
    pass


@app.command()
def lint(
    script_file: Path = typer.Argument(
        ...,
        help="Path to the job script file",
        exists=True
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format: text (default), json"
    ),
):
    """
    Lint a job script for errors.

    This command checks a job script for common errors and reports them with line numbers
    and descriptive messages. It validates directives, checks for missing or invalid values,
    and ensures the script follows the expected format.

    Examples:
        ksubmit lint script.sh
        ksubmit lint script.sh --output json
    """
    from ksubmit.linting.lint import lint_script, LintError
    import json

    console.print(f"[bold]Linting script:[/bold] {script_file}")

    # Lint the script
    errors = lint_script(script_file)

    # Format and print errors
    if output == "json":
        # JSON output
        error_list = [
            {
                "line": error.line_number,
                "rule_id": error.rule_id,
                "error_code": error.error_code,
                "message": error.message
            }
            for error in errors
        ]
        console.print(json.dumps({"errors": error_list}, indent=2))
    else:
        # Default text output
        if errors:
            console.print(f"[bold red]Found {len(errors)} error(s) in {script_file}:[/bold red]")
            for error in errors:
                console.print(f"[red]Line {error.line_number}:[/red] [{error.rule_id}] {error.message}")
        else:
            console.print(f"[bold green]✓[/bold green] No errors found in {script_file}")

    # Return exit code based on whether errors were found
    return len(errors) > 0