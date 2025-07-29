"""
Global output management for clean CLI experience.

This module provides centralized control over CLI output formatting,
ensuring consistent user-centric messaging across all commands.
"""

from typing import Optional
import click
from click import style


class OutputManager:
    """Central manager for clean, user-centric CLI output."""

    def __init__(self, verbose: bool = False):
        """Initialize output manager.

        Args:
            verbose: If True, show system details and logs. If False, show clean output only.
        """
        self.verbose = verbose

        # Set environment variable for other modules to check
        import os

        os.environ["ASTON_VERBOSE"] = "1" if verbose else "0"

        self.configure_logging()

    def configure_logging(self):
        """Globally suppress system logs unless verbose mode."""
        if not self.verbose:
            # AGGRESSIVE logging suppression for CLI minimalism
            import logging

            # Set root logger to ERROR level to catch everything
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.ERROR)

            # Suppress specific loggers that might bypass root logger
            loggers_to_suppress = [
                "",  # Root logger
                "aston",
                "git-manager",
                "gitmanager",
                "testindex",
                "aston.core.filtering",
                "aston.core.filter_contract",
                "aston.preprocessing",
                "aston.knowledge",
                "aston.cli.commands",
                "aston.core",
                "aston.preprocessing.cloning.git_manager",
            ]

            for logger_name in loggers_to_suppress:
                logger = logging.getLogger(logger_name)
                logger.setLevel(logging.ERROR)
                logger.disabled = True  # Completely disable for clean output

            # Create a universal filter that blocks ALL INFO/DEBUG logs
            class MinimalismFilter(logging.Filter):
                def filter(self, record):
                    # Only allow ERROR and CRITICAL in clean mode
                    return record.levelno >= logging.ERROR

            # Apply the filter globally
            for handler in root_logger.handlers:
                handler.addFilter(MinimalismFilter())

    def success(self, message: str):
        """Display success message with ✓ prefix."""
        styled_message = style(f"✓ {message}", fg="green")
        click.echo(styled_message)

    def step(self, message: str):
        """Display step transition with → prefix."""
        styled_message = style(f"→ {message}", fg="bright_black")
        click.echo(styled_message)

    def info(self, message: str):
        """Display info message - only shown in verbose mode."""
        if self.verbose:
            click.echo(f"• {message}")

    def system_detail(self, message: str):
        """Display system details - only shown in verbose mode."""
        if self.verbose:
            # Strip emojis from system details
            clean_message = message
            for emoji in ["📂", "🔄", "💾", "⚠️", "📊", "📖", "🌐"]:
                clean_message = clean_message.replace(emoji, "").strip()
            click.echo(clean_message)

    def warning(self, message: str):
        """Display warning message (always shown)."""
        styled_message = style(f"! {message}", fg="yellow", bold=True)
        click.echo(styled_message)

    def error(self, message: str):
        """Display error message (always shown)."""
        styled_message = style(f"✗ {message}", fg="red", bold=True)
        click.echo(styled_message)

    def blank_line(self):
        """Add blank line for spacing (clean output only)."""
        if not self.verbose:
            click.echo("")

    def progress_message(self, message: str):
        """Display progress message during operations."""
        if self.verbose:
            click.echo(f"• {message}")
        # In clean mode, progress is handled by progress bars only

    def final_message(self, message: str, next_action: Optional[str] = None):
        """Display final success message with optional next action."""
        if not self.verbose:
            self.blank_line()

        self.success(message)

        if next_action:
            self.step(next_action)

    def summary_banner(self, chunks: int, files: int, duration: float):
        """Display mission accomplished summary banner."""
        if not self.verbose:
            self.blank_line()
        summary = (
            f"Instantiated — {chunks:,} chunks from {files} files in {duration:.1f}s"
        )
        styled_summary = style(f"✓ {summary}", fg="green")
        click.echo(styled_summary)
