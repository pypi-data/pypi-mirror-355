"""
DO NOT USE THIS MODULE. FIND IN @storage/cache/
DEPRECATED.
"""

"""
Storage adapters for GraphCache.

This module provides pluggable storage backends for the graph cache system,
starting with a pickle+lz4 implementation but designed to support other
backends like mmap or SQLite in the future.
"""

import time
import pickle
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

from aston.core.logging import get_logger

logger = get_logger(__name__)

try:
    import lz4.frame

    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False
    logger.warning("lz4 not available, falling back to gzip compression")
    import gzip


class CacheStorageAdapter(ABC):
    """Abstract base class for cache storage adapters."""

    @abstractmethod
    def save(self, cache_file: Path, data: Dict[str, Any]) -> bool:
        """Save cache data to storage.

        Args:
            cache_file: Path to cache file
            data: Cache data to save

        Returns:
            True if save was successful
        """
        pass

    @abstractmethod
    def load(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Load cache data from storage.

        Args:
            cache_file: Path to cache file

        Returns:
            Cache data if successful, None if failed
        """
        pass

    @abstractmethod
    def exists(self, cache_file: Path) -> bool:
        """Check if cache file exists.

        Args:
            cache_file: Path to cache file

        Returns:
            True if cache file exists
        """
        pass

    @abstractmethod
    def get_metadata(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Get cache file metadata.

        Args:
            cache_file: Path to cache file

        Returns:
            Metadata dict with 'size', 'mtime', etc.
        """
        pass


class PickleLZ4Adapter(CacheStorageAdapter):
    """Storage adapter using pickle + lz4 compression."""

    def __init__(self, compression_level: int = 4):
        """Initialize the adapter.

        Args:
            compression_level: LZ4 compression level (1-12, higher = more compression)
        """
        self.compression_level = compression_level
        self.use_lz4 = HAS_LZ4

        if not self.use_lz4:
            logger.warning("Using gzip compression instead of lz4")

    def save(self, cache_file: Path, data: Dict[str, Any]) -> bool:
        """Save cache data using pickle + compression.

        Args:
            cache_file: Path to cache file
            data: Cache data to save

        Returns:
            True if save was successful
        """
        try:
            start_time = time.time()

            # Ensure parent directory exists
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Pickle the data
            pickled_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

            # Compress the data
            if self.use_lz4:
                compressed_data = lz4.frame.compress(
                    pickled_data, compression_level=self.compression_level
                )
            else:
                compressed_data = gzip.compress(pickled_data, compresslevel=6)

            # Write to file
            with open(cache_file, "wb") as f:
                f.write(compressed_data)

            # Log performance metrics
            duration = time.time() - start_time
            original_size = len(pickled_data)
            compressed_size = len(compressed_data)
            compression_ratio = (
                original_size / compressed_size if compressed_size > 0 else 0
            )

            logger.debug(f"Cache saved: {cache_file}")
            logger.debug(
                f"Size: {original_size:,} → {compressed_size:,} bytes "
                f"({compression_ratio:.1f}x compression) in {duration:.3f}s"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save cache to {cache_file}: {e}")
            return False

    def load(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Load cache data using pickle + decompression.

        Args:
            cache_file: Path to cache file

        Returns:
            Cache data if successful, None if failed
        """
        try:
            start_time = time.time()

            if not cache_file.exists():
                return None

            # Read compressed data
            with open(cache_file, "rb") as f:
                compressed_data = f.read()

            # Decompress the data
            if self.use_lz4:
                pickled_data = lz4.frame.decompress(compressed_data)
            else:
                pickled_data = gzip.decompress(compressed_data)

            # Unpickle the data
            data = pickle.loads(pickled_data)

            # Log performance metrics
            duration = time.time() - start_time
            logger.debug(f"Cache loaded: {cache_file} in {duration:.3f}s")

            return data

        except Exception as e:
            logger.error(f"Failed to load cache from {cache_file}: {e}")
            return None

    def exists(self, cache_file: Path) -> bool:
        """Check if cache file exists.

        Args:
            cache_file: Path to cache file

        Returns:
            True if cache file exists
        """
        return cache_file.exists()

    def get_metadata(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Get cache file metadata.

        Args:
            cache_file: Path to cache file

        Returns:
            Metadata dict with size, mtime, etc.
        """
        try:
            if not cache_file.exists():
                return None

            stat = cache_file.stat()
            return {
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "created": stat.st_ctime
                if hasattr(stat, "st_ctime")
                else stat.st_mtime,
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for {cache_file}: {e}")
            return None


def compute_data_hash(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """Compute a hash of the graph data for cache invalidation.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        SHA256 hash of the data
    """
    try:
        # Create a deterministic representation
        node_repr = sorted(
            [
                f"{n.get('id', '')}:{n.get('name', '')}:{n.get('file_path', '')}"
                for n in nodes
            ]
        )
        edge_repr = sorted(
            [
                f"{e.get('source', '')}:{e.get('target', '')}:{e.get('type', '')}"
                for e in edges
            ]
        )

        # Combine and hash
        combined = "\n".join(node_repr + edge_repr)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]

    except Exception as e:
        logger.warning(f"Failed to compute data hash: {e}")
        return "unknown"
