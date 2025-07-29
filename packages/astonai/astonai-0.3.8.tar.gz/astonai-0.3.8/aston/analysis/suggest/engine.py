"""
Aston Suggestion Engine - Multi-Purpose Code Intelligence.

This module provides the main SuggestionEngine class for generating various
types of suggestions: tests, UAT scenarios, documentation, comments, and more.

Clean API ready for NL-Router integration and future suggestion types.
"""

import json
import os
import time
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from aston.core.logging import get_logger
from aston.core.path_resolution import PathResolver
from aston.analysis.criticality_scorer import CriticalityScorer, CriticalityWeights

from .exceptions import SuggestionError
from .data_loaders import DataLoader
from .generators.heuristic import HeuristicGenerator
from .generators.llm import LLMGenerator

logger = get_logger(__name__)


class SuggestionEngine:
    """
    Multi-purpose suggestion engine for Aston's expanding intelligence surface.
    
    Currently supports:
    - Test generation (pytest, unit tests, integration tests)
    
    Future capabilities:
    - UAT scenario generation
    - Documentation suggestions  
    - Code improvement recommendations
    - Refactoring suggestions
    """

    def __init__(
        self,
        llm_enabled: bool = False,
        model: str = "gpt-4o",
        budget: float = 0.03,
        criticality_weights: Optional[CriticalityWeights] = None,
    ):
        """Initialize the suggestion engine.

        Args:
            llm_enabled: Whether to use LLM for suggestions
            model: LLM model to use (if enabled)
            budget: Maximum cost per suggestion in dollars
            criticality_weights: Custom criticality weights for ranking
        """
        self.llm_enabled = llm_enabled
        self.model = model
        self.budget = Decimal(str(budget))
        
        # Initialize generators
        self.heuristic_generator = HeuristicGenerator()
        self.llm_generator = LLMGenerator(model, budget) if llm_enabled else None
        
        # Initialize data management
        self.data_loader = DataLoader()
        self.criticality_scorer = CriticalityScorer(criticality_weights)
        
        # Cache for loaded data
        self.nodes_map = {}  # id -> node
        self.file_nodes_map = {}  # file_path -> [node_ids]
        self._all_nodes = []  # Cache for all nodes
        self._all_edges = []  # Cache for all edges

    def generate_test_suggestions(
        self,
        target: str,
        nodes_file: Optional[Union[str, Path]] = None,
        critical_path_file: Optional[Union[str, Path]] = None,
        edges_file: Optional[Union[str, Path]] = None,
        output_file: Optional[Union[str, Path]] = None,
        k: int = 5,
        use_criticality: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate test suggestions for the target file or node.
        
        This is the current primary method. Future methods will include:
        - generate_uat_suggestions()
        - generate_doc_suggestions()  
        - generate_comment_suggestions()

        Args:
            target: Path to file or fully-qualified node name
            nodes_file: Path to the nodes.json file (optional)
            critical_path_file: Path to the critical_path.json file (optional)
            edges_file: Path to the edges.json file (optional, for criticality)
            output_file: Path to write the suggestions file (optional)
            k: Maximum number of suggestions to generate
            use_criticality: Whether to use criticality-based ranking

        Returns:
            List of test suggestions
        """
        return self._generate_suggestions(
            target=target,
            suggestion_type="test",
            nodes_file=nodes_file,
            critical_path_file=critical_path_file,
            edges_file=edges_file,
            output_file=output_file,
            k=k,
            use_criticality=use_criticality
        )

    # Backward compatibility alias
    def generate_suggestions(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Backward compatibility alias for generate_test_suggestions."""
        return self.generate_test_suggestions(*args, **kwargs)

    def _generate_suggestions(
        self,
        target: str,
        suggestion_type: str = "test",
        nodes_file: Optional[Union[str, Path]] = None,
        critical_path_file: Optional[Union[str, Path]] = None,
        edges_file: Optional[Union[str, Path]] = None,
        output_file: Optional[Union[str, Path]] = None,
        k: int = 5,
        use_criticality: bool = True,
    ) -> List[Dict[str, Any]]:
        """Internal method for generating various types of suggestions."""
        start_time = time.time()

        # Use default paths if not provided
        if nodes_file is None:
            nodes_file = PathResolver.nodes_file()
        if critical_path_file is None:
            critical_path_file = PathResolver.knowledge_graph_dir() / "critical_path.json"
        if edges_file is None:
            edges_file = PathResolver.edges_file()
        if output_file is None:
            output_file = PathResolver.knowledge_graph_dir() / f"{suggestion_type}_suggestions.json"

        nodes_file = Path(nodes_file)
        critical_path_file = Path(critical_path_file)
        edges_file = Path(edges_file)
        output_file = Path(output_file)

        logger.info(f"Generating {suggestion_type} suggestions for target: {target}")

        # Ensure nodes file exists
        if not nodes_file.exists():
            raise SuggestionError(f"Nodes file not found: {nodes_file}")

        # Load all data
        nodes = self.data_loader.load_nodes(nodes_file)
        self._cache_data(nodes)

        # Load edges for criticality ranking if requested
        edges = []
        if use_criticality and edges_file.exists():
            try:
                edges = self.data_loader.load_edges(edges_file)
                self._all_edges = edges
                logger.info(f"Loaded {len(edges)} edges for criticality ranking")
            except Exception as e:
                logger.warning(f"Failed to load edges for criticality ranking: {e}")
                use_criticality = False

        # Load critical path if available
        critical_nodes = []
        if critical_path_file.exists():
            try:
                critical_nodes = self.data_loader.load_critical_path(critical_path_file)
                logger.info(f"Loaded {len(critical_nodes)} critical nodes")
            except Exception as e:
                logger.warning(f"Failed to load critical path data: {e}")

        # Identify target nodes
        is_file_path = os.path.exists(target) or "/" in target or "\\" in target
        target_nodes = self._identify_target_nodes(target, is_file_path)

        if not target_nodes:
            raise SuggestionError(f"No matching nodes found for target: {target}")

        logger.info(f"Found {len(target_nodes)} target nodes")

        # Prioritize nodes
        prioritized_nodes = self._prioritize_nodes(target_nodes, critical_nodes, use_criticality)

        # Generate suggestions based on type
        suggestions = self._generate_typed_suggestions(prioritized_nodes, suggestion_type, k)

        # Write output
        self._write_output(suggestions, output_file, suggestion_type)

        duration = time.time() - start_time
        logger.info(f"Generated {len(suggestions)} {suggestion_type} suggestions in {duration:.2f}s")

        return suggestions

    def _cache_data(self, nodes: List[Dict[str, Any]]) -> None:
        """Cache loaded data for efficient access."""
        self._all_nodes = nodes
        self.nodes_map, self.file_nodes_map = self.data_loader.build_lookup_maps(nodes)

    def _identify_target_nodes(self, target: str, is_file_path: bool) -> List[Dict[str, Any]]:
        """Identify nodes matching the target."""
        if is_file_path:
            # Find nodes by file path
            target_nodes = []
            for node in self._all_nodes:
                node_file = node.get("file_path", "")
                if target in node_file or node_file.endswith(target):
                    target_nodes.append(node)
            return target_nodes
        else:
            # Find nodes by name (exact match)
            target_nodes = []
            for node in self._all_nodes:
                if node.get("name") == target:
                    target_nodes.append(node)
            return target_nodes

    def _prioritize_nodes(
        self,
        target_nodes: List[Dict[str, Any]],
        critical_nodes: List[Dict[str, Any]],
        use_criticality: bool = True,
    ) -> List[Dict[str, Any]]:
        """Prioritize nodes based on criticality or critical path."""
        if not target_nodes:
            return []

        # Create priority mapping from critical path
        critical_ids = {node.get("id") for node in critical_nodes}
        
        def get_node_priority(node):
            node_id = node.get("id")
            
            # Highest priority: critical path nodes
            if node_id in critical_ids:
                return (3, 0)  # (priority_level, -criticality_score)
            
            # Medium priority: use criticality if enabled
            if use_criticality:
                try:
                    criticality = self.criticality_scorer.calculate_criticality(
                        node, self._all_nodes, self._all_edges
                    )
                    return (2, -criticality)  # Negative for descending sort
                except Exception:
                    return (1, 0)  # Low priority if scoring fails
            
            # Default priority
            return (1, 0)

        # Sort by priority
        prioritized = sorted(target_nodes, key=get_node_priority, reverse=True)
        
        logger.info(f"Prioritized {len(prioritized)} nodes")
        return prioritized

    def _generate_typed_suggestions(self, nodes: List[Dict[str, Any]], suggestion_type: str, k: int) -> List[Dict[str, Any]]:
        """Generate suggestions of the specified type."""
        all_suggestions = []
        
        for node in nodes:
            # Generate heuristic suggestions
            heuristic_suggestions = self.heuristic_generator.generate_suggestions(node)
            all_suggestions.extend(heuristic_suggestions)
            
            # Generate LLM suggestions if enabled
            if self.llm_enabled and self.llm_generator:
                try:
                    llm_suggestions = self.llm_generator.generate_suggestions(node)
                    all_suggestions.extend(llm_suggestions)
                except Exception as e:
                    logger.warning(f"LLM suggestion generation failed: {e}")

        # Sort by coverage gain and take top k
        all_suggestions.sort(key=lambda x: x.get("estimated_coverage_gain", 0), reverse=True)
        return all_suggestions[:k]

    def _write_output(self, suggestions: List[Dict[str, Any]], output_file: Path, suggestion_type: str) -> None:
        """Write suggestions to output file."""
        try:
            output_data = {
                "suggestion_type": suggestion_type,
                "suggestions": suggestions,
                "metadata": {
                    "version": "K1",
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "count": len(suggestions)
                }
            }
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
                
            logger.info(f"{suggestion_type.capitalize()} suggestions written to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to write output: {e}")
            raise SuggestionError(f"Failed to write output: {e}")

    # Backward compatibility alias
    generate_suggestions = generate_test_suggestions 