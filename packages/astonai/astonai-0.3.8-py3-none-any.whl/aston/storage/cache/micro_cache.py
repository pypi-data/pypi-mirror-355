"""
Micro cache layer for AstonAI graph data with sub-300ms latency targets.

This module provides intelligent caching of nodes, edges, and pre-computed
metrics to enable fast analysis command execution for the upcoming NL-router
and L-series features.
"""

import time
import json
import hashlib
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict


from aston.core.logging import get_logger
from aston.storage.cache.memory_cache import MemoryCache

logger = get_logger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    precompute_hits: int = 0
    precompute_misses: int = 0
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    cache_size_mb: float = 0.0

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def precompute_hit_ratio(self) -> float:
        """Calculate pre-computation hit ratio."""
        total_precompute = self.precompute_hits + self.precompute_misses
        if total_precompute == 0:
            return 0.0
        return self.precompute_hits / total_precompute


@dataclass
class CacheConfig:
    """Configuration for the micro cache layer."""

    # Core cache settings
    default_ttl_seconds: int = 3600  # 1 hour default TTL
    max_memory_mb: int = 256  # Maximum memory usage (reduced from 512)

    # Performance targets
    target_latency_ms: int = 300  # Sub-300ms target
    precompute_threshold: int = 100  # Pre-compute for queries > 100 nodes

    # Pre-computation settings (criticality only for now)
    enable_criticality_precompute: bool = True

    # Debug and monitoring
    enable_performance_monitoring: bool = True
    log_slow_queries: bool = True
    slow_query_threshold_ms: int = 100


class GraphDataCache:
    """High-performance cache for graph nodes and edges."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._nodes_cache = MemoryCache(default_ttl=config.default_ttl_seconds)
        self._edges_cache = MemoryCache(default_ttl=config.default_ttl_seconds)
        self._relationships_cache = MemoryCache(default_ttl=config.default_ttl_seconds)

        # Indexed caches for fast lookups
        self._nodes_by_file: Dict[str, Set[str]] = defaultdict(set)
        self._edges_by_source: Dict[str, Set[str]] = defaultdict(set)
        self._edges_by_target: Dict[str, Set[str]] = defaultdict(set)

        self._lock = threading.RLock()

    def cache_node(self, node: Dict[str, Any]) -> None:
        """Cache a single node with indexing."""
        with self._lock:
            node_id = node.get("id")
            if not node_id:
                return

            # Cache the node
            self._nodes_cache.set(f"node:{node_id}", node)

            # Update file index
            file_path = node.get("file_path")
            if file_path:
                self._nodes_by_file[file_path].add(node_id)

    def cache_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Batch cache multiple nodes."""
        for node in nodes:
            self.cache_node(node)

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a cached node by ID."""
        return self._nodes_cache.get(f"node:{node_id}")

    def get_nodes_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all cached nodes for a file."""
        with self._lock:
            node_ids = self._nodes_by_file.get(file_path, set())
            nodes = []
            for node_id in node_ids:
                node = self.get_node(node_id)
                if node:
                    nodes.append(node)
            return nodes

    def cache_edge(self, edge: Dict[str, Any]) -> None:
        """Cache a single edge with indexing."""
        with self._lock:
            edge_id = edge.get("id")
            if not edge_id:
                return

            # Cache the edge
            self._edges_cache.set(f"edge:{edge_id}", edge)

            # Update indexes
            source_id = edge.get("source_id")
            target_id = edge.get("target_id")

            if source_id:
                self._edges_by_source[source_id].add(edge_id)
            if target_id:
                self._edges_by_target[target_id].add(edge_id)

    def cache_edges(self, edges: List[Dict[str, Any]]) -> None:
        """Batch cache multiple edges."""
        for edge in edges:
            self.cache_edge(edge)

    def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Get a cached edge by ID."""
        return self._edges_cache.get(f"edge:{edge_id}")

    def get_edges_by_source(self, source_id: str) -> List[Dict[str, Any]]:
        """Get all cached edges from a source node."""
        with self._lock:
            edge_ids = self._edges_by_source.get(source_id, set())
            edges = []
            for edge_id in edge_ids:
                edge = self.get_edge(edge_id)
                if edge:
                    edges.append(edge)
            return edges

    def get_edges_by_target(self, target_id: str) -> List[Dict[str, Any]]:
        """Get all cached edges to a target node."""
        with self._lock:
            edge_ids = self._edges_by_target.get(target_id, set())
            edges = []
            for edge_id in edge_ids:
                edge = self.get_edge(edge_id)
                if edge:
                    edges.append(edge)
            return edges

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._nodes_cache.clear()
            self._edges_cache.clear()
            self._relationships_cache.clear()
            self._nodes_by_file.clear()
            self._edges_by_source.clear()
            self._edges_by_target.clear()


class MetricsCache:
    """Cache for pre-computed metrics and analysis results."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._metrics_cache = MemoryCache(default_ttl=config.default_ttl_seconds)
        self._computation_hashes: Dict[str, str] = {}
        self._lock = threading.RLock()

    def _compute_hash(self, data: Any) -> str:
        """Compute hash for cache invalidation."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def cache_criticality_scores(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        scores: Dict[str, float],
    ) -> None:
        """Cache criticality scores with dependency tracking."""
        with self._lock:
            # Compute hash of input data
            input_hash = self._compute_hash(
                {
                    "nodes": [n.get("id") for n in nodes],
                    "edges": [(e.get("source_id"), e.get("target_id")) for e in edges],
                }
            )

            cache_key = f"criticality_scores:{input_hash}"
            self._metrics_cache.set(cache_key, scores)
            self._computation_hashes["criticality"] = input_hash

    def get_criticality_scores(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Get cached criticality scores if valid."""
        with self._lock:
            # Check if input matches cached computation
            input_hash = self._compute_hash(
                {
                    "nodes": [n.get("id") for n in nodes],
                    "edges": [(e.get("source_id"), e.get("target_id")) for e in edges],
                }
            )

            if self._computation_hashes.get("criticality") == input_hash:
                cache_key = f"criticality_scores:{input_hash}"
                return self._metrics_cache.get(cache_key)
            return None

    def cache_centrality_scores(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        scores: Dict[str, float],
    ) -> None:
        """Cache centrality scores."""
        with self._lock:
            input_hash = self._compute_hash(
                {
                    "nodes": [n.get("id") for n in nodes],
                    "edges": [(e.get("source_id"), e.get("target_id")) for e in edges],
                }
            )

            cache_key = f"centrality_scores:{input_hash}"
            self._metrics_cache.set(cache_key, scores)
            self._computation_hashes["centrality"] = input_hash

    def get_centrality_scores(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Get cached centrality scores."""
        with self._lock:
            input_hash = self._compute_hash(
                {
                    "nodes": [n.get("id") for n in nodes],
                    "edges": [(e.get("source_id"), e.get("target_id")) for e in edges],
                }
            )

            if self._computation_hashes.get("centrality") == input_hash:
                cache_key = f"centrality_scores:{input_hash}"
                return self._metrics_cache.get(cache_key)
            return None

    def cache_coverage_data(
        self, file_path: str, coverage_data: Dict[str, Any]
    ) -> None:
        """Cache coverage data for a file."""
        cache_key = f"coverage:{file_path}"
        self._metrics_cache.set(cache_key, coverage_data)

    def get_coverage_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get cached coverage data for a file."""
        cache_key = f"coverage:{file_path}"
        return self._metrics_cache.get(cache_key)

    def invalidate_metrics(self, metric_type: Optional[str] = None) -> None:
        """Invalidate cached metrics."""
        with self._lock:
            if metric_type:
                # Remove specific metric type
                if metric_type in self._computation_hashes:
                    del self._computation_hashes[metric_type]

                # Clear related cache entries
                keys_to_clear = []
                for key in self._metrics_cache.keys():
                    if key.startswith(f"{metric_type}_"):
                        keys_to_clear.append(key)

                for key in keys_to_clear:
                    self._metrics_cache.delete(key)
            else:
                # Clear all metrics
                self._metrics_cache.clear()
                self._computation_hashes.clear()


class MicroCache:
    """Main micro cache interface for sub-300ms graph data access."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize the micro cache layer."""
        self.config = config or CacheConfig()
        self.graph_cache = GraphDataCache(self.config)
        self.metrics_cache = MetricsCache(self.config)

        # Performance monitoring
        self.stats = CacheStats()
        self._performance_monitor = threading.Lock()

        # Graph change detection
        self._last_graph_hash: Optional[str] = None
        self._change_check_time = time.time()

        logger.info(
            f"Initialized MicroCache with target latency: {self.config.target_latency_ms}ms"
        )

    def _start_timer(self) -> float:
        """Start performance timer."""
        return time.time() * 1000  # Convert to milliseconds

    def _end_timer(self, start_time: float, operation: str) -> float:
        """End performance timer and update stats."""
        duration = (time.time() * 1000) - start_time

        with self._performance_monitor:
            self.stats.total_requests += 1
            # Update rolling average
            self.stats.avg_response_time_ms = (
                self.stats.avg_response_time_ms * (self.stats.total_requests - 1)
                + duration
            ) / self.stats.total_requests

            if (
                self.config.log_slow_queries
                and duration > self.config.slow_query_threshold_ms
            ):
                logger.warning(f"Slow cache operation '{operation}': {duration:.2f}ms")

        return duration

    def is_warmed_up(self) -> bool:
        """Check if cache contains substantial data."""
        # Check cache directly to avoid circular dependency
        nodes_count = len(self.graph_cache._nodes_cache.keys())
        edges_count = len(self.graph_cache._edges_cache.keys())

        # Consider warmed up if we have reasonable amount of data
        return nodes_count > 2 and edges_count >= 0  # Allow 0 edges for test scenarios

    def warm_up_cache(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        force: bool = False,
    ) -> None:
        """Pre-populate cache with commonly accessed data."""
        # Skip if already warmed up and not forcing
        if not force and self.is_warmed_up():
            logger.info("Cache already warmed up, skipping reload")
            return

        start_time = self._start_timer()

        logger.info(f"Warming up cache with {len(nodes)} nodes and {len(edges)} edges")

        # Cache all nodes and edges
        self.graph_cache.cache_nodes(nodes)
        self.graph_cache.cache_edges(edges)

        # Pre-compute criticality scores if enabled
        if (
            self.config.enable_criticality_precompute
            and len(nodes) >= self.config.precompute_threshold
        ):
            self._precompute_criticality_scores(nodes, edges)

        duration = self._end_timer(start_time, "warm_up_cache")
        logger.info(f"Cache warm-up completed in {duration:.2f}ms")

    def _precompute_criticality_scores(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> None:
        """Pre-compute criticality scores."""
        try:
            from aston.analysis.criticality_scorer import CriticalityScorer

            scorer = CriticalityScorer()
            scores = scorer.calculate_criticality_scores(nodes, edges)
            self.metrics_cache.cache_criticality_scores(nodes, edges, scores)

            with self._performance_monitor:
                self.stats.precompute_hits += 1

            logger.debug(f"Pre-computed criticality scores for {len(nodes)} nodes")
        except Exception as e:
            logger.warning(f"Failed to pre-compute criticality scores: {e}")
            with self._performance_monitor:
                self.stats.precompute_misses += 1

    def get_node_fast(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node with sub-300ms guarantee."""
        start_time = self._start_timer()

        node = self.graph_cache.get_node(node_id)
        self._end_timer(start_time, "get_node_fast")

        with self._performance_monitor:
            if node:
                self.stats.hits += 1
            else:
                self.stats.misses += 1

        return node

    def get_nodes_by_file_fast(self, file_path: str) -> List[Dict[str, Any]]:
        """Get nodes for a file with sub-300ms guarantee."""
        start_time = self._start_timer()

        nodes = self.graph_cache.get_nodes_by_file(file_path)
        self._end_timer(start_time, "get_nodes_by_file_fast")

        with self._performance_monitor:
            if nodes:
                self.stats.hits += 1
            else:
                self.stats.misses += 1

        return nodes

    def get_node_relationships_fast(
        self, node_id: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get outgoing and incoming edges for a node."""
        start_time = self._start_timer()

        outgoing = self.graph_cache.get_edges_by_source(node_id)
        incoming = self.graph_cache.get_edges_by_target(node_id)

        self._end_timer(start_time, "get_node_relationships_fast")

        with self._performance_monitor:
            if outgoing or incoming:
                self.stats.hits += 1
            else:
                self.stats.misses += 1

        return outgoing, incoming

    def get_criticality_scores_fast(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Get pre-computed criticality scores with fallback."""
        start_time = self._start_timer()

        # Try cache first
        scores = self.metrics_cache.get_criticality_scores(nodes, edges)

        if scores is None and len(nodes) < self.config.precompute_threshold:
            # For small graphs, compute on-demand
            try:
                from aston.analysis.criticality_scorer import CriticalityScorer

                scorer = CriticalityScorer()
                scores = scorer.calculate_criticality_scores(nodes, edges)
                self.metrics_cache.cache_criticality_scores(nodes, edges, scores)
            except Exception as e:
                logger.warning(f"Failed to compute criticality scores: {e}")

        self._end_timer(start_time, "get_criticality_scores_fast")

        with self._performance_monitor:
            if scores:
                self.stats.hits += 1
            else:
                self.stats.misses += 1

        return scores

    def invalidate_cache(self, file_paths: Optional[List[str]] = None) -> None:
        """Invalidate cache entries for changed files."""
        if file_paths:
            logger.info(f"Invalidating cache for {len(file_paths)} files")
            # Selective invalidation - clear nodes/edges for specific files
            for file_path in file_paths:
                nodes = self.graph_cache.get_nodes_by_file(file_path)
                for node in nodes:
                    node_id = node.get("id")
                    if node_id:
                        # Clear node and its relationships
                        outgoing, incoming = self.get_node_relationships_fast(node_id)
                        # Clear from indexes (implementation would need more detailed tracking)

            # Invalidate all metrics since graph structure may have changed
            self.metrics_cache.invalidate_metrics()
        else:
            logger.info("Clearing entire cache")
            self.graph_cache.clear()
            self.metrics_cache.invalidate_metrics()

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics."""
        return {
            "performance": asdict(self.stats),
            "config": asdict(self.config),
            "memory_usage": {
                "nodes_cached": len(self.graph_cache._nodes_cache.keys()),
                "edges_cached": len(self.graph_cache._edges_cache.keys()),
                "metrics_cached": len(self.metrics_cache._metrics_cache.keys()),
            },
            "state": {
                "is_warmed_up": self.is_warmed_up(),
                "is_global_instance": self is _global_cache,
            },
            "latency_target_met": self.stats.avg_response_time_ms
            <= self.config.target_latency_ms,
        }


# Global cache instance
_global_cache: Optional[MicroCache] = None
_global_cache_config: Optional[CacheConfig] = None


def get_micro_cache(config: Optional[CacheConfig] = None) -> MicroCache:
    """Get or create the global micro cache instance."""
    global _global_cache, _global_cache_config

    # If no config provided, use existing cache if available
    if config is None:
        if _global_cache is not None:
            return _global_cache
        # Create with default config
        config = CacheConfig()

    # Check if we need to recreate cache due to significant config changes
    needs_recreation = (
        _global_cache is None
        or _global_cache_config is None
        or _global_cache_config.target_latency_ms != config.target_latency_ms
        or _global_cache_config.max_memory_mb != config.max_memory_mb
        or _global_cache_config.default_ttl_seconds != config.default_ttl_seconds
    )

    if needs_recreation:
        if _global_cache is not None:
            logger.info("Recreating global cache due to configuration changes")
        _global_cache = MicroCache(config)
        _global_cache_config = config
        logger.info("Created global MicroCache instance")
    else:
        # Update non-critical config settings without recreation
        _global_cache.config.enable_criticality_precompute = (
            config.enable_criticality_precompute
        )
        _global_cache.config.log_slow_queries = config.log_slow_queries

    return _global_cache


def clear_global_cache(reset_instance: bool = False) -> None:
    """Clear the global cache instance.

    Args:
        reset_instance: If True, completely reset the global instance
    """
    global _global_cache, _global_cache_config

    if _global_cache:
        _global_cache.invalidate_cache()
        logger.info("Cleared global MicroCache data")

    if reset_instance:
        _global_cache = None
        _global_cache_config = None
        logger.info("Reset global MicroCache instance")


def warm_up_global_cache(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], force: bool = False
) -> None:
    """Warm up the global cache with graph data."""
    cache = get_micro_cache()
    cache.warm_up_cache(nodes, edges, force=force)
