"""
Embedding functionality for code chunks.

This package provides utilities for generating vector embeddings from code chunks,
as well as storing and searching for similar code snippets.

New Provider-Based Architecture:
- Use providers/ for different embedding backends (MiniLM, OpenAI)
- Use faiss_store.py for high-performance vector storage
- Use CLI: `aston embed --backend {minilm|openai|auto}`
"""

from aston.knowledge.embedding.vector_store import VectorStoreInterface, SearchResult
from aston.knowledge.embedding.providers.provider_factory import (
    get_provider,
    BackendType,
)
