"""
EmbeddingService — cloud embedding via OpenAI-compatible API

Replaces the previous Ollama-based embedding with OpenAI text-embedding-3-small
or any OpenAI-compatible embedding endpoint.
"""

import logging
import time
from typing import List, Optional

from openai import OpenAI

from ..config import Config

logger = logging.getLogger('mirofish.embedding')


class EmbeddingService:
    """Generate embeddings using an OpenAI-compatible API."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
    ):
        self.model = model or Config.EMBEDDING_MODEL
        self.base_url = base_url or Config.EMBEDDING_BASE_URL
        self.api_key = api_key or Config.EMBEDDING_API_KEY or Config.LLM_API_KEY
        self.max_retries = max_retries

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=30.0,
        )

        # Simple in-memory cache (text -> embedding vector)
        self._cache: dict[str, List[float]] = {}
        self._cache_max_size = 2000

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector (dimensions depend on model)

        Raises:
            EmbeddingError: If request fails after retries
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        text = text.strip()

        # Check cache
        if text in self._cache:
            return self._cache[text]

        vectors = self._request_embeddings([text])
        vector = vectors[0]

        self._cache_put(text, vector)
        return vector

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Number of texts per request

        Returns:
            List of embedding vectors (same order as input)
        """
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        # Check cache first
        for i, text in enumerate(texts):
            text = text.strip() if text else ""
            if text in self._cache:
                results[i] = self._cache[text]
            elif text:
                uncached_indices.append(i)
                uncached_texts.append(text)
            else:
                results[i] = [0.0] * 1536  # zero vector for empty text

        # Batch-embed uncached texts
        if uncached_texts:
            all_vectors: List[List[float]] = []
            for start in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[start:start + batch_size]
                vectors = self._request_embeddings(batch)
                all_vectors.extend(vectors)

            for idx, vec, text in zip(uncached_indices, all_vectors, uncached_texts):
                results[idx] = vec
                self._cache_put(text, vec)

        return results  # type: ignore

    def _request_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Make embedding request via OpenAI-compatible API with retry.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                )
                embeddings = [item.embedding for item in response.data]
                if len(embeddings) != len(texts):
                    raise EmbeddingError(
                        f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                    )
                return embeddings

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Embedding request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                # Exponential backoff
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)

        raise EmbeddingError(
            f"Embedding failed after {self.max_retries} retries: {last_error}"
        )

    def _cache_put(self, text: str, vector: List[float]) -> None:
        """Add to cache, evicting oldest entries if full."""
        if len(self._cache) >= self._cache_max_size:
            keys_to_remove = list(self._cache.keys())[:self._cache_max_size // 10]
            for key in keys_to_remove:
                del self._cache[key]
        self._cache[text] = vector

    def health_check(self) -> bool:
        """Check if embedding endpoint is reachable."""
        try:
            vec = self.embed("health check")
            return len(vec) > 0
        except Exception:
            return False


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass
