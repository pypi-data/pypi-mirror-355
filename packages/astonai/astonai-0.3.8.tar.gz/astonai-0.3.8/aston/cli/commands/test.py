"""
TestIndex test command.

This module implements the `testindex test` command that runs tests with coverage.
"""
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from aston.core.cli.runner import common_options
from aston.core.logging import get_logger
from aston.cli.utils.env_check import needs_env

# Set up logger
logger = get_logger(__name__)


@click.command("test", help="Run tests with coverage")
@click.option("--pytest-args", type=str, help="Additional arguments to pass to pytest")
@click.option("--no-cov", is_flag=True, help="Run tests without coverage")
@click.option("--no-env-check", is_flag=True, help="Skip environment dependency check")
@click.option("--parallel", is_flag=True, help="Run tests in parallel using pytest-xdist")
@common_options
@needs_env("test")
def test_command(
    pytest_args: Optional[str],
    no_cov: bool = False,
    no_env_check: bool = False,
    parallel: bool = False,
    **kwargs,
):
    """Run tests with coverage.

    This command:
    1. Runs pytest with coverage
    2. Generates coverage.xml file in the repository root with correct path format

    Exit codes:
    - 0: Tests passed
    - 1: Tests failed
    - 2: Other error occurred
    """
    try:
        console = Console()

        # Use the repository root (current directory) for coverage output
        output_dir = Path.cwd()

        # Run pytest with or without coverage
        if no_cov:
            cmd = ["pytest"]
        else:
            cmd = [
                "pytest",
                "--cov=aston",
                "--cov-report",
                f"xml:{output_dir / 'coverage.xml'}",
                # Fix path resolution: ensure coverage paths include package prefix
                "--cov-config=pyproject.toml" if (Path.cwd() / "pyproject.toml").exists() else "",
            ]
            
            # Remove empty string if pyproject.toml doesn't exist
            cmd = [arg for arg in cmd if arg]

        # Add parallel execution if requested
        if parallel:
            try:
                import pytest_xdist
                cmd.extend(["-n", "auto"])
                console.print("[yellow]Running tests in parallel with pytest-xdist[/]")
            except ImportError:
                console.print("[yellow]Warning: pytest-xdist not installed, running sequentially[/]")
                console.print("Install with: pip install pytest-xdist")

        # Add user-provided pytest args if specified
        if pytest_args:
            cmd.extend(pytest_args.split())

        console.print(f"Running: [green]{' '.join(cmd)}[/]")

        # Run the pytest command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print output
        console.print(result.stdout)
        if result.stderr:
            console.print("[yellow]STDERR:[/]")
            console.print(result.stderr)

            # Check for common errors in stderr
            if "ModuleNotFoundError: No module named 'pytest_cov" in result.stderr:
                console.print("[bold red]Error:[/] pytest-cov plugin missing")
                console.print(
                    "[bold green]Solution:[/] Run 'pip install pytest-cov' or add --no-cov flag."
                )

        # Return appropriate exit code
        return result.returncode

    except Exception as e:
        console = Console()
        console.print(f"[red]Error running tests:[/] {e}")
        return 2
