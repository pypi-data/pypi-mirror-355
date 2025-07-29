"""
TestIndex init command.

This module implements the `testindex init` command that initializes a Knowledge graph
for a repository. It handles both local and remote repositories.
"""
import os
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import json

import click
import yaml
from rich.progress import Progress
from rich.console import Console

from aston.core.cli.runner import common_options
from aston.core.cli.clean_output import clean_output
from aston.core.config import ConfigModel
from aston.core.exceptions import CLIError
from aston.core.utils import ensure_directory
from aston.core.filtering import create_astonignore_template
from aston.preprocessing.chunking.code_chunker import PythonCodeChunker
from aston.preprocessing.integration.chunk_graph_adapter import ChunkGraphAdapter
from aston.preprocessing.cloning.git_manager import GitManager
from aston.core.logging import get_logger
from aston.cli.utils.env_check import needs_env
from aston.cli.common_filters import (
    add_filter_options,
    create_file_filter,
    handle_filter_display,
)
from aston.core.filter_contract import FilterContract

# Constants
from aston.constants import DATA_DIR_NAME
import pathlib._local
from aston.core.output import OutputManager

DEFAULT_CONFIG_DIR = DATA_DIR_NAME
DEFAULT_CONFIG_FILE = "config.yml"

# Default exclude patterns for file filtering
DEFAULT_EXCLUDE_PATTERNS = [
    "venv*/**",
    ".venv*/**",
    "env/**",
    ".env/**",
    "node_modules/**",
    ".git/**",
    ".svn/**",
    ".hg/**",
    "__pycache__/**",
    "*.pyc",
    ".pytest_cache/**",
    ".coverage/**",
    "htmlcov/**",
    "build/**",
    "dist/**",
    "*.egg-info/**",
    ".tox/**",
    ".mypy_cache/**",
    ".idea/**",
    ".vscode/**",
    "*.min.js",
    "*.bundle.js",
]

# Set up logger
logger = get_logger(__name__)


class RepositoryAdapter(ABC):
    """Abstract base class for repository adapters."""

    @abstractmethod
    def detect_repository(self, path: Path) -> bool:
        """Detect if the given path is a repository of this type.

        Args:
            path: Path to check

        Returns:
            bool: True if this is a repository of this type
        """
        pass

    @abstractmethod
    def get_root(self, path: Path) -> Optional[Path]:
        """Get the root directory of the repository.

        Args:
            path: Path to start searching from

        Returns:
            Optional[Path]: Path to repository root, or None if not found
        """
        pass

    @abstractmethod
    def clone(self, url: str, target_path: Path) -> None:
        """Clone a repository from a URL.

        Args:
            url: Repository URL
            target_path: Path to clone to

        Raises:
            CLIError: If cloning fails
        """
        pass

    @abstractmethod
    def pull(self, path: Path) -> None:
        """Pull latest changes for a repository.

        Args:
            path: Path to repository

        Raises:
            CLIError: If pull fails
        """
        pass


class GitRepositoryAdapter(RepositoryAdapter):
    """Adapter for Git repositories."""

    def __init__(self):
        # Create a default config for GitManager
        config = ConfigModel()
        self.git_manager = GitManager(config)

    def detect_repository(self, path: Path) -> bool:
        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def get_root(self, path: Path) -> Optional[Path]:
        current = path.absolute()

        # Traverse up to 10 levels of directories
        for _ in range(10):
            if self.detect_repository(current):
                return current

            # Stop if we're at the root directory
            if current.parent == current:
                break

            current = current.parent

        return None

    def clone(self, url: str, target_path: Path) -> None:
        try:
            self.git_manager.clone_repository(url, target_path)
        except Exception as e:
            error_msg = f"Failed to clone Git repository: {str(e)}"
            logger.error(error_msg)
            raise CLIError(error_msg)

    def pull(self, path: Path) -> None:
        try:
            self.git_manager.update_repository(path)
        except Exception as e:
            raise CLIError(f"Failed to pull Git repository: {str(e)}")


class MercurialRepositoryAdapter(RepositoryAdapter):
    """Adapter for Mercurial repositories."""

    def detect_repository(self, path: Path) -> bool:
        hg_dir = path / ".hg"
        return hg_dir.exists() and hg_dir.is_dir()

    def get_root(self, path: Path) -> Optional[Path]:
        current = path.absolute()

        # Traverse up to 10 levels of directories
        for _ in range(10):
            if self.detect_repository(current):
                return current

            # Stop if we're at the root directory
            if current.parent == current:
                break

            current = current.parent

        return None

    def clone(self, url: str, target_path: Path) -> None:
        try:
            import subprocess

            subprocess.run(["hg", "clone", url, str(target_path)], check=True)
        except subprocess.CalledProcessError as e:
            raise CLIError(f"Failed to clone Mercurial repository: {str(e)}")
        except FileNotFoundError:
            raise CLIError(
                "Mercurial (hg) command not found. Please install Mercurial."
            )

    def pull(self, path: Path) -> None:
        try:
            import subprocess

            subprocess.run(["hg", "pull", "-u"], cwd=str(path), check=True)
        except subprocess.CalledProcessError as e:
            raise CLIError(f"Failed to pull Mercurial repository: {str(e)}")
        except FileNotFoundError:
            raise CLIError(
                "Mercurial (hg) command not found. Please install Mercurial."
            )


class SVNRepositoryAdapter(RepositoryAdapter):
    """Adapter for Subversion repositories."""

    def detect_repository(self, path: Path) -> bool:
        svn_dir = path / ".svn"
        return svn_dir.exists() and svn_dir.is_dir()

    def get_root(self, path: Path) -> Optional[Path]:
        current = path.absolute()

        # Traverse up to 10 levels of directories
        for _ in range(10):
            if self.detect_repository(current):
                return current

            # Stop if we're at the root directory
            if current.parent == current:
                break

            current = current.parent

        return None

    def clone(self, url: str, target_path: Path) -> None:
        try:
            import subprocess

            subprocess.run(["svn", "checkout", url, str(target_path)], check=True)
        except subprocess.CalledProcessError as e:
            raise CLIError(f"Failed to checkout SVN repository: {str(e)}")
        except FileNotFoundError:
            raise CLIError(
                "Subversion (svn) command not found. Please install Subversion."
            )

    def pull(self, path: Path) -> None:
        try:
            import subprocess

            subprocess.run(["svn", "update"], cwd=str(path), check=True)
        except subprocess.CalledProcessError as e:
            raise CLIError(f"Failed to update SVN repository: {str(e)}")
        except FileNotFoundError:
            raise CLIError(
                "Subversion (svn) command not found. Please install Subversion."
            )


class PlainDirectoryAdapter(RepositoryAdapter):
    """Adapter for plain directories (no VCS)."""

    def detect_repository(self, path: Path) -> bool:
        # A plain directory is always considered a "repository"
        return path.is_dir()

    def get_root(self, path: Path) -> Optional[Path]:
        return path.absolute()

    def clone(self, url: str, target_path: Path) -> None:
        # For plain directories, we just create the directory
        ensure_directory(target_path)

    def pull(self, path: Path) -> None:
        # No-op for plain directories
        pass


# List of available repository adapters
REPOSITORY_ADAPTERS = [
    GitRepositoryAdapter(),
    MercurialRepositoryAdapter(),
    SVNRepositoryAdapter(),
    PlainDirectoryAdapter(),
]


def detect_repository_type(path: Path) -> Optional[RepositoryAdapter]:
    """Detect the type of repository at the given path.

    Args:
        path: Path to check

    Returns:
        Optional[RepositoryAdapter]: Repository adapter if detected, None otherwise
    """
    for adapter in REPOSITORY_ADAPTERS:
        if adapter.detect_repository(path):
            return adapter
    return None


def setup_repo(
    url: Optional[str], path: Optional[str], force: bool = False, output_manager: Optional[OutputManager]=None
) -> Path:
    """Set up the repository for analysis.

    Args:
        url: URL of the repository to clone
        path: Path to the existing local repository
        force: Whether to force clone/clean

    Returns:
        Path: Path to the repository

    Raises:
        CLIError: If repository setup fails
    """
    if url:
        # Clone the repository
        click.echo(f"🌐 Cloning repository from {url}...")
        repo_dir = (
            Path(DATA_DIR_NAME) / "cache" / url.split("/")[-1].replace(".git", "")
        )

        # Create directory if it doesn't exist
        ensure_directory(repo_dir.parent)

        # Determine repository type from URL
        adapter = None
        if url.endswith(".git"):
            adapter = GitRepositoryAdapter()
        elif url.startswith("svn+"):
            adapter = SVNRepositoryAdapter()
        elif url.startswith("hg+"):
            adapter = MercurialRepositoryAdapter()
        else:
            # Try to detect from URL
            if "svn" in url:
                adapter = SVNRepositoryAdapter()
            elif "hg" in url:
                adapter = MercurialRepositoryAdapter()
            else:
                # Default to Git
                adapter = GitRepositoryAdapter()

        # Clone or update repository
        try:
            if repo_dir.exists() and not force:
                click.echo(f"📂 Repository already exists at {repo_dir}")
                click.echo("🔄 Pulling latest changes...")
                adapter.pull(repo_dir)
            else:
                if repo_dir.exists():
                    shutil.rmtree(repo_dir)
                adapter.clone(url, repo_dir)

            click.echo(f"✅ Repository cloned to {repo_dir}")
            return repo_dir

        except Exception as e:
            error_msg = f"Failed to clone repository: {str(e)}"
            logger.error(error_msg)
            raise CLIError(error_msg)

    elif path:
        # Use the specified path
        repo_path = Path(path).absolute()
        if not repo_path.exists():
            error_msg = f"Repository path does not exist: {repo_path}"
            logger.error(error_msg)
            raise CLIError(error_msg)

        # Detect repository type
        adapter = detect_repository_type(repo_path)
        if output_manager:
            if adapter:
                output_manager.system_detail(
                    f"📂 Using {adapter.__class__.__name__} repository at {repo_path}"
                )
            else:
                output_manager.system_detail(f"📂 Using plain directory at {repo_path}")
                adapter = PlainDirectoryAdapter()
        else:
            # Fallback for non-clean output
            if adapter:
                click.echo(
                    f"Using {adapter.__class__.__name__} repository at {repo_path}"
                )
            else:
                click.echo(f"Using plain directory at {repo_path}")
                adapter = PlainDirectoryAdapter()

        return repo_path

    else:
        # Try to find repository in current directory
        current_dir = Path.cwd()

        # Try each adapter
        for adapter in REPOSITORY_ADAPTERS:
            root = adapter.get_root(current_dir)
            if root:
                if output_manager:
                    output_manager.system_detail(
                        f"📂 Using {adapter.__class__.__name__} repository at {root}"
                    )
                else:
                    click.echo(
                        f"Using {adapter.__class__.__name__} repository at {root}"
                    )
                return root

        # If no repository found, use current directory as plain directory
        if output_manager:
            output_manager.system_detail("📂 Using current directory as plain directory")
        else:
            click.echo("Using current directory as plain directory")
        return current_dir


def write_config(
    config_path: Path, neo4j_uri: str, vector_store_path: str, output_manager=None
) -> None:
    """Write the configuration file.

    Args:
        config_path: Path to save the config file
        neo4j_uri: URI for the Neo4j database
        vector_store_path: Path to the vector store

    Raises:
        CLIError: If config file cannot be written
    """
    # Create config directory
    ensure_directory(config_path.parent)

    # Create config dictionary
    config = {
        "neo4j_uri": neo4j_uri,
        "vector_store": vector_store_path,
        "schema_version": "K1",
    }

    # Write config file
    try:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        if output_manager:
            output_manager.system_detail(f"Configuration written to {config_path}")
        else:
            click.echo(f"Configuration written to {config_path}")

    except Exception as e:
        logger.error(f"Failed to write config file: {e}")
        raise CLIError(f"Failed to write config file: {str(e)}")


def run_ingest_pipeline_with_files(
    repo_path: Path,
    config_path: Path,
    force_offline: bool = False,
    python_files: List[Path] = None,
    verbose: bool = False,
    output_manager=None,
) -> Tuple[int, int]:
    """Run the ingest pipeline on a pre-filtered list of files.

    Args:
        repo_path: Path to the repository
        config_path: Path to save the config file
        force_offline: Force offline mode even if Neo4j is available
        python_files: List of Python file paths to process

    Returns:
        Tuple[int, int]: Number of chunks, number of nodes

    Raises:
        CLIError: If ingest pipeline fails
    """
    if not python_files:
        raise CLIError("No Python files provided to process.")

    # Create config
    config = ConfigModel()

    # Create code chunker
    chunker = PythonCodeChunker(config)

    # Count lines of code for the filtered files
    loc = 0
    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                loc += len(f.readlines())
        except Exception as e:
            logger.warning(f"Could not count lines in {file_path}: {e}")

    # Display parsing step
    if output_manager:
        loc_str = f"{loc/1000:.1f}k" if loc >= 1000 else str(loc)
        output_manager.step(f"Parsing {loc_str} LOC from {len(python_files)} files")
        output_manager.system_detail("📊 Analyzing repository...")
        output_manager.system_detail(
            f"📖 Parsing {loc/1000:.1f} k LOC from {len(python_files)} files..."
        )
    elif verbose:
        click.echo("📊 Analyzing repository...")
        click.echo(f"📖 Parsing {loc/1000:.1f} k LOC from {len(python_files)} files...")

    # Try connecting to Neo4j
    neo4j_client = None
    str(config_path / "vectors.sqlite")
    offline_mode = force_offline

    if not offline_mode:
        try:
            from aston.knowledge.graph.neo4j_client import (
                Neo4jClient,
                Neo4jConfig,
                Neo4jConnectionError,
            )

            neo4j_config = Neo4jConfig.from_environment()
            neo4j_client = Neo4jClient(neo4j_config)
            if output_manager:
                output_manager.system_detail("🌐 Connected to Neo4j - using online mode")
            elif verbose:
                click.echo("🌐 Connected to Neo4j - using online mode")
        except (ImportError, Exception) as e:
            offline_mode = True
            logger.debug(f"Neo4j connection failed: {e}")
            if not force_offline:
                if output_manager:
                    output_manager.system_detail(
                        "⚠️  Could not connect to Neo4j - falling back to offline mode"
                    )
                    output_manager.system_detail(
                        "💾  Knowledge graph will be stored as files only"
                    )
                elif verbose:
                    # Only show warning if user explicitly requested online mode
                    click.echo(
                        "⚠️  Could not connect to Neo4j - falling back to offline mode"
                    )
                    click.echo("💾  Knowledge graph will be stored as files only")

    # Chunk the files - minimal or verbose mode
    chunk_results = {}
    processed_count = 0
    skipped_count = 0

    if output_manager and not output_manager.verbose:
        # MINIMAL MODE: No progress bar, just process silently with simple indicator
        import sys

        for i, file_path in enumerate(python_files):
            try:
                rel_path = file_path.relative_to(repo_path)
                chunks = chunker.chunk_file(file_path)
                chunk_results[str(rel_path)] = chunks
                processed_count += 1

                # Simple dot progress for minimalism
                if i % 50 == 0:  # Every 50 files, show a dot
                    sys.stdout.write(".")
                    sys.stdout.flush()
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                skipped_count += 1

        # Clear the dots
        if processed_count > 50:
            sys.stdout.write("\r" + " " * (processed_count // 50) + "\r")
            sys.stdout.flush()
    else:
        # VERBOSE MODE: Show progress bar
        progress = Progress()
        file_task = progress.add_task("Parsing files", total=len(python_files))

        with progress:
            for file_path in python_files:
                try:
                    rel_path = file_path.relative_to(repo_path)
                    chunks = chunker.chunk_file(file_path)
                    chunk_results[str(rel_path)] = chunks
                    processed_count += 1

                    # Verbose mode shows every file
                    progress.update(
                        file_task, advance=1, description=f"Parsing {rel_path}"
                    )

                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    skipped_count += 1
                    progress.update(file_task, advance=1)

    # Flatten chunks
    all_chunks = []
    for file_chunks in chunk_results.values():
        all_chunks.extend(file_chunks)

    if output_manager:
        output_manager.success(f"Parsed {len(all_chunks):,} code chunks")
        if skipped_count > 0:
            output_manager.system_detail(
                f"⚠️  Skipped {skipped_count} files due to errors"
            )
        output_manager.blank_line()
        output_manager.step("Building knowledge graph")
        output_manager.system_detail("🔄 Building knowledge graph...")
    elif verbose:
        click.echo(
            f"✅ Parsed {len(all_chunks)} code chunks from {processed_count} files"
        )
        if skipped_count > 0:
            click.echo(f"⚠️  Skipped {skipped_count} files due to errors")
        # Process chunks with graph adapter
        click.echo("🔄 Building knowledge graph...")
    else:
        # Fallback clean output
        click.echo(f"✓ Parsed {len(all_chunks):,} code chunks")
        click.echo("")
        click.echo("→ Building knowledge graph")

    # Process chunks offline if Neo4j is not available
    if offline_mode:
        # Create output directory
        output_dir = config_path / "knowledge_graph"
        ensure_directory(output_dir)

        # Save chunks to files
        chunks_file = output_dir / "chunks.json"
        with open(chunks_file, "w") as f:
            import json

            chunk_dicts = [chunk.to_dict() for chunk in all_chunks]
            json.dump(chunk_dicts, f, indent=2)

        if output_manager:
            output_manager.system_detail(
                f"💾 Saved {len(all_chunks)} chunks to {chunks_file}"
            )
        elif verbose:
            click.echo(f"💾 Saved {len(all_chunks)} chunks to {chunks_file}")

        # Try limited processing without Neo4j - extract nodes only
        adapter = ChunkGraphAdapter(neo4j_client=None)
        nodes = []
        for chunk in all_chunks:
            try:
                node_dict = adapter.chunk_to_node(chunk)
                nodes.append(node_dict)
            except Exception as e:
                logger.warning(f"Error converting chunk to node: {e}")

        # Save nodes to file
        nodes_file = output_dir / "nodes.json"
        with open(nodes_file, "w") as f:
            import json

            json.dump(nodes, f, indent=2)

        if output_manager:
            output_manager.success("Artifacts saved to .aston/")
            output_manager.system_detail(f"💾 Saved {len(nodes)} nodes to {nodes_file}")
        elif verbose:
            click.echo(f"💾 Saved {len(nodes)} nodes to {nodes_file}")
        else:
            click.echo("✓ Artifacts saved to .aston/")

        # Return counts
        return len(all_chunks), len(nodes)

    # Process chunks with Neo4j
    try:
        adapter = ChunkGraphAdapter(neo4j_client)

        # Process chunks
        chunk_node_map = adapter.process_chunks(all_chunks)

        # Build relationships
        relationships = adapter.build_relationships(all_chunks, chunk_node_map)

        click.echo(
            f"✅ Created {len(chunk_node_map)} nodes and {len(relationships)} relationships in knowledge graph"
        )

        return len(all_chunks), len(chunk_node_map)

    except Exception as e:
        logger.error(f"Error building knowledge graph: {e}")
        raise CLIError(f"Failed to build knowledge graph: {str(e)}")


def perform_incremental_rechunk(
    repo_path: Path,
    config_path: Path,
    file_changes: Dict[str, List[str]],
    filter_contract: FilterContract,
    offline: bool = False,
) -> Tuple[int, int]:
    """Perform incremental rechunking of changed files.

    Args:
        repo_path: Repository root path
        config_path: Configuration directory path
        file_changes: Dictionary with added, modified, removed file lists
        filter_contract: FilterContract instance
        offline: Whether to run in offline mode

    Returns:
        Tuple of (chunks_processed, nodes_updated)
    """
    console = Console()

    # Load existing data
    kg_dir = config_path / "knowledge_graph"
    chunks_file = kg_dir / "chunks.json"
    nodes_file = kg_dir / "nodes.json"

    existing_chunks = []

    if chunks_file.exists():
        with open(chunks_file, "r") as f:
            existing_chunks = json.load(f)

    if nodes_file.exists():
        with open(nodes_file, "r") as f:
            json.load(f)

    # Create chunker
    config = ConfigModel()
    chunker = PythonCodeChunker(config)

    # Process file changes
    new_chunks_count = 0
    processed_files = set()

    # Get all files that need processing (added + modified)
    files_to_process = file_changes["added"] + file_changes["modified"]
    files_to_remove = file_changes["removed"]

    # Remove chunks for deleted files
    if files_to_remove:
        console.print(
            f"🗑️  Removing chunks for {len(files_to_remove)} deleted files..."
        )
        original_chunk_count = len(existing_chunks)
        existing_chunks = [
            c for c in existing_chunks if c.get("file_path") not in files_to_remove
        ]
        removed_chunks = original_chunk_count - len(existing_chunks)
        console.print(f"   Removed {removed_chunks} chunks")

    # Process changed files
    if files_to_process:
        console.print(f"🔄 Processing {len(files_to_process)} changed files...")

        with Progress() as progress:
            task = progress.add_task("Rechunking files", total=len(files_to_process))

            for rel_path in files_to_process:
                try:
                    file_path = repo_path / rel_path
                    if not file_path.exists() or file_path.suffix != ".py":
                        progress.update(task, advance=1)
                        continue

                    # Remove old chunks for this file
                    existing_chunks = [
                        c for c in existing_chunks if c.get("file_path") != rel_path
                    ]

                    # Generate new chunks
                    chunks = chunker.chunk_file(file_path)

                    # Add new chunks
                    for chunk in chunks:
                        chunk_dict = chunk.to_dict()
                        existing_chunks.append(chunk_dict)
                        new_chunks_count += 1

                    processed_files.add(rel_path)
                    progress.update(
                        task, advance=1, description=f"Processing {rel_path}"
                    )

                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    progress.update(task, advance=1)

    # Update chunks file
    with open(chunks_file, "w") as f:
        json.dump(existing_chunks, f, indent=2)

    # Incrementally update nodes - only regenerate nodes for changed files
    from aston.preprocessing.integration.chunk_graph_adapter import ChunkGraphAdapter

    ChunkGraphAdapter(neo4j_client=None)

    # Load existing nodes
    if nodes_file.exists():
        with open(nodes_file, "r") as f:
            all_nodes = json.load(f)
    else:
        all_nodes = []

    # Remove nodes for files that were processed (deleted or modified)
    files_to_update = set(files_to_process + files_to_remove)
    all_nodes = [
        node for node in all_nodes if node.get("file_path") not in files_to_update
    ]

    # Add nodes for new chunks (only from processed files)
    for chunk_dict in existing_chunks:
        file_path = chunk_dict.get("file_path")
        if file_path in processed_files:
            try:
                # Convert dict back to node
                node_dict = {
                    "id": chunk_dict.get("id"),
                    "type": chunk_dict.get("type", "Implementation"),
                    "name": chunk_dict.get("name"),
                    "file_path": chunk_dict.get("file_path"),
                    "start_line": chunk_dict.get("start_line"),
                    "end_line": chunk_dict.get("end_line"),
                    "content": chunk_dict.get("content"),
                }
                all_nodes.append(node_dict)
            except Exception as e:
                logger.warning(f"Error converting chunk to node: {e}")

    # Save updated nodes
    with open(nodes_file, "w") as f:
        json.dump(all_nodes, f, indent=2)

    # Update manifest - reuse the existing manifest from filter_contract
    if filter_contract._manifest is not None:
        # Save the already-generated manifest
        filter_contract.save_manifest(kg_dir)
    else:
        # Fallback: generate new manifest if needed
        filter_contract.generate_manifest()
        filter_contract.save_manifest(kg_dir)

    console.print("✅ Incremental rechunk completed:")
    console.print(f"   📝 Processed {len(processed_files)} files")
    console.print(f"   🧩 Generated {new_chunks_count} new chunks")
    console.print(f"   📊 Total chunks: {len(existing_chunks)}")
    console.print(f"   🎯 Total nodes: {len(all_nodes)}")

    return new_chunks_count, len(all_nodes)


@click.command("init", help="Initialize Knowledge graph for a repository")
@click.option("--path", "-p", type=str, help="Path to repository")
@click.option("--url", "-u", type=str, help="GitHub repository URL to clone")
@click.option("--force", "-f", is_flag=True, help="Force rebuild of existing graph")
@click.option(
    "--rechunk",
    is_flag=True,
    help="Incrementally rechunk only changed files since last run",
)
@click.option(
    "--config-dir", type=str, default=DEFAULT_CONFIG_DIR, help="Configuration directory"
)
@click.option(
    "--online", is_flag=True, help="Run in online mode with Neo4j (default: offline)"
)
@click.option(
    "--offline",
    is_flag=True,
    help="[DEPRECATED] Use offline mode (now default behavior)",
)
@click.option(
    "--create-astonignore",
    is_flag=True,
    help="Create a template .astonignore file and exit",
)
@click.option("--no-env-check", is_flag=True, help="Skip environment dependency check")
@add_filter_options
@common_options
@needs_env("init")
@clean_output
def init_command(
    path,
    url,
    force,
    rechunk,
    config_dir,
    online,
    offline,
    create_astonignore,
    include,
    exclude,
    include_regex,
    exclude_regex,
    preset,
    dry_run,
    show_patterns,
    verbose,
    summary_only: bool = False,
    no_env_check: bool = False,
    _output=None,
    **kwargs,
):
    """Initialize Knowledge graph for a repository.

    This command:
    1. Detects the repository type and root directory
    2. Extracts code chunks from source files
    3. Builds a knowledge graph from the chunks
    4. Writes configuration to disk

    Modes:
    - Default: Full initialization (fails if graph exists)
    - --force: Force full rebuild of existing graph
    - --rechunk: Incrementally update only changed files since last run

    Advanced filtering options:
    - Use --preset for common configurations (python-only, no-tests, source-only, minimal)
    - Use --include/--exclude for glob patterns
    - Use --include-regex/--exclude-regex for regex patterns
    - Create .astonignore file for persistent patterns
    - Use --dry-run to preview file selection

    Examples:
        # Initialize with default offline mode
        aston init

        # Use a preset configuration
        aston init --preset python-only

        # Enable Neo4j integration
        aston init --online

        # Incremental rechunk (fast update)
        aston init --rechunk

        # Include only specific directories
        aston init --include "src/**/*.py" --include "tests/**/*.py"

        # Use regex patterns
        aston init --include-regex ".*/(core|utils)/.*\\.py$"

        # Dry run to see what would be processed
        aston init --dry-run --preset no-tests

        # Create .astonignore template
        aston init --create-astonignore

    Exit codes:
    - 0: Success
    - 1: Error occurred during initialization
    """
    try:
        t0 = time.time()

        # IMMEDIATE logging suppression before any imports
        if not verbose:
            import logging

            logging.getLogger("git-manager").disabled = True
            logging.getLogger().setLevel(logging.ERROR)

        # Clean output is now handled by the @clean_output decorator
        _output.success("Dependencies ready")

        # Determine offline mode: default to offline unless --online is specified
        # Keep backward compatibility: --offline flag does nothing but doesn't error
        force_offline = not online
        if offline and online:
            _output.warning("Both --offline and --online specified. Using --online.")
            force_offline = False

        # Set up the repository
        repo_path = setup_repo(url, path, force, _output)

        # Handle special modes first
        if create_astonignore:
            create_astonignore_template(repo_path)
            return

        # Create and configure file filter
        file_filter = create_file_filter(
            repo_root=repo_path,
            include=include,
            exclude=exclude,
            include_regex=include_regex,
            exclude_regex=exclude_regex,
            preset=preset,
        )

        # Handle display options (show patterns or dry run)
        if handle_filter_display(file_filter, show_patterns, dry_run, verbose):
            return

        # Set up config path
        config_path = repo_path / config_dir
        config_file = config_path / DEFAULT_CONFIG_FILE

        # Check if knowledge graph already exists
        knowledge_graph_dir = config_path / "knowledge_graph"
        if (
            (config_file.exists() or knowledge_graph_dir.exists())
            and not force
            and not rechunk
        ):
            _output.warning("Graph already exists")
            _output.step("Use --force to rebuild or --rechunk to update incrementally")
            return

        # Create config directory
        ensure_directory(config_path)

        # Create filter contract
        filter_contract = FilterContract(file_filter)

        # Detect repository type for clean output
        repo_name = repo_path.name
        _output.success(f"Git repo detected at ./{repo_name}")

        # Generate and save manifest
        knowledge_graph_dir = config_path / "knowledge_graph"
        ensure_directory(knowledge_graph_dir)

        manifest_path = knowledge_graph_dir / "filter_manifest.json"

        # Handle rechunk mode
        if rechunk and manifest_path.exists():
            click.echo("🔄 Rechunk mode: analyzing changes since last run...")

            # Load stored manifest once
            stored_manifest = filter_contract.load_manifest(manifest_path)

            # Check if rechunking is needed (this already generates current manifest internally)
            if not filter_contract.requires_rechunk(manifest_path):
                click.echo("✅ No changes detected - knowledge graph is up to date")
                return

            # Get changed files using the already-generated manifest
            file_changes = filter_contract.get_changed_files(stored_manifest)

            # Display change summary
            total_changes = (
                len(file_changes["added"])
                + len(file_changes["removed"])
                + len(file_changes["modified"])
            )
            click.echo(f"📊 Found {total_changes} changed files:")
            if file_changes["added"]:
                click.echo(f"  ✅ Added: {len(file_changes['added'])} files")
            if file_changes["modified"]:
                click.echo(f"  📝 Modified: {len(file_changes['modified'])} files")
            if file_changes["removed"]:
                click.echo(f"  ❌ Removed: {len(file_changes['removed'])} files")

            # Perform incremental rechunk (pass the filter_contract to avoid regenerating manifest)
            num_chunks, num_nodes = perform_incremental_rechunk(
                repo_path, config_path, file_changes, filter_contract, force_offline
            )

            click.echo(
                f"✨ Rechunk completed: processed {num_chunks} chunks, updated {num_nodes} nodes"
            )

        else:
            # Full initialization
            if rechunk and not manifest_path.exists():
                click.echo(
                    "📋 No previous manifest found - performing full initialization"
                )

            manifest = filter_contract.generate_manifest()
            manifest_path = filter_contract.save_manifest(knowledge_graph_dir)

            # Get filtered Python files from contract
            python_files = filter_contract.get_files_to_process()

            # Clean output for filtering step
            total_files = manifest.get("total_files_discovered", len(python_files))
            _output.step(f"Filtering... {len(python_files)} files from {total_files:,}")
            _output.info(
                f"Generated filter manifest with {manifest['file_count']} files"
            )

            # Run the ingest pipeline with discovered files
            num_chunks, num_nodes = run_ingest_pipeline_with_files(
                repo_path, config_path, force_offline, python_files, verbose, _output
            )

        # Write config file
        neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        vector_store_path = str(config_path / "vectors.sqlite")
        write_config(config_file, neo4j_uri, vector_store_path, _output)

        # Calculate duration
        duration = time.time() - t0

        # Print summary banner
        _output.summary_banner(num_chunks, len(python_files), duration)
        _output.step("Try: `aston coverage` or `aston criticality` next")

        # Verbose details
        _output.system_detail(
            f"Knowledge graph ready (neo4j://{neo4j_uri.split('://')[1]})"
        )
        _output.system_detail(
            f"Processed {num_chunks} chunks into {num_nodes} nodes in {duration:.1f}s"
        )

    except Exception as e:
        if _output:
            _output.error(f"Init failed: {e}")
        else:
            logger.error(f"Error: {e}")
        raise CLIError(f"{e}")
