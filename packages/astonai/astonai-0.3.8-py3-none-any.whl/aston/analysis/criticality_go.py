"""
Go-based criticality scorer integration.

This module provides a Python interface to the Go-based criticality scorer binary,
offering significant performance improvements over the pure Python implementation.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

import logging

logger = logging.getLogger(__name__)


class BinaryNotFoundError(Exception):
    """Raised when the Go binary cannot be found."""

    pass


class GoCriticalityError(Exception):
    """Raised when the Go binary execution fails."""

    pass


class GoCriticalityScorer:
    """
    Go-based criticality scorer for high-performance graph analysis.

    This class provides a Python interface to the aston-rank Go binary,
    offering significant performance improvements for large codebases.
    """

    def __init__(self, binary_path: Optional[Path] = None):
        """
        Initialize the Go criticality scorer.

        Args:
            binary_path: Optional explicit path to the aston-rank binary.
                        If None, will search for the binary automatically.
        """
        self.binary_path = binary_path or self._find_binary()
        self._validate_binary()

    def _find_binary(self) -> Optional[Path]:
        """
        Find the aston-rank binary in various locations.

        Search order:
        1. aston/bin/aston-rank-{platform} (bundled with package)
        2. aston/bin/aston-rank (development)
        3. ~/.aston/bin/aston-rank (user-installed)
        4. PATH environment variable (system-installed)

        Returns:
            Path to the binary, or None if not found.
        """
        # Detect platform for bundled binaries
        platform_suffix = self._detect_platform()

        # 1. Bundled platform-specific binary
        if platform_suffix:
            bundled_binary = (
                Path(__file__).parent.parent / "bin" / f"aston-rank-{platform_suffix}"
            )
            if bundled_binary.exists() and bundled_binary.is_file():
                logger.debug(f"Found bundled binary: {bundled_binary}")
                return bundled_binary

            # Windows adds .exe
            if sys.platform == "win32" and not bundled_binary.name.endswith(".exe"):
                win_binary = Path(f"{bundled_binary}.exe")
                if win_binary.exists() and win_binary.is_file():
                    logger.debug(f"Found bundled Windows binary: {win_binary}")
                    return win_binary

        # 2. Development binary (relative to this file)
        dev_binary = Path(__file__).parent.parent / "bin" / "aston-rank"
        if dev_binary.exists() and dev_binary.is_file():
            logger.debug(f"Found development binary: {dev_binary}")
            return dev_binary

        # 3. User-installed binary
        user_binary = Path.home() / ".aston" / "bin" / "aston-rank"
        if user_binary.exists() and user_binary.is_file():
            logger.debug(f"Found user binary: {user_binary}")
            return user_binary

        # 4. System PATH
        system_binary = shutil.which("aston-rank")
        if system_binary:
            logger.debug(f"Found system binary: {system_binary}")
            return Path(system_binary)

        # 5. Legacy: look for aston-criticality for backward compatibility
        legacy_binary = Path(__file__).parent.parent / "bin" / "aston-criticality"
        if legacy_binary.exists() and legacy_binary.is_file():
            logger.debug(f"Found legacy binary: {legacy_binary}")
            return legacy_binary

        legacy_system = shutil.which("aston-criticality")
        if legacy_system:
            logger.debug(f"Found legacy system binary: {legacy_system}")
            return Path(legacy_system)

        logger.warning("Go binary not found in any location")
        return None

    def _detect_platform(self) -> Optional[str]:
        """
        Detect the current platform for binary selection.

        Returns:
            Platform identifier (e.g., 'darwin-arm64') or None if unknown.
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "darwin":
            # macOS
            if machine == "x86_64" or machine == "amd64":
                return "darwin-amd64"
            elif machine == "arm64":
                return "darwin-arm64"
        elif system == "linux":
            # Linux
            if machine == "x86_64" or machine == "amd64":
                return "linux-amd64"
            elif machine == "aarch64" or machine == "arm64":
                return "linux-arm64"
        elif system == "windows":
            # Windows
            if machine == "amd64" or machine == "x86_64":
                return "windows-amd64"

        logger.warning(f"Unknown platform: {system}-{machine}")
        return None

    def _validate_binary(self) -> None:
        """
        Validate that the binary exists and is executable.

        Raises:
            BinaryNotFoundError: If binary is not found or not executable.
        """
        if not self.binary_path:
            raise BinaryNotFoundError(
                "aston-rank binary not found. Please install it or use --scorer python"
            )

        if not self.binary_path.exists():
            raise BinaryNotFoundError(f"Binary does not exist: {self.binary_path}")

        if not os.access(self.binary_path, os.X_OK):
            # On Windows, .exe files might not show as executable with os.access
            if not (
                sys.platform == "win32" and self.binary_path.suffix.lower() == ".exe"
            ):
                raise BinaryNotFoundError(
                    f"Binary is not executable: {self.binary_path}"
                )

        # Test binary with version check
        try:
            result = subprocess.run(
                [str(self.binary_path), "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise BinaryNotFoundError(
                    f"Binary version check failed: {result.stderr}"
                )
            logger.debug(f"Binary version: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            raise BinaryNotFoundError("Binary version check timed out")
        except Exception as e:
            raise BinaryNotFoundError(f"Binary validation failed: {e}")

    def calculate_scores(
        self,
        nodes_file: Union[str, Path],
        edges_file: Union[str, Path],
        top_k: int = 50,
        algorithm: str = "degree",
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate criticality scores using the Go binary.

        Args:
            nodes_file: Path to the nodes.json file
            edges_file: Path to the edges.json file
            top_k: Number of top nodes to return (default: 50)
            algorithm: Algorithm to use (default: "degree")
            verbose: Enable verbose logging

        Returns:
            Dictionary containing the scoring results

        Raises:
            GoCriticalityError: If the Go binary execution fails
        """
        start_time = time.time()

        # Convert paths to strings
        nodes_file = str(Path(nodes_file))
        edges_file = str(Path(edges_file))

        # Validate input files
        if not os.path.exists(nodes_file):
            raise GoCriticalityError(f"Nodes file does not exist: {nodes_file}")
        if not os.path.exists(edges_file):
            raise GoCriticalityError(f"Edges file does not exist: {edges_file}")

        # Build command
        cmd = [
            str(self.binary_path),
            "-nodes",
            nodes_file,
            "-edges",
            edges_file,
            "-top",
            str(top_k),
            "-algorithm",
            algorithm,
        ]

        if verbose:
            cmd.append("-verbose")

        logger.debug(f"Executing Go binary: {' '.join(cmd)}")

        try:
            # Execute the binary
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise GoCriticalityError(f"Go binary failed: {error_msg}")

            # Parse JSON output
            try:
                response = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise GoCriticalityError(f"Failed to parse JSON output: {e}")

            # Add Python execution metadata
            execution_time = time.time() - start_time
            response["python_execution_time_ms"] = int(execution_time * 1000)

            if verbose and result.stderr:
                logger.info(f"Go binary stderr: {result.stderr.strip()}")

            return response

        except subprocess.TimeoutExpired:
            raise GoCriticalityError("Go binary execution timed out")
        except Exception as e:
            raise GoCriticalityError(f"Failed to execute Go binary: {e}")

    def get_top_critical_nodes(
        self,
        nodes_file: Union[str, Path],
        edges_file: Union[str, Path],
        limit: int = 50,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Get top critical nodes with compatibility for existing Python API.

        This method provides compatibility with the existing Python CriticalityScorer.

        Args:
            nodes_file: Path to the nodes.json file
            edges_file: Path to the edges.json file
            limit: Number of top nodes to return
            **kwargs: Additional arguments (algorithm, verbose, etc.)

        Returns:
            List of top critical nodes with score and metadata
        """
        algorithm = kwargs.get("algorithm", "degree")
        verbose = kwargs.get("verbose", False)

        result = self.calculate_scores(
            nodes_file=nodes_file,
            edges_file=edges_file,
            top_k=limit,
            algorithm=algorithm,
            verbose=verbose,
        )

        # Transform to match Python API format
        top_nodes = result.get("top_nodes", [])

        # Load full node data for enhanced display
        enriched_nodes = self._enrich_with_node_data(top_nodes, nodes_file)
        return enriched_nodes

    def _enrich_with_node_data(
        self, top_nodes: List[Dict[str, Any]], nodes_file: Union[str, Path]
    ) -> List[Dict[str, Any]]:
        """
        Enrich Go scorer results with full node metadata for enhanced display.

        Args:
            top_nodes: List of top nodes from Go scorer
            nodes_file: Path to nodes.json file with full metadata

        Returns:
            List of enriched nodes with full metadata
        """
        try:
            # Load full node data
            with open(nodes_file, "r") as f:
                all_nodes = json.load(f)

            # Create lookup map for fast access
            node_lookup = {node["id"]: node for node in all_nodes}

            # Enrich each top node with full metadata
            enriched_nodes = []
            for go_node in top_nodes:
                node_id = go_node.get("node_id", "")
                full_node = node_lookup.get(node_id, {})

                # Merge Go scoring data with full node metadata
                enriched_node = {
                    # Core identification
                    "id": node_id,
                    "score": go_node.get("score", 0.0),
                    "rank": go_node.get("rank", 0),
                    # Enhanced metadata from full node data
                    "type": full_node.get("type", "unknown"),
                    "name": full_node.get("name", "unknown"),
                    "node_name": full_node.get(
                        "name", "unknown"
                    ),  # Alias for compatibility
                    "file_path": full_node.get("file_path", "unknown"),
                    "line_number": full_node.get("line_number"),
                    "description": full_node.get("description", ""),
                    "properties": full_node.get("properties", {}),
                    # Go scorer metadata
                    "degree_in": go_node.get("metadata", {}).get("degree_in", 0),
                    "degree_out": go_node.get("metadata", {}).get("degree_out", 0),
                    # Keep original data for debugging
                    "_original_go": go_node,
                    "_original_node": full_node,
                }
                enriched_nodes.append(enriched_node)

            return enriched_nodes

        except Exception as e:
            logger.warning(f"Failed to enrich node data, using basic metadata: {e}")
            # Fallback to basic transformation
            return self._basic_transform_nodes(top_nodes)

    def _basic_transform_nodes(
        self, top_nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback transformation when full node data is not available."""
        transformed_nodes = []
        for node in top_nodes:
            transformed_node = {
                "id": node.get("node_id", "unknown"),
                "score": node.get("score", 0.0),
                "rank": node.get("rank", 0),
                "type": node.get("metadata", {}).get("node_type", "unknown"),
                "node_name": node.get("metadata", {}).get("node_name", "unknown"),
                "file_path": node.get("metadata", {}).get("file_path", "unknown"),
                "degree_in": node.get("metadata", {}).get("degree_in", 0),
                "degree_out": node.get("metadata", {}).get("degree_out", 0),
                "_original": node,
            }
            transformed_nodes.append(transformed_node)
        return transformed_nodes

    def is_available(self) -> bool:
        """
        Check if the Go binary is available and working.

        Returns:
            True if the Go binary is available, False otherwise.
        """
        try:
            self._validate_binary()
            return True
        except BinaryNotFoundError:
            return False

    def get_algorithm_info(self, algorithm: str = "degree") -> Dict[str, Any]:
        """
        Get information about a specific algorithm.

        Args:
            algorithm: Name of the algorithm

        Returns:
            Dictionary with algorithm information

        Raises:
            GoCriticalityError: If retrieving algorithm info fails
        """
        try:
            result = subprocess.run(
                [str(self.binary_path), "-info", "-algorithm", algorithm],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise GoCriticalityError(
                    f"Failed to get algorithm info: {result.stderr}"
                )

            return {"name": algorithm, "description": result.stdout.strip()}

        except Exception as e:
            raise GoCriticalityError(f"Failed to get algorithm info: {e}")


def get_available_scorers() -> Tuple[bool, bool]:
    """
    Check which scorers are available (Go and/or Python).

    Returns:
        Tuple of (go_available, python_available)
    """
    # Check Go availability
    go_available = False
    try:
        GoCriticalityScorer()
        go_available = True
    except BinaryNotFoundError:
        go_available = False

    # Check Python availability
    python_available = True  # Python scorer is always available as it's pure Python

    return go_available, python_available


def create_scorer(
    scorer_type: str = "auto",
) -> Union["GoCriticalityScorer", "CriticalityScorer"]:
    """
    Create a criticality scorer based on preference and availability.

    Args:
        scorer_type: Type of scorer to create:
                    - "auto": Use Go if available, otherwise Python
                    - "go": Use Go scorer (raises error if not available)
                    - "python": Use Python scorer

    Returns:
        Criticality scorer instance

    Raises:
        BinaryNotFoundError: If Go scorer is requested but not available
        ImportError: If Python scorer cannot be imported
    """
    go_available, python_available = get_available_scorers()

    # Explicit Go request
    if scorer_type.lower() == "go":
        if go_available:
            logger.info("Using Go criticality scorer")
            return GoCriticalityScorer()
        else:
            raise BinaryNotFoundError(
                "Go criticality scorer was requested but binary not found"
            )

    # Explicit Python request
    if scorer_type.lower() == "python":
        logger.info("Using Python criticality scorer")
        from aston.analysis.criticality_scorer import CriticalityScorer

        return CriticalityScorer()

    # Auto selection
    if go_available:
        logger.info("Auto-selected Go criticality scorer for better performance")
        return GoCriticalityScorer()
    else:
        logger.info("Auto-selected Python criticality scorer (Go binary not found)")
        from aston.analysis.criticality_scorer import CriticalityScorer

        return CriticalityScorer()


# Backwards compatibility
GoScorer = GoCriticalityScorer
