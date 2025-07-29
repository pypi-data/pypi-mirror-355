"""
Data loading utilities for test suggestion engine.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

from aston.core.logging import get_logger
from .exceptions import SuggestionError

logger = get_logger(__name__)


class DataLoader:
    """Handles loading of nodes, edges, and critical path data."""

    @staticmethod
    def load_nodes(nodes_file: Path) -> List[Dict[str, Any]]:
        """Load nodes from JSON file.

        Args:
            nodes_file: Path to nodes.json

        Returns:
            List of node dictionaries
        """
        try:
            with open(nodes_file, "r") as f:
                nodes = json.load(f)
            logger.info(f"Loaded {len(nodes)} nodes from {nodes_file}")
            return nodes
        except Exception as e:
            raise SuggestionError(f"Failed to load nodes: {str(e)}")

    @staticmethod
    def load_critical_path(critical_path_file: Path) -> List[Dict[str, Any]]:
        """Load critical path data from JSON file.

        Args:
            critical_path_file: Path to critical_path.json

        Returns:
            List of critical node dictionaries
        """
        try:
            with open(critical_path_file, "r") as f:
                critical_data = json.load(f)

            # Extract nodes if the structure has 'nodes' key
            if isinstance(critical_data, dict) and "nodes" in critical_data:
                nodes = critical_data["nodes"]
            else:
                nodes = critical_data

            logger.info(f"Loaded {len(nodes)} critical nodes from {critical_path_file}")
            return nodes
        except Exception as e:
            raise SuggestionError(f"Failed to load critical path data: {str(e)}")

    @staticmethod
    def load_edges(edges_file: Path) -> List[Dict[str, Any]]:
        """Load edges from JSON file.

        Args:
            edges_file: Path to edges.json

        Returns:
            List of edge dictionaries
        """
        try:
            with open(edges_file, "r") as f:
                edges = json.load(f)

            # Extract edges if the structure has 'edges' key
            if isinstance(edges, dict) and "edges" in edges:
                edges = edges["edges"]

            logger.info(f"Loaded {len(edges)} edges from {edges_file}")
            return edges
        except Exception as e:
            raise SuggestionError(f"Failed to load edges: {str(e)}")

    @staticmethod
    def build_lookup_maps(nodes: List[Dict[str, Any]]) -> tuple[Dict[str, Dict], Dict[str, List[str]]]:
        """Build lookup maps for efficient node access.

        Args:
            nodes: List of node dictionaries

        Returns:
            Tuple of (nodes_map, file_nodes_map)
        """
        nodes_map = {}  # id -> node
        file_nodes_map = {}  # file_path -> [node_ids]

        for node in nodes:
            node_id = node.get("id")
            if node_id:
                nodes_map[node_id] = node

                # Build file -> nodes mapping
                file_path = node.get("file_path")
                if file_path:
                    if file_path not in file_nodes_map:
                        file_nodes_map[file_path] = []
                    file_nodes_map[file_path].append(node_id)

        logger.info(
            f"Built lookup maps: {len(nodes_map)} nodes, {len(file_nodes_map)} files"
        )
        return nodes_map, file_nodes_map 