"""
Storage utilities for the Test Intelligence Engine.

This package provides utilities for caching and persistent storage.
"""

__version__ = "0.1.0"

# Re-export key classes for easier imports
from aston.storage.cache import MemoryCache
from aston.storage.cache.micro_cache import MicroCache, CacheConfig, get_micro_cache
from aston.storage.cache.graph_loader import GraphDataLoader, load_and_warm_cache
from aston.storage.persistence import FileStorage
