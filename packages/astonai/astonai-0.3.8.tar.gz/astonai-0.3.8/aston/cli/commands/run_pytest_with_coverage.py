"""
Aston coverage generation command.

This module implements the `aston cov` command that runs tests with coverage
and generates properly formatted coverage.xml files for Aston's analysis.
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


@click.command("cov", help="Run tests with coverage (optimized for Aston)")
@click.option("--pytest-args", type=str, help="Additional arguments to pass to pytest")
@click.option("--no-cov", is_flag=True, help="Run tests without coverage")
@click.option("--parallel", is_flag=True, help="Run tests in parallel using pytest-xdist")
@click.option("--fast", is_flag=True, help="Use coverage.py directly for faster execution")
@click.option("--target", type=str, default="aston", help="Coverage target package (default: aston)")
@common_options
@needs_env("test")
def cov_command(
    pytest_args: Optional[str],
    no_cov: bool = False,
    parallel: bool = False,
    fast: bool = False,
    target: str = "aston",
    **kwargs,
):
    """Run tests with coverage optimized for Aston analysis.

    This command:
    1. Runs pytest with coverage using proper path resolution
    2. Generates coverage.xml file with correct package-prefixed paths
    3. Supports parallel execution and fast mode

    Exit codes:
    - 0: Tests passed
    - 1: Tests failed
    - 2: Other error occurred
    """
    try:
        console = Console()

        # Use the repository root (current directory) for coverage output
        output_dir = Path.cwd()
        coverage_file = output_dir / "coverage.xml"

        if fast and not no_cov:
            # Fast mode: Use coverage.py directly
            console.print("[yellow]Running in fast mode with coverage.py[/]")
            
            # Step 1: Run coverage with pytest
            run_cmd = [
                "coverage", "run",
                "--source", target,
                "--omit", "*/tests/*,*/test_*,*/cli/commands/*,*/bin/*",
                "-m", "pytest"
            ]
            
            if pytest_args:
                run_cmd.extend(pytest_args.split())
                
            console.print(f"Running: [green]{' '.join(run_cmd)}[/]")
            result = subprocess.run(run_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                console.print(result.stdout)
                if result.stderr:
                    console.print("[yellow]STDERR:[/]")
                    console.print(result.stderr)
                return result.returncode
            
            # Step 2: Generate XML report
            xml_cmd = ["coverage", "xml", "-o", str(coverage_file)]
            console.print(f"Generating XML: [green]{' '.join(xml_cmd)}[/]")
            xml_result = subprocess.run(xml_cmd, capture_output=True, text=True)
            
            if xml_result.returncode != 0:
                console.print("[red]Error generating coverage XML[/]")
                console.print(xml_result.stderr)
                return xml_result.returncode
                
            console.print(result.stdout)
            console.print(f"[green]Coverage XML generated: {coverage_file}[/]")
            
        else:
            # Standard mode: Use pytest-cov
            if no_cov:
                cmd = ["pytest"]
            else:
                cmd = [
                    "pytest",
                    f"--cov={target}",
                    "--cov-report",
                    f"xml:{coverage_file}",
                    "--cov-branch",  # Include branch coverage
                ]

                # Only add config if pyproject.toml exists
                if (Path.cwd() / "pyproject.toml").exists():
                    cmd.append("--cov-config=pyproject.toml")

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

        # Post-process coverage.xml to ensure correct path format
        if not no_cov and coverage_file.exists():
            _fix_coverage_paths(coverage_file, target)
            console.print(f"[green]Coverage paths normalized in {coverage_file}[/]")

        return result.returncode

    except Exception as e:
        console = Console()
        console.print(f"[red]Error running coverage:[/] {e}")
        return 2


def _fix_coverage_paths(coverage_file: Path, target_package: str) -> None:
    """Fix coverage.xml paths to ensure they include the package prefix.
    
    Args:
        coverage_file: Path to the coverage.xml file
        target_package: The target package name (e.g., 'aston')
    """
    try:
        import xml.etree.ElementTree as ET
        
        # Parse the XML
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        # Track if any changes were made
        changes_made = False
        
        # Process each class element
        for class_elem in root.findall(".//class"):
            filename = class_elem.get("filename", "")
            if filename:
                # Check if filename needs the package prefix
                if not filename.startswith(f"{target_package}/") and not filename.startswith(f"{target_package}\\"):
                    # Add package prefix if it's a relative path within the package
                    if not filename.startswith("/") and not filename.startswith("\\"):
                        new_filename = f"{target_package}/{filename}"
                        class_elem.set("filename", new_filename)
                        changes_made = True
                        logger.debug(f"Fixed path: {filename} -> {new_filename}")
        
        # Write back the modified XML if changes were made
        if changes_made:
            tree.write(coverage_file, encoding="utf-8", xml_declaration=True)
            logger.info(f"Fixed {coverage_file} with proper package paths")
        
    except Exception as e:
        logger.error(f"Error fixing coverage paths: {e}")
        # Don't fail the entire command if path fixing fails
        pass 