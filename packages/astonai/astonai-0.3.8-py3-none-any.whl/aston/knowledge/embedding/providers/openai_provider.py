"""
OpenAI embedding provider for the new provider architecture.

This module provides an OpenAI-based embedding provider that implements
the EmbeddingProviderInterface for use with the new embedding system.
"""

import os
import time
import asyncio
from typing import List, Dict, Any
import numpy as np
import aiohttp

from aston.knowledge.embedding.providers.provider_interface import (
    EmbeddingProviderInterface,
)
from aston.knowledge.errors import (
    EmbeddingGenerationError,
    EmbeddingModelError,
    EmbeddingRateLimitError,
    EmbeddingTokenLimitError,
)
from aston.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(EmbeddingProviderInterface):
    """OpenAI embedding provider implementation."""

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "text-embedding-3-small",
        api_base: str = "https://api.openai.com/v1",
        rate_limit_requests: int = 50,
        rate_limit_tokens: int = 150000,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_tokens_per_request: int = 8191,
        **kwargs,
    ):
        """Initialize the OpenAI embedding provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model_name: Embedding model to use
            api_base: API base URL
            rate_limit_requests: Max requests per minute
            rate_limit_tokens: Max tokens per minute
            max_retries: Max retry attempts
            retry_delay: Base retry delay in seconds
            max_tokens_per_request: Max tokens per request
            **kwargs: Additional configuration options
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model_name = model_name
        self.api_base = api_base
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_tokens = rate_limit_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_tokens_per_request = max_tokens_per_request

        # Rate limiting state
        self._request_timestamps = []
        self._token_counts = []

        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    @property
    def name(self) -> str:
        """Get the name of the provider."""
        return "openai"

    @property
    def dimension(self) -> int:
        """Get the dimension of the embeddings produced by this provider."""
        # Dimensions for different OpenAI models
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dimensions.get(self.model_name, 1536)

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate an embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            A numpy array of the embedding

        Raises:
            EmbeddingGenerationError: If embedding generation fails
            EmbeddingRateLimitError: If rate limits are exceeded
            EmbeddingTokenLimitError: If text exceeds token limits
            EmbeddingModelError: If there's an issue with the model
        """
        # Check if text exceeds token limit
        if (
            len(text) > self.max_tokens_per_request * 4
        ):  # Approximation: 4 chars per token
            raise EmbeddingTokenLimitError(
                f"Text exceeds maximum token limit of {self.max_tokens_per_request}"
            )

        # Apply rate limiting
        await self._apply_rate_limiting(1, len(text) // 4)

        # Prepare request
        url = f"{self.api_base}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {"input": text, "model": self.model_name, "encoding_format": "float"}

        # Execute request with retries
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, headers=headers, json=data
                    ) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", "60"))
                            logger.warning(
                                f"Rate limit exceeded. Retry after {retry_after}s"
                            )
                            raise EmbeddingRateLimitError(
                                f"OpenAI API rate limit exceeded. Retry after {retry_after}s"
                            )

                        response_data = await response.json()

                        if response.status != 200:
                            error_msg = response_data.get("error", {}).get(
                                "message", "Unknown error"
                            )
                            logger.error(f"OpenAI API error: {error_msg}")

                            if (
                                "token" in error_msg.lower()
                                and "limit" in error_msg.lower()
                            ):
                                raise EmbeddingTokenLimitError(error_msg)
                            elif (
                                "rate" in error_msg.lower()
                                and "limit" in error_msg.lower()
                            ):
                                raise EmbeddingRateLimitError(error_msg)
                            elif "model" in error_msg.lower():
                                raise EmbeddingModelError(error_msg)
                            else:
                                raise EmbeddingGenerationError(
                                    f"OpenAI API error: {error_msg}"
                                )

                        # Extract embedding and token count
                        embedding_data = response_data["data"][0]
                        embedding_vector = embedding_data["embedding"]
                        token_count = response_data["usage"]["prompt_tokens"]

                        # Update rate limiting state
                        self._update_rate_limiting(token_count)

                        return np.array(embedding_vector, dtype=np.float32)

            except (
                EmbeddingRateLimitError,
                EmbeddingModelError,
                EmbeddingTokenLimitError,
            ):
                # Don't retry these exceptions
                raise
            except Exception as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Embedding generation attempt {attempt+1} failed: {str(e)}. Retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All embedding generation attempts failed: {str(e)}")
                    raise EmbeddingGenerationError(
                        f"Failed to generate embedding after {self.max_retries} attempts: {str(e)}"
                    )

    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: The texts to embed

        Returns:
            A list of numpy arrays of the embeddings

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        # Check total token count (approximate)
        total_tokens = sum(len(text) // 4 for text in texts)

        # Apply rate limiting
        await self._apply_rate_limiting(len(texts), total_tokens)

        # Prepare request
        url = f"{self.api_base}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {"input": texts, "model": self.model_name, "encoding_format": "float"}

        # Execute request with retries
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, headers=headers, json=data
                    ) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", "60"))
                            logger.warning(
                                f"Rate limit exceeded. Retry after {retry_after}s"
                            )
                            raise EmbeddingRateLimitError(
                                f"OpenAI API rate limit exceeded. Retry after {retry_after}s"
                            )

                        response_data = await response.json()

                        if response.status != 200:
                            error_msg = response_data.get("error", {}).get(
                                "message", "Unknown error"
                            )
                            logger.error(f"OpenAI API error: {error_msg}")

                            if (
                                "token" in error_msg.lower()
                                and "limit" in error_msg.lower()
                            ):
                                raise EmbeddingTokenLimitError(error_msg)
                            elif (
                                "rate" in error_msg.lower()
                                and "limit" in error_msg.lower()
                            ):
                                raise EmbeddingRateLimitError(error_msg)
                            elif "model" in error_msg.lower():
                                raise EmbeddingModelError(error_msg)
                            else:
                                raise EmbeddingGenerationError(
                                    f"OpenAI API error: {error_msg}"
                                )

                        # Extract embeddings and token count
                        embeddings_data = response_data["data"]

                        # Make sure embeddings are in the correct order
                        embeddings_data = sorted(
                            embeddings_data, key=lambda x: x["index"]
                        )

                        total_tokens_used = response_data["usage"]["prompt_tokens"]

                        # Convert to numpy arrays
                        results = []
                        for embedding_data in embeddings_data:
                            embedding_vector = embedding_data["embedding"]
                            results.append(np.array(embedding_vector, dtype=np.float32))

                        # Update rate limiting state
                        self._update_rate_limiting(total_tokens_used)

                        return results

            except (
                EmbeddingRateLimitError,
                EmbeddingModelError,
                EmbeddingTokenLimitError,
            ):
                # Don't retry these exceptions
                raise
            except Exception as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Batch embedding generation attempt {attempt+1} failed: {str(e)}. Retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"All batch embedding generation attempts failed: {str(e)}"
                    )
                    raise EmbeddingGenerationError(
                        f"Failed to generate batch embeddings after {self.max_retries} attempts: {str(e)}"
                    )

    def get_config(self) -> Dict[str, Any]:
        """Get the configuration of this provider.

        Returns:
            A dictionary with the provider configuration
        """
        return {
            "name": self.name,
            "model_name": self.model_name,
            "api_base": self.api_base,
            "dimension": self.dimension,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_tokens": self.rate_limit_tokens,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "max_tokens_per_request": self.max_tokens_per_request,
        }

    async def _apply_rate_limiting(self, request_count: int, token_count: int) -> None:
        """Apply rate limiting before making a request.

        Args:
            request_count: Number of requests to be made
            token_count: Number of tokens to be processed

        Raises:
            EmbeddingRateLimitError: If rate limits would be exceeded
        """
        current_time = time.time()
        one_minute_ago = current_time - 60

        # Clean up old timestamps
        self._request_timestamps = [
            t for t in self._request_timestamps if t >= one_minute_ago
        ]
        self._token_counts = self._token_counts[-self.rate_limit_requests :]

        # Check if limits would be exceeded
        if len(self._request_timestamps) + request_count > self.rate_limit_requests:
            # Calculate time until we can make the request
            oldest_timestamp = self._request_timestamps[0]
            wait_time = 60 - (current_time - oldest_timestamp)
            logger.warning(
                f"Request rate limit would be exceeded. Waiting {wait_time:.2f}s"
            )
            raise EmbeddingRateLimitError(
                f"Request rate limit exceeded. Try again in {wait_time:.2f}s"
            )

        recent_tokens = sum(self._token_counts)
        if recent_tokens + token_count > self.rate_limit_tokens:
            # Calculate time until we can make the request
            wait_time = 60  # Simplified - we wait a full minute
            logger.warning(f"Token rate limit would be exceeded. Waiting {wait_time}s")
            raise EmbeddingRateLimitError(
                f"Token rate limit exceeded. Try again in {wait_time}s"
            )

    def _update_rate_limiting(self, token_count: int) -> None:
        """Update rate limiting state after a successful request.

        Args:
            token_count: Number of tokens processed in the request
        """
        current_time = time.time()
        self._request_timestamps.append(current_time)
        self._token_counts.append(token_count)
