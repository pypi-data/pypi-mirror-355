"""
Minimal command integration for micro cache core functionality.

This module provides basic decorators and context managers for cache integration.
Advanced features (auto-enhancement, monkey-patching) are deferred to cache-extras.
"""

import time
from functools import wraps
from typing import Dict, Any, Optional

from aston.core.logging import get_logger
from aston.storage.cache.micro_cache import get_micro_cache, CacheConfig
from aston.storage.cache.graph_loader import load_and_warm_cache

logger = get_logger(__name__)


def with_micro_cache(warm_up: bool = False, config: Optional[CacheConfig] = None):
    """Decorator to add micro cache to command functions.

    Args:
        warm_up: Whether to warm up cache before command execution
        config: Optional cache configuration
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance
            cache = get_micro_cache(config)

            # Warm up if requested
            if warm_up and not cache.is_warmed_up():
                try:
                    # Load default config for warming
                    warm_config = {"offline_mode": True}
                    load_and_warm_cache(warm_config, config)
                except Exception as e:
                    logger.warning(f"Failed to warm cache: {e}")

            # Add cache to kwargs
            kwargs["_micro_cache"] = cache

            # Execute function
            return func(*args, **kwargs)

        return wrapper

    return decorator


class CacheEnhancedExecution:
    """Context manager for cache-enhanced command execution."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        cache_config: Optional[CacheConfig] = None,
    ):
        """Initialize cache enhanced execution context.

        Args:
            config: Data source configuration
            cache_config: Cache configuration
        """
        self.config = config or {"offline_mode": True}
        self.cache_config = cache_config
        self.cache = None
        self.start_time = None

    def __enter__(self):
        """Enter the context and set up cache."""
        self.start_time = time.time()
        self.cache = get_micro_cache(self.cache_config)

        # Warm up cache if not already warmed
        if not self.cache.is_warmed_up():
            try:
                load_and_warm_cache(self.config, self.cache_config)
            except Exception as e:
                logger.warning(f"Failed to warm cache on context entry: {e}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and optionally report performance."""
        if self.start_time:
            duration = time.time() - self.start_time
            stats = self.cache.get_cache_statistics() if self.cache else {}
            perf = stats.get("performance", {})

            logger.info(f"Cache-enhanced execution completed in {duration:.2f}s")
            logger.info(f"Cache hit ratio: {perf.get('hit_ratio', 0):.1%}")

    def get_cache(self):
        """Get the cache instance."""
        return self.cache


class CachedAnalysisHelper:
    """Helper class for common cached analysis operations."""

    def __init__(self, cache_config: Optional[CacheConfig] = None):
        """Initialize with cache configuration."""
        self.cache = get_micro_cache(cache_config)

    def get_nodes_fast(self, file_paths: Optional[list] = None) -> list:
        """Get nodes quickly from cache."""
        if not file_paths:
            return []

        all_nodes = []
        for file_path in file_paths:
            nodes = self.cache.get_nodes_by_file_fast(file_path)
            all_nodes.extend(nodes)

        return all_nodes

    def get_edges_fast(self, node_ids: Optional[list] = None) -> list:
        """Get edges quickly from cache."""
        if not node_ids:
            return []

        all_edges = []
        for node_id in node_ids:
            outgoing, incoming = self.cache.get_node_relationships_fast(node_id)
            all_edges.extend(outgoing)
            all_edges.extend(incoming)

        # Remove duplicates
        seen = set()
        unique_edges = []
        for edge in all_edges:
            edge_id = edge.get("id")
            if edge_id and edge_id not in seen:
                seen.add(edge_id)
                unique_edges.append(edge)

        return unique_edges

    def get_criticality_scores_fast(
        self, nodes: list, edges: list
    ) -> Optional[Dict[str, float]]:
        """Get criticality scores quickly from cache."""
        return self.cache.get_criticality_scores_fast(nodes, edges)
