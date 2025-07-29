"""
Factory for creating embedding providers.

This module provides a factory function for creating embedding providers
based on configuration and availability.
"""

from typing import Dict, Any, Optional, Literal

from aston.knowledge.embedding.providers.provider_interface import (
    EmbeddingProviderInterface,
)
from aston.core.logging import get_logger

logger = get_logger(__name__)

# Type for backend names
BackendType = Literal["minilm", "openai", "auto"]


def get_provider(
    backend: BackendType = "auto", config: Optional[Dict[str, Any]] = None
) -> EmbeddingProviderInterface:
    """
    Get an embedding provider based on the specified backend and configuration.

    Args:
        backend: The backend to use (minilm, openai, auto)
        config: Optional configuration for the provider

    Returns:
        An instance of EmbeddingProviderInterface

    Raises:
        ImportError: If the required dependencies are not installed
        ValueError: If the backend is unknown
    """
    if config is None:
        config = {}

    if backend == "minilm":
        return _get_minilm_provider(config)
    elif backend == "openai":
        return _get_openai_provider(config)
    elif backend == "auto":
        # Try minilm first, fall back to openai if not available
        try:
            return _get_minilm_provider(config)
        except ImportError:
            # Fall back to OpenAI if MiniLM is not available
            try:
                return _get_openai_provider(config)
            except Exception as e:
                raise ImportError(
                    "Neither MiniLM nor OpenAI backend is available. "
                    "Please install sentence-transformers for MiniLM or set OPENAI_API_KEY for OpenAI."
                ) from e
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _get_minilm_provider(config: Dict[str, Any]) -> EmbeddingProviderInterface:
    """
    Create a MiniLM provider with the given configuration.

    Args:
        config: Configuration for the provider

    Returns:
        An instance of MiniLMProvider

    Raises:
        ImportError: If sentence-transformers is not installed
    """
    from aston.knowledge.embedding.providers.minilm_provider import MiniLMProvider

    model_name = config.get("model_name", "all-MiniLM-L6-v2")
    use_cuda = config.get("use_cuda", None)

    return MiniLMProvider(model_name=model_name, use_cuda=use_cuda)


def _get_openai_provider(config: Dict[str, Any]) -> EmbeddingProviderInterface:
    """
    Create an OpenAI provider with the given configuration.

    Args:
        config: Configuration for the provider

    Returns:
        An instance of OpenAIProvider

    Raises:
        ValueError: If OpenAI API key is not available
        ImportError: If aiohttp is not installed
    """
    from aston.knowledge.embedding.providers.openai_provider import OpenAIProvider

    # Extract configuration with defaults
    api_key = config.get("api_key") or config.get("openai_api_key")
    model_name = config.get("model_name", "text-embedding-3-small")
    api_base = config.get("api_base", "https://api.openai.com/v1")
    rate_limit_requests = config.get("rate_limit_requests", 50)
    rate_limit_tokens = config.get("rate_limit_tokens", 150000)
    max_retries = config.get("max_retries", 3)
    retry_delay = config.get("retry_delay", 1.0)
    max_tokens_per_request = config.get("max_tokens_per_request", 8191)

    return OpenAIProvider(
        api_key=api_key,
        model_name=model_name,
        api_base=api_base,
        rate_limit_requests=rate_limit_requests,
        rate_limit_tokens=rate_limit_tokens,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_tokens_per_request=max_tokens_per_request,
    )
