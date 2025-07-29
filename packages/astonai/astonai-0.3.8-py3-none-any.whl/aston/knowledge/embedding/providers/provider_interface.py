"""
Interface for embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np


class EmbeddingProviderInterface(ABC):
    """Abstract interface for embedding providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the provider."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get the dimension of the embeddings produced by this provider."""
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate an embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            A numpy array of the embedding
        """
        pass

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: The texts to embed

        Returns:
            A list of numpy arrays of the embeddings
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get the configuration of this provider.

        Returns:
            A dictionary with the provider configuration
        """
        pass
