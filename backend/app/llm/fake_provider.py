"""Deterministic fake provider — the zero-API-key demo/CI path (§12).

Embeddings are sha256-seeded random unit vectors: the same text always
produces the same vector, so similarity search behaves consistently in
tests without any real model.
"""

import hashlib
import math
import random

from app.llm.base import EMBEDDING_DIM


class FakeEmbeddingProvider:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    @staticmethod
    def _embed_one(text: str) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
        rng = random.Random(seed)
        vector = [rng.gauss(0.0, 1.0) for _ in range(EMBEDDING_DIM)]
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
