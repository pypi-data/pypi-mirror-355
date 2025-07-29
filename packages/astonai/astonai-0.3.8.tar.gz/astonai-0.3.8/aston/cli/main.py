"""
Main CLI module for TestIndex.

This module defines the main CLI command group and entry point function.
"""
import sys
from typing import List, Optional

import click

from aston.core.cli.runner import create_cli, run_cli
from aston.core.exceptions import CLIError

# Import commands
from aston.cli.commands.init import init_command
from aston.cli.commands.refresh import refresh_command
from aston.cli.commands.coverage import coverage_command
from aston.cli.commands.ingest_coverage import ingest_coverage_command
from aston.cli.commands.test import test_command
from aston.cli.commands.run_pytest_with_coverage import cov_command
from aston.cli.commands.check import check_command
from aston.cli.commands.graph import graph_command
from aston.cli.commands.suggest import suggest_command
from aston.cli.commands.diff import diff_command
from aston.cli.commands.regression_guard import regression_guard_command
from aston.cli.commands.criticality import criticality
from aston.cli.commands.cache import cache_group
from aston.cli.commands.embed import embed_command

# Create main CLI group
cli = create_cli(
    name="aston",
    help_text=(
        "Aston — build the knowledge graph for your repo and spot test‑coverage gaps.\n\n"
        "Run any command with -h/--help for more options."
    ),
)

# Register commands
cli.add_command(init_command)
cli.add_command(refresh_command)
cli.add_command(coverage_command)
cli.add_command(ingest_coverage_command)
cli.add_command(test_command)
cli.add_command(cov_command)
cli.add_command(check_command)
cli.add_command(graph_command)
cli.add_command(suggest_command)
cli.add_command(diff_command)
cli.add_command(regression_guard_command)
cli.add_command(criticality)
cli.add_command(cache_group)
cli.add_command(embed_command)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the TestIndex CLI.

    Args:
        args: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        run_cli(cli, args=args)
        return 0
    except CLIError as e:
        click.echo(f"Error: {e}", err=True)
        return 1
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
