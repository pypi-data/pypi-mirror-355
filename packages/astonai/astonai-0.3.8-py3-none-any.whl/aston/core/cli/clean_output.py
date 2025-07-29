"""
Clean output decorator for CLI commands.

This module provides a decorator that automatically sets up clean output
management for CLI commands, ensuring consistent user experience.
"""

from functools import wraps
from typing import Callable
import click

from aston.core.output import OutputManager


def clean_output(func: Callable) -> Callable:
    """Decorator to standardize clean output across all commands.

    This decorator:
    1. Extracts the verbose flag from command parameters
    2. Creates an OutputManager instance
    3. Suppresses system logging when not in verbose mode
    4. Injects the output manager into the command function

    Usage:
        @click.command()
        @clean_output
        def my_command(..., _output: OutputManager, **kwargs):
            _output.success("Operation completed")
            _output.step("Try: `aston next-command`")

    Args:
        func: The CLI command function to wrap

    Returns:
        Wrapped function with clean output management
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract verbose flag from kwargs or click context
        verbose = kwargs.get("verbose", False)

        # Handle click context if verbose not in kwargs
        if not verbose and hasattr(click, "get_current_context"):
            try:
                ctx = click.get_current_context()
                verbose = ctx.params.get("verbose", False)
            except RuntimeError:
                # No click context available
                pass

        # Create output manager with verbose setting
        output = OutputManager(verbose=verbose)

        # Inject output manager into command
        kwargs["_output"] = output

        return func(*args, **kwargs)

    return wrapper


def get_output_manager(verbose: bool = False) -> OutputManager:
    """Get an OutputManager instance directly.

    Useful for functions that are not CLI commands but need clean output.

    Args:
        verbose: Whether to enable verbose output

    Returns:
        OutputManager instance
    """
    return OutputManager(verbose=verbose)
