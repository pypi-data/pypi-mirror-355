"""
Environment dependency checker for Aston CLI commands.

This module provides utilities to check if required dependencies are installed
before running Aston CLI commands, preventing cryptic errors and providing
clear instructions on how to fix missing dependencies.
"""
import os
from importlib.util import find_spec
from functools import wraps
from typing import Callable

# Map package names to import names where they differ
NAME_MAP = {
    "pytest-cov": "pytest_cov",
    "coverage-conditional-plugin": "coverage_conditional_plugin",
    "pytest-xdist": "xdist",
    "sentence-transformers": "sentence_transformers",
    "faiss-cpu": "faiss",
    "aiohttp": "aiohttp",
}

# Split dependencies into mandatory (exit if missing) and optional (warn only)
MANDATORY = {
    "test": ["pytest", "pytest-cov"],
    "coverage": ["pytest-cov", "coverage-conditional-plugin"],
    "init": [],
    "embed": [],  # No mandatory deps for embed - backend-specific
}

OPTIONAL = {
    "test": ["pytest-xdist"],
    "coverage": [],
    "init": [],
    "embed": ["sentence-transformers", "faiss-cpu", "aiohttp"],  # All backends optional
}


def check_env(cmd: str, verbose: bool = False) -> bool:
    """Check if environment has all required dependencies for a command.

    Args:
        cmd: The command being run (e.g., 'test', 'coverage')
        verbose: If True, show success message. If False, stay silent on success.

    Returns:
        bool: True if all mandatory dependencies are present, False otherwise
    """
    # Allow opt-out via environment variable or flag
    if os.getenv("ASTON_NO_ENV_CHECK"):
        return True

    # Check for missing mandatory dependencies
    missing = [
        pkg
        for pkg in MANDATORY.get(cmd, [])
        if find_spec(NAME_MAP.get(pkg, pkg)) is None
    ]

    if missing:
        group = "test" if cmd == "test" else "coverage"
        # Special handling for embedding dependencies (should not happen now)
        if cmd == "embed":
            print(f"⚠️ Missing: {', '.join(missing)}")
            print("Note: Embedding dependencies are checked per backend at runtime")
        else:
            print(f"⚠️ Missing: {', '.join(missing)}")
            print(f'To fix: pip install "astonai[{group}]"')
        return False

    # Check for missing optional dependencies - warn but don't exit
    opt_missing = [
        pkg
        for pkg in OPTIONAL.get(cmd, [])
        if find_spec(NAME_MAP.get(pkg, pkg)) is None
    ]

    if opt_missing and verbose:
        print(f"(tip) install '{', '.join(opt_missing)}' for faster runs")

    # Only show success message in verbose mode
    if verbose:
        print("✅ All required dependencies are present.")
    return True


def needs_env(cmd: str) -> Callable:
    """Decorator to check environment before running a command.

    Args:
        cmd: The command name to check dependencies for

    Returns:
        Decorated function that checks env before executing
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip check if --no-env-check flag is provided
            if kwargs.get("no_env_check"):
                if "no_env_check" in kwargs:
                    del kwargs[
                        "no_env_check"
                    ]  # Remove from kwargs before passing to func
                return func(*args, **kwargs)

            # Check verbose mode for clean output
            verbose = kwargs.get("verbose", False)
            if not check_env(cmd, verbose=verbose):
                return 1  # Exit with error for missing mandatory deps
            return func(*args, **kwargs)

        return wrapper

    return decorator
