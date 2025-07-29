"""
Graph data loader for the micro cache layer.

This module provides efficient loading of graph data from various sources
including Neo4j, offline JSON files, and knowledge graph storage.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from aston.core.logging import get_logger
from aston.core.path_resolution import PathResolver
from aston.storage.cache.micro_cache import MicroCache, CacheConfig

logger = get_logger(__name__)


class GraphDataLoader:
    """Efficient loader for graph data from multiple sources."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize the graph data loader."""
        self.config = config or CacheConfig()
        self.path_resolver = PathResolver()

    def load_from_offline_json(
        self, knowledge_graph_dir: Optional[Union[str, Path]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load graph data from offline JSON files.

        Args:
            knowledge_graph_dir: Directory containing graph JSON files

        Returns:
            Tuple of (nodes, edges) lists
        """
        start_time = time.time()

        if knowledge_graph_dir is None:
            knowledge_graph_dir = self.path_resolver.knowledge_graph_dir()
        else:
            knowledge_graph_dir = Path(knowledge_graph_dir)

        if not knowledge_graph_dir.exists():
            logger.warning(
                f"Knowledge graph directory not found: {knowledge_graph_dir}"
            )
            return [], []

        nodes = []
        edges = []

        try:
            # Load nodes
            nodes_file = knowledge_graph_dir / "nodes.json"
            if nodes_file.exists():
                with open(nodes_file, "r") as f:
                    nodes_data = json.load(f)
                    if isinstance(nodes_data, list):
                        nodes = nodes_data
                    elif isinstance(nodes_data, dict) and "nodes" in nodes_data:
                        nodes = nodes_data["nodes"]

                logger.info(f"Loaded {len(nodes)} nodes from {nodes_file}")

            # Load edges/relationships
            edges_file = knowledge_graph_dir / "edges.json"
            relationships_file = knowledge_graph_dir / "relationships.json"

            if edges_file.exists():
                with open(edges_file, "r") as f:
                    edges_data = json.load(f)
                    if isinstance(edges_data, list):
                        edges = edges_data
                    elif isinstance(edges_data, dict) and "edges" in edges_data:
                        edges = edges_data["edges"]

                logger.info(f"Loaded {len(edges)} edges from {edges_file}")

            elif relationships_file.exists():
                with open(relationships_file, "r") as f:
                    relationships_data = json.load(f)
                    if isinstance(relationships_data, list):
                        edges = relationships_data
                    elif (
                        isinstance(relationships_data, dict)
                        and "relationships" in relationships_data
                    ):
                        edges = relationships_data["relationships"]

                logger.info(
                    f"Loaded {len(edges)} relationships from {relationships_file}"
                )

            # Normalize edge format
            edges = self._normalize_edge_format(edges)

            duration = time.time() - start_time
            logger.info(f"Loaded graph data from offline JSON in {duration:.2f}s")

            return nodes, edges

        except Exception as e:
            logger.error(f"Failed to load offline graph data: {e}")
            return [], []

    def load_from_config(
        self, config: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load graph data based on configuration.

        Args:
            config: Configuration dictionary containing data source info

        Returns:
            Tuple of (nodes, edges) lists
        """
        # Only support offline mode for core implementation
        knowledge_graph_dir = config.get("knowledge_graph_dir")
        return self.load_from_offline_json(knowledge_graph_dir)

    def _normalize_edge_format(
        self, edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize edge format for consistent caching.

        Args:
            edges: List of edge dictionaries with potentially different formats

        Returns:
            List of normalized edge dictionaries
        """
        normalized = []

        for edge in edges:
            normalized_edge = {
                "id": edge.get("id"),
                "type": edge.get("type", edge.get("relationship_type")),
                "source_id": edge.get("source_id", edge.get("from_id")),
                "target_id": edge.get("target_id", edge.get("to_id")),
                "properties": edge.get("properties", {}),
            }

            # Add any additional fields
            for key, value in edge.items():
                if key not in normalized_edge:
                    normalized_edge[key] = value

            normalized.append(normalized_edge)

        return normalized


def load_and_warm_cache(
    config: Dict[str, Any],
    cache_config: Optional[CacheConfig] = None,
    force_reload: bool = False,
) -> MicroCache:
    """Load graph data and warm up the micro cache.

    Args:
        config: Data source configuration
        cache_config: Cache configuration
        force_reload: Force cache reload even if already warmed

    Returns:
        Configured and warmed MicroCache instance
    """
    from aston.storage.cache.micro_cache import get_micro_cache

    cache = get_micro_cache(cache_config)

    # Check if already warmed up (unless forcing reload)
    if not force_reload and cache.is_warmed_up():
        logger.info("Cache already contains data, skipping reload")
        return cache

    loader = GraphDataLoader(cache_config)
    nodes, edges = loader.load_from_config(config)

    if nodes or edges:
        cache.warm_up_cache(nodes, edges, force=force_reload)
        logger.info(f"Warmed cache with {len(nodes)} nodes and {len(edges)} edges")
    else:
        logger.warning("No graph data found to warm cache")

    return cache


def get_cache_with_data(
    config: Dict[str, Any], cache_config: Optional[CacheConfig] = None
) -> MicroCache:
    """Get a micro cache instance with pre-loaded data.

    Args:
        config: Data source configuration
        cache_config: Cache configuration

    Returns:
        MicroCache instance with data loaded
    """
    return load_and_warm_cache(config, cache_config)
