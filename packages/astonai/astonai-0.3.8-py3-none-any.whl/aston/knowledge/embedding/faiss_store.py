"""
FAISS vector store implementation for efficient vector similarity search.

This module provides a FAISS-based implementation of the VectorStoreInterface
for high-performance local vector storage and retrieval.
"""

import uuid
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from aston.knowledge.embedding.vector_store import (
    VectorStoreInterface,
    EmbeddingVector,
    EmbeddingMetadata,
    SearchResult,
)
from aston.knowledge.errors import VectorOperationError, VectorInvalidDimensionError
from aston.core.path_resolution import PathResolver
from aston.core.logging import get_logger

logger = get_logger(__name__)

# Lazy import to avoid immediate dependency requirement
_faiss = None


def _load_faiss():
    """Lazy-load faiss module."""
    global _faiss

    if _faiss is None:
        try:
            import faiss

            _faiss = faiss
            logger.info("Loaded FAISS module")
        except ImportError:
            raise ImportError(
                "faiss-cpu is required for FAISS vector store. "
                "Install with: pip install faiss-cpu"
            )

    return _faiss


class FaissVectorStore(VectorStoreInterface):
    """
    FAISS-based implementation of the VectorStoreInterface.

    This implementation uses FAISS for efficient vector similarity search
    and stores metadata in memory with persistence to disk.
    """

    def __init__(
        self,
        index_path: Optional[str] = None,
        dimension: int = 384,
        backend: str = "minilm",
    ):
        """
        Initialize a FAISS vector store.

        Args:
            index_path: Path to the index file. If None, uses the default path.
            dimension: Dimension of the vectors to store
            backend: Backend name used for default path generation (minilm, openai)
        """
        # Lazy load FAISS
        self._faiss = _load_faiss()

        self._dimension = dimension
        self._backend = backend

        # Determine index path
        if index_path is None:
            # Use default path in .aston/vectors/{backend}/index.faiss
            index_dir = PathResolver.repo_root() / ".aston" / "vectors" / backend
            index_dir.mkdir(parents=True, exist_ok=True)
            self._index_path = index_dir / "index.faiss"

            # Also determine metadata path
            self._metadata_path = index_dir / "metadata.json"
        else:
            self._index_path = Path(index_path)
            self._metadata_path = Path(index_path).with_suffix(".metadata.json")

        # Initialize index
        self._index = None
        self._metadata: Dict[str, EmbeddingMetadata] = {}
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: Dict[int, str] = {}
        self._initialized = False
        self._vector_count = 0

        # Statistics
        self._init_time = None
        self._last_operation = None

    def _ensure_initialized(self, for_write: bool = False) -> None:
        """
        Ensure the index is initialized.

        Args:
            for_write: Whether initialization is for a write operation
        """
        if not self._initialized:
            self._initialize_index(for_write)

    def _initialize_index(self, for_write: bool = False) -> None:
        """
        Initialize the FAISS index.

        Args:
            for_write: Whether initialization is for a write operation
        """
        start_time = time.time()

        # Check if index exists
        if self._index_path.exists() and self._metadata_path.exists():
            # Load existing index
            logger.info(f"Loading existing FAISS index from {self._index_path}")
            self._index = self._faiss.read_index(str(self._index_path))

            # Load metadata
            with open(self._metadata_path, "r") as f:
                metadata_data = json.load(f)

                # Reconstruct metadata objects
                self._metadata = {}
                for vector_id, meta_dict in metadata_data.get("metadata", {}).items():
                    self._metadata[vector_id] = EmbeddingMetadata(**meta_dict)

                # Load ID mappings
                self._id_to_index = metadata_data.get("id_to_index", {})
                # Convert string keys to integers for index_to_id
                self._index_to_id = {
                    int(k): v for k, v in metadata_data.get("index_to_id", {}).items()
                }

            # Update vector count
            self._vector_count = self._index.ntotal

        else:
            if not for_write:
                logger.warning(
                    f"FAISS index not found at {self._index_path}. Creating empty index."
                )

            # Create new index
            self._index = self._faiss.IndexFlatIP(self._dimension)
            self._metadata = {}
            self._id_to_index = {}
            self._index_to_id = {}
            self._vector_count = 0

            # Save empty index and metadata
            if for_write:
                self._save_index()

        self._initialized = True
        self._init_time = time.time() - start_time
        logger.info(
            f"FAISS index initialized in {self._init_time:.2f}s with {self._vector_count} vectors"
        )

    def _save_index(self) -> None:
        """Save the index and metadata to disk."""
        if not self._initialized:
            return

        # Create parent directory if it doesn't exist
        self._index_path.parent.mkdir(parents=True, exist_ok=True)

        # Save index
        self._faiss.write_index(self._index, str(self._index_path))

        # Save metadata
        metadata_data = {
            "metadata": {k: asdict(v) for k, v in self._metadata.items()},
            "id_to_index": self._id_to_index,
            "index_to_id": self._index_to_id,
        }

        with open(self._metadata_path, "w") as f:
            json.dump(metadata_data, f)

        logger.info(
            f"Saved FAISS index with {self._vector_count} vectors to {self._index_path}"
        )

    def _validate_vector(self, vector: EmbeddingVector) -> np.ndarray:
        """
        Validate and normalize a vector.

        Args:
            vector: The vector to validate

        Returns:
            A numpy array of the normalized vector

        Raises:
            VectorInvalidDimensionError: If the vector has an invalid dimension
        """
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float32)

        if vector.shape != (self._dimension,):
            raise VectorInvalidDimensionError(
                f"Vector dimension {vector.shape} does not match expected dimension ({self._dimension},)"
            )

        # Normalize the vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    async def store_vector(
        self,
        vector: EmbeddingVector,
        metadata: EmbeddingMetadata,
        vector_id: Optional[str] = None,
    ) -> str:
        """
        Store a single vector with its metadata.

        Args:
            vector: The embedding vector to store
            metadata: Metadata associated with the vector
            vector_id: Optional ID for the vector

        Returns:
            The ID of the stored vector
        """
        if vector_id is None:
            vector_id = str(uuid.uuid4())

        # Ensure index is initialized for writing
        self._ensure_initialized(for_write=True)

        try:
            # Validate vector
            vector_np = self._validate_vector(vector)

            # Add vector to index
            self._index.add(np.array([vector_np]))

            # Store metadata
            self._metadata[vector_id] = metadata

            # Update mappings
            index = self._vector_count
            self._id_to_index[vector_id] = index
            self._index_to_id[index] = vector_id

            # Update vector count
            self._vector_count += 1

            # Save index and metadata
            self._save_index()

            self._last_operation = time.time()
            return vector_id

        except Exception as e:
            raise VectorOperationError(f"Failed to store vector: {e}")

    async def batch_store_vectors(
        self,
        vectors: List[EmbeddingVector],
        metadata_list: List[EmbeddingMetadata],
        vector_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Store multiple vectors with their metadata in a batch operation.

        Args:
            vectors: List of embedding vectors to store
            metadata_list: List of metadata objects associated with the vectors
            vector_ids: Optional list of IDs for the vectors

        Returns:
            List of IDs for the stored vectors
        """
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors and metadata objects must match")

        if vector_ids is not None and len(vector_ids) != len(vectors):
            raise ValueError("Number of vector IDs must match number of vectors")

        # Generate IDs if not provided
        if vector_ids is None:
            vector_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

        # Ensure index is initialized for writing
        self._ensure_initialized(for_write=True)

        try:
            # Validate and normalize vectors
            vectors_np = np.array(
                [self._validate_vector(v) for v in vectors], dtype=np.float32
            )

            # Add vectors to index
            self._index.add(vectors_np)

            # Store metadata and update mappings
            for i, (vector_id, metadata) in enumerate(zip(vector_ids, metadata_list)):
                index = self._vector_count + i
                self._metadata[vector_id] = metadata
                self._id_to_index[vector_id] = index
                self._index_to_id[index] = vector_id

            # Update vector count
            self._vector_count += len(vectors)

            # Save index and metadata
            self._save_index()

            self._last_operation = time.time()
            return vector_ids

        except Exception as e:
            raise VectorOperationError(f"Failed to batch store vectors: {e}")

    async def get_vector(
        self, vector_id: str
    ) -> Tuple[Optional[EmbeddingVector], Optional[EmbeddingMetadata]]:
        """
        Retrieve a vector and its metadata by ID.

        Args:
            vector_id: The ID of the vector to retrieve

        Returns:
            A tuple of (vector, metadata) if found, or (None, None) if not found
        """
        self._ensure_initialized()

        if vector_id not in self._id_to_index:
            return None, None

        try:
            # Get vector index
            index = self._id_to_index[vector_id]

            # Reconstruct vector from index
            vector = self._index.reconstruct(index)

            # Get metadata
            metadata = self._metadata.get(vector_id)

            self._last_operation = time.time()
            return vector, metadata

        except Exception as e:
            raise VectorOperationError(f"Failed to retrieve vector: {e}")

    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector and its metadata by ID.

        Note: FAISS does not support efficient vector deletion.
        This implementation marks the vector as deleted in metadata
        but keeps it in the index. The vector will be removed on
        the next rebuild of the index.

        Args:
            vector_id: The ID of the vector to delete

        Returns:
            True if the vector was marked as deleted, False if it wasn't found
        """
        self._ensure_initialized()

        if vector_id not in self._id_to_index:
            return False

        try:
            # Remove metadata and mappings
            index = self._id_to_index.pop(vector_id)
            self._index_to_id.pop(index)
            self._metadata.pop(vector_id)

            # Save metadata
            self._save_index()

            self._last_operation = time.time()
            return True

        except Exception as e:
            raise VectorOperationError(f"Failed to delete vector: {e}")

    async def search_vectors(
        self,
        query_vector: EmbeddingVector,
        limit: int = 10,
        score_threshold: float = 0.0,
        filter_metadata: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_vector: The query vector to search for
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            filter_metadata: Optional metadata filter criteria

        Returns:
            List of SearchResult objects ordered by similarity (highest first)
        """
        self._ensure_initialized()

        if self._vector_count == 0:
            return []

        try:
            # Validate query vector
            query_np = self._validate_vector(query_vector)

            # Search for similar vectors
            D, I = self._index.search(
                np.array([query_np]), min(limit * 10, self._vector_count)
            )

            # D is distances, I is indices
            distances = D[0]
            indices = I[0]

            results = []
            for distance, idx in zip(distances, indices):
                # Get vector ID from index
                vector_id = self._index_to_id.get(int(idx))

                if vector_id is None:
                    continue

                # Get metadata
                metadata = self._metadata.get(vector_id)

                if metadata is None:
                    continue

                # Apply metadata filter if provided
                if filter_metadata and not self._matches_filter(
                    metadata, filter_metadata
                ):
                    continue

                # Apply score threshold
                if distance < score_threshold:
                    continue

                # Add to results
                results.append(
                    SearchResult(id=vector_id, score=float(distance), metadata=metadata)
                )

                # Stop if we have enough results
                if len(results) >= limit:
                    break

            self._last_operation = time.time()
            return results

        except Exception as e:
            raise VectorOperationError(f"Failed to search vectors: {e}")

    def _matches_filter(
        self, metadata: EmbeddingMetadata, filter_criteria: Dict
    ) -> bool:
        """
        Check if metadata matches filter criteria.

        Args:
            metadata: The metadata to check
            filter_criteria: The filter criteria

        Returns:
            True if the metadata matches the filter, False otherwise
        """
        for key, value in filter_criteria.items():
            if key == "additional":
                # Check additional metadata
                for additional_key, additional_value in value.items():
                    if additional_key not in metadata.additional:
                        return False
                    if metadata.additional[additional_key] != additional_value:
                        return False
            else:
                # Check direct metadata field
                if not hasattr(metadata, key):
                    return False
                if getattr(metadata, key) != value:
                    return False

        return True

    async def count_vectors(self, filter_metadata: Optional[Dict] = None) -> int:
        """
        Count the number of vectors in the store, optionally filtered by metadata.

        Args:
            filter_metadata: Optional metadata filter criteria

        Returns:
            The count of vectors matching the filter (or total count if no filter)
        """
        self._ensure_initialized()

        if filter_metadata is None:
            return self._vector_count

        # Count vectors matching filter
        count = 0
        for vector_id, metadata in self._metadata.items():
            if self._matches_filter(metadata, filter_metadata):
                count += 1

        return count

    async def clear(self) -> None:
        """
        Clear all vectors and metadata from the store.
        """
        self._ensure_initialized(for_write=True)

        try:
            # Create new empty index
            self._index = self._faiss.IndexFlatIP(self._dimension)
            self._metadata = {}
            self._id_to_index = {}
            self._index_to_id = {}
            self._vector_count = 0

            # Save empty index and metadata
            self._save_index()

            self._last_operation = time.time()

        except Exception as e:
            raise VectorOperationError(f"Failed to clear vector store: {e}")

    async def close(self) -> None:
        """
        Close any open connections or resources.
        """
        if self._initialized:
            # Save index and metadata
            self._save_index()

            # Reset state
            self._index = None
            self._initialized = False

            logger.info("Closed FAISS vector store")


# Helper function to convert dataclass to dict
def asdict(obj):
    """Convert a dataclass instance to a dictionary."""
    if hasattr(obj, "__dataclass_fields__"):
        # It's a dataclass
        return {k: asdict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        # It's a dictionary
        return {k: asdict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # It's a list
        return [asdict(v) for v in obj]
    else:
        # It's a primitive type
        return obj
