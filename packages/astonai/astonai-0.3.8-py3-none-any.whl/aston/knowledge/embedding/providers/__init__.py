"""
Embedding providers for AstonAI.

This package provides various implementations of embedding providers
that can be used with the EmbeddingService.
"""

from aston.knowledge.embedding.providers.provider_factory import get_provider
from aston.knowledge.embedding.providers.provider_interface import (
    EmbeddingProviderInterface,
)
from aston.knowledge.embedding.providers.minilm_provider import MiniLMProvider
from aston.knowledge.embedding.providers.openai_provider import OpenAIProvider

__all__ = [
    "get_provider",
    "EmbeddingProviderInterface",
    "MiniLMProvider",
    "OpenAIProvider",
]
