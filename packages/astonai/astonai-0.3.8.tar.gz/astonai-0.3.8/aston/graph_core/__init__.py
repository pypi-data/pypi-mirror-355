"""
DO NOT USE THIS MODULE. FIND IN @storage/cache/
DEPRECATED.
"""

"""
Graph Core module for TestIndex.

This module provides core graph utilities including caching, storage adapters,
and graph management primitives for high-performance graph operations.
"""

from aston.graph_core.cache import GraphCache
from aston.graph_core.storage import CacheStorageAdapter, PickleLZ4Adapter

__all__ = ["GraphCache", "CacheStorageAdapter", "PickleLZ4Adapter"]
