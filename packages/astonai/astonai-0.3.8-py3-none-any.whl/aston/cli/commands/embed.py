"""
AstonAI embed command for generating vector embeddings.

This module implements the `aston embed` command for generating embeddings
from code files or chunks using different backends.
"""

import time
import asyncio
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from aston.core.path_resolution import PathResolver
from aston.core.cli.runner import common_options
from aston.core.filter_contract import FilterContract
from aston.cli.utils.env_check import needs_env
from aston.cli.common_filters import (
    create_file_filter,
    handle_filter_display,
    add_filter_options,
)
from aston.core.logging import get_logger
from aston.knowledge.embedding.providers.provider_factory import (
    get_provider,
    BackendType,
)
from aston.knowledge.embedding.vector_store import EmbeddingMetadata
from aston.knowledge.embedding.faiss_store import FaissVectorStore

logger = get_logger(__name__)


@click.command("embed", help="Generate vector embeddings for code files")
@click.option(
    "--backend",
    type=click.Choice(["minilm", "openai", "auto"]),
    default="minilm",
    help="Embedding backend to use (default: minilm)",
)
@click.option(
    "--file",
    "-f",
    type=str,
    multiple=True,
    help="Specific file(s) to embed (can be used multiple times)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be embedded without actually doing it",
)
@click.option(
    "--model",
    type=str,
    default="all-MiniLM-L6-v2",
    help="Specific model to use for the selected backend (default: all-MiniLM-L6-v2 for minilm, text-embedding-3-small for openai)",
)
@click.option("--force", is_flag=True, help="Force rebuild of existing embeddings")
@click.option(
    "--api-key", type=str, help="OpenAI API key (overrides OPENAI_API_KEY env var)"
)
@click.option(
    "--batch-size",
    type=int,
    default=10,
    help="Batch size for API requests (OpenAI only, default: 10)",
)
@click.option(
    "--rate-limit-requests",
    type=int,
    default=50,
    help="Max requests per minute (OpenAI only, default: 50)",
)
@click.option(
    "--rate-limit-tokens",
    type=int,
    default=150000,
    help="Max tokens per minute (OpenAI only, default: 150000)",
)
@click.option("--no-env-check", is_flag=True, help="Skip environment dependency check")
@add_filter_options
@common_options
@needs_env("embed")
def embed_command(
    backend: BackendType,
    file: Tuple[str],
    dry_run: bool,
    model: str,
    force: bool,
    api_key: Optional[str],
    batch_size: int,
    rate_limit_requests: int,
    rate_limit_tokens: int,
    no_env_check: bool,
    include: Optional[List[str]],
    exclude: Optional[List[str]],
    include_regex: Optional[List[str]],
    exclude_regex: Optional[List[str]],
    preset: Optional[str],
    show_patterns: bool,
    verbose: bool,
    **kwargs,
):
    """Generate vector embeddings for code files.

    This command:
    1. Identifies code files to process (based on filters or specific files)
    2. Extracts code chunks or uses whole files
    3. Generates embeddings using the specified backend
    4. Stores embeddings in a vector store for later retrieval

    The command supports different backends:
    - minilm: Fast local embedding generation using sentence-transformers
    - openai: High-quality embeddings using OpenAI's API (requires API key)
    - auto: Try minilm first, fall back to openai if not available

    Examples:
        # Generate embeddings for all Python files using MiniLM
        aston embed --backend minilm

        # Embed specific files
        aston embed --file src/main.py --file src/utils.py

        # Use filters to control which files to embed
        aston embed --include "src/**/*.py" --exclude "tests/**"

        # Dry run to see what would be embedded
        aston embed --dry-run --preset python-only
    """
    console = Console()

    try:
        # Check if we need to install dependencies
        if backend == "minilm":
            try:
                import sentence_transformers
                import torch
                import faiss
            except ImportError as e:
                if "sentence_transformers" in str(e):
                    console.print(
                        "[red]Error:[/red] sentence-transformers package is required for MiniLM embeddings."
                    )
                    console.print(
                        "Install with: [bold]pip install sentence-transformers==2.*[/bold]"
                    )
                elif "faiss" in str(e):
                    console.print(
                        "[red]Error:[/red] faiss-cpu package is required for vector storage."
                    )
                    console.print("Install with: [bold]pip install faiss-cpu[/bold]")
                else:
                    console.print(f"[red]Error:[/red] {e}")
                return 1
        elif backend == "openai":
            try:
                import aiohttp
            except ImportError:
                console.print(
                    "[red]Error:[/red] aiohttp package is required for OpenAI embeddings."
                )
                console.print("Install with: [bold]pip install aiohttp[/bold]")
                return 1

            # Check for API key
            import os

            if not os.environ.get("OPENAI_API_KEY") and not api_key:
                console.print(
                    "[red]Error:[/red] OpenAI API key is required for OpenAI embeddings."
                )
                console.print(
                    "Set environment variable: [bold]export OPENAI_API_KEY=sk-...[/bold]"
                )
                console.print("Or use: [bold]--api-key sk-...[/bold]")
                return 1

        # Get repository root
        repo_root = PathResolver.repo_root()

        # Create and configure file filter
        file_filter = create_file_filter(
            repo_root=repo_root,
            include=include,
            exclude=exclude,
            include_regex=include_regex,
            exclude_regex=exclude_regex,
            preset=preset,
        )

        # Handle display options (show patterns or dry run)
        if handle_filter_display(file_filter, show_patterns, False, verbose):
            return 0

        # If specific files were provided, use them instead of filters
        files_to_process = []
        if file:
            for f in file:
                path = Path(f)
                if not path.is_absolute():
                    path = repo_root / path
                if path.exists():
                    files_to_process.append(path)
                else:
                    console.print(f"[yellow]Warning:[/yellow] File not found: {path}")
        else:
            # Use filter contract to get files
            filter_contract = FilterContract(file_filter)
            files_to_process = [Path(f) for f in filter_contract.get_files_to_process()]

        # Check if we have any files to process
        if not files_to_process:
            console.print("[yellow]No files found to embed.[/yellow]")
            return 0

        console.print(f"Found [green]{len(files_to_process)}[/green] files to process.")

        if dry_run:
            console.print("\n[bold]Files that would be processed:[/bold]")
            for f in files_to_process[:10]:  # Show only first 10 files
                console.print(f"  - {f.relative_to(repo_root)}")
            if len(files_to_process) > 10:
                console.print(f"  - ... and {len(files_to_process) - 10} more files")
            console.print(f"\nTotal: {len(files_to_process)} files")
            console.print("\n[yellow]Dry run, no embeddings generated.[/yellow]")
            return 0

        # Create vector store directory if it doesn't exist
        vectors_dir = repo_root / ".aston" / "vectors" / backend
        vectors_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding provider
        console.print(f"Initializing [bold]{backend}[/bold] embedding provider...")
        provider_config = {"model_name": model}

        # Add backend-specific configuration
        if backend == "openai":
            # Set default model for OpenAI if using default MiniLM model
            if model == "all-MiniLM-L6-v2":
                provider_config["model_name"] = "text-embedding-3-small"

            # Add OpenAI-specific config
            provider_config.update(
                {
                    "api_key": api_key,
                    "rate_limit_requests": rate_limit_requests,
                    "rate_limit_tokens": rate_limit_tokens,
                }
            )

        provider = get_provider(backend, provider_config)

        # Initialize vector store
        vector_store = FaissVectorStore(backend=backend, dimension=provider.dimension)

        # Begin embedding generation
        total_files = len(files_to_process)
        start_time = time.time()

        # Function to read file content
        def read_file_content(file_path: Path) -> str:
            """Read file content and return as string."""
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try with a different encoding
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        return f.read()
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
                    return ""
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                return ""

        # Track statistics
        total_vectors = 0
        total_size_bytes = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Generating embeddings...", total=total_files)

            # Process files in batches
            batch_size = 10
            for i in range(0, total_files, batch_size):
                batch_files = files_to_process[i : i + batch_size]
                batch_contents = []
                batch_metadata = []

                # Read file contents
                for file_path in batch_files:
                    content = read_file_content(file_path)
                    if content:
                        rel_path = file_path.relative_to(repo_root)
                        total_size_bytes += len(content.encode("utf-8"))

                        batch_contents.append(content)
                        batch_metadata.append(
                            EmbeddingMetadata(
                                source_type="file",
                                source_id=str(rel_path),
                                content_type="code",
                                content=content[:1000],  # Store first 1000 chars only
                                additional={
                                    "file_path": str(rel_path),
                                    "file_size": len(content),
                                    "embedding_time": time.time(),
                                },
                            )
                        )

                # Generate embeddings
                if batch_contents:
                    embeddings = asyncio.run(
                        provider.generate_embeddings(batch_contents)
                    )

                    # Store vectors
                    asyncio.run(
                        vector_store.batch_store_vectors(embeddings, batch_metadata)
                    )

                    total_vectors += len(embeddings)

                # Update progress
                progress.update(task, advance=len(batch_files))

        # Close vector store
        asyncio.run(vector_store.close())

        # Print summary
        duration = time.time() - start_time
        console.print("\n[bold green]Embedding generation complete![/bold green]")
        console.print(f"Processed [bold]{total_files}[/bold] files")
        console.print(f"Generated [bold]{total_vectors}[/bold] vectors")
        console.print(
            f"Total size: [bold]{total_size_bytes / 1024 / 1024:.2f} MB[/bold]"
        )
        console.print(f"Time taken: [bold]{duration:.2f}s[/bold]")
        console.print(f"Speed: [bold]{total_files / duration:.2f}[/bold] files/second")
        console.print(f"Vectors stored at: [bold]{vectors_dir}[/bold]")

        return 0

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        return 1


# Command is now synchronous - no wrapper needed
