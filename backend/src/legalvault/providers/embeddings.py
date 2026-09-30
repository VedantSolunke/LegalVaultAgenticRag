"""Embedding providers for section ingest and semantic retrieval."""

from __future__ import annotations

import hashlib
import math
from typing import Protocol

EMBEDDING_DIMENSION = 768


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]: ...

    def embed_query(self, text: str) -> list[float]: ...


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


class StubEmbeddingProvider:
    """Deterministic embeddings for tests and offline ingest without Gemini."""

    def embed_text(self, text: str) -> list[float]:
        return self._hash_embed(text)

    def embed_query(self, text: str) -> list[float]:
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> list[float]:
        vec = [0.0] * EMBEDDING_DIMENSION
        lowered = text.lower().strip()
        for token in lowered.split():
            digest = hashlib.sha256(token.encode()).digest()
            for i in range(EMBEDDING_DIMENSION):
                byte = digest[i % len(digest)]
                vec[i] += (byte / 255.0) - 0.5
        return _normalize(vec)
