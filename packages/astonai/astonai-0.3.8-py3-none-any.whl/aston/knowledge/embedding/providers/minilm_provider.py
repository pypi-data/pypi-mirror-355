"""
MiniLM embedding provider for local, CPU-based embeddings.

This module implements a provider for the MiniLM model from sentence-transformers,
enabling fast local embedding generation without API costs.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
import numpy as np

from aston.knowledge.embedding.providers.provider_interface import (
    EmbeddingProviderInterface,
)
from aston.core.path_resolution import PathResolver
from aston.core.logging import get_logger

logger = get_logger(__name__)

# Lazy import to avoid immediate dependency requirement
_sentence_transformers = None
_is_cuda_available = None


def _load_sentence_transformers():
    """Lazy-load sentence_transformers module."""
    global _sentence_transformers, _is_cuda_available

    if _sentence_transformers is None:
        try:
            import sentence_transformers
            import torch

            _sentence_transformers = sentence_transformers
            _is_cuda_available = torch.cuda.is_available()
            logger.info(
                f"Loaded sentence_transformers. CUDA available: {_is_cuda_available}"
            )
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for MiniLM embeddings. "
                "Install with: pip install sentence-transformers>=2.0.0"
            )

    return _sentence_transformers


class MiniLMProvider(EmbeddingProviderInterface):
    """Local MiniLM provider for generating embeddings using sentence-transformers."""

    def __init__(
        self, model_name: str = "all-MiniLM-L6-v2", use_cuda: Optional[bool] = None
    ):
        """Initialize the MiniLM provider.

        Args:
            model_name: The name of the MiniLM model to use
            use_cuda: Whether to use CUDA for inference. If None, auto-detect.
        """
        self._model_name = model_name
        self._dimension = 384  # all-MiniLM-L6-v2 dimension is 384
        self._model = None
        self._batch_size = 32
        self._max_seq_length = 256  # Limit tokens for performance
        self._use_cuda = use_cuda
        self._load_time = None
        self._initialized = False

    @property
    def name(self) -> str:
        """Get the name of the provider."""
        return f"minilm-{self._model_name}"

    @property
    def dimension(self) -> int:
        """Get the dimension of the embeddings produced by this provider."""
        return self._dimension

    def _ensure_initialized(self):
        """Ensure the model is loaded."""
        if not self._initialized:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize the model."""
        logger.info(f"Loading MiniLM model: {self._model_name}")
        start_time = time.time()

        sentence_transformers = _load_sentence_transformers()

        # Auto-detect CUDA if not explicitly set
        if self._use_cuda is None:
            self._use_cuda = _is_cuda_available

        # Create model directory if it doesn't exist
        cache_dir = PathResolver.repo_root() / ".aston" / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the model
        device = "cuda" if self._use_cuda else "cpu"
        self._model = sentence_transformers.SentenceTransformer(
            self._model_name, device=device, cache_folder=str(cache_dir)
        )

        # Configure for faster inference
        self._model.max_seq_length = self._max_seq_length

        self._load_time = time.time() - start_time
        self._initialized = True

        logger.info(f"MiniLM model loaded in {self._load_time:.2f}s. Device: {device}")

    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate an embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            A numpy array of the embedding
        """
        self._ensure_initialized()

        # Run in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self._model.encode(text, normalize_embeddings=True)
        )

        # Ensure we always get a 1D array
        if isinstance(embedding, np.ndarray):
            if embedding.ndim == 2 and embedding.shape[0] == 1:
                # Convert (1, D) to (D,)
                embedding = embedding[0]
            elif embedding.ndim != 1:
                # Flatten any unexpected shapes
                embedding = embedding.flatten()
        else:
            embedding = np.array(embedding).flatten()

        return embedding

    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: The texts to embed

        Returns:
            A list of numpy arrays of the embeddings
        """
        self._ensure_initialized()

        # Process in batches for memory efficiency
        results = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]

            # Run in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            batch_embeddings = await loop.run_in_executor(
                None, lambda: self._model.encode(batch, normalize_embeddings=True)
            )

            # Ensure we always get 1D arrays for individual embeddings
            if isinstance(batch_embeddings, np.ndarray):
                if batch_embeddings.ndim == 1:
                    # Single embedding case
                    results.append(batch_embeddings)
                elif batch_embeddings.ndim == 2:
                    # Batch embeddings case - convert each row to 1D
                    for j in range(batch_embeddings.shape[0]):
                        results.append(batch_embeddings[j])
                else:
                    raise ValueError(
                        f"Unexpected embedding shape: {batch_embeddings.shape}"
                    )
            else:
                # Handle list of embeddings
                for emb in batch_embeddings:
                    if isinstance(emb, np.ndarray) and emb.ndim == 1:
                        results.append(emb)
                    else:
                        results.append(np.array(emb).flatten())

        return results

    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration of this provider.

        Returns:
            A dictionary with the provider configuration
        """
        return {
            "provider": "minilm",
            "model_name": self._model_name,
            "dimension": self._dimension,
            "use_cuda": self._use_cuda,
            "batch_size": self._batch_size,
            "max_seq_length": self._max_seq_length,
            "load_time_seconds": self._load_time,
        }
