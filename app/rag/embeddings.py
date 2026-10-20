"""
Embeddings Provider Factory.
Supports OpenAI Embeddings with deterministic offline fallback for CI/CD and testing.
"""

import re
import hashlib
import numpy as np
from typing import List, Optional
from langchain_core.embeddings import Embeddings

from app.config import settings
from app.core.logging import logger


class DeterministicMockEmbeddings(Embeddings):
    """
    Deterministic mock embeddings generator for offline development,
    demonstration, and automated testing without requiring paid API keys.
    Combines word-hash features with dense normalized vectors so that
    matching keywords produce high cosine similarity.
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _embed_text(self, text: str) -> List[float]:
        vec = np.zeros(self.dimension, dtype=np.float32)

        # 1. Base deterministic ambient vector from overall text hash
        hasher = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(hasher[:8], byteorder="big") % (2**32)
        rng = np.random.default_rng(seed)
        vec += rng.standard_normal(self.dimension) * 0.05

        # 2. Token-level hash projection (bag-of-words semantic component)
        tokens = re.findall(r'\b[a-zA-Z0-9_]{2,}\b', text.lower())
        for token in tokens:
            token_hash = hashlib.md5(token.encode("utf-8")).digest()
            idx1 = int.from_bytes(token_hash[:4], byteorder="big") % self.dimension
            idx2 = int.from_bytes(token_hash[4:8], byteorder="big") % self.dimension
            vec[idx1] += 1.0
            vec[idx2] += 0.5

        # 3. L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


def get_embedding_provider(provider: Optional[str] = None) -> Embeddings:
    """
    Returns the appropriate embedding provider based on configuration.
    Falls back to DeterministicMockEmbeddings if no OpenAI API key is detected.
    """
    selected_provider = provider or settings.EMBEDDING_PROVIDER

    if selected_provider.lower() == "openai":
        api_key = settings.OPENAI_API_KEY
        if api_key and api_key.strip():
            try:
                from langchain_openai import OpenAIEmbeddings
                logger.info(f"Initialized OpenAI Embeddings (model={settings.EMBEDDING_MODEL})")
                return OpenAIEmbeddings(
                    model=settings.EMBEDDING_MODEL,
                    openai_api_key=api_key.strip()
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI Embeddings, falling back to Mock: {e}")
        else:
            logger.info("No OPENAI_API_KEY provided; using deterministic mock embeddings for offline mode/testing.")

    logger.info("Initialized DeterministicMockEmbeddings (1536-dim)")
    return DeterministicMockEmbeddings(dimension=1536)
