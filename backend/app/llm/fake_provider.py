"""Deterministic fake provider — the zero-API-key demo/CI path (§12).

Embeddings are bag-of-words vectors around a shared base direction:
identical texts → similarity 1.0, lexically overlapping texts rank above
unrelated ones, and any two texts sit near ~0.6 — above the §4.3
retrieval threshold, so the keyless demo always finds context. Real
threshold pruning is exercised with real providers; the ungrounded path
is exercised by having no ready documents.

The fake chat provider echoes the first excerpt and cites [1] (and [2])
so citation mapping works end to end.
"""

import hashlib
import math
import random
import re

from app.ingestion.chunking import approx_token_count
from app.llm.base import EMBEDDING_DIM, ChatResult

_WORD_WEIGHT = 0.8


def _seeded_vector(seed_text: str) -> list[float]:
    seed = int.from_bytes(hashlib.sha256(seed_text.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    return [rng.gauss(0.0, 1.0) for _ in range(EMBEDDING_DIM)]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


_BASE = _normalize(_seeded_vector("docquery-fake-base-direction"))


class FakeEmbeddingProvider:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    @staticmethod
    def _embed_one(text: str) -> list[float]:
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        if words:
            acc = [0.0] * EMBEDDING_DIM
            for word in words:  # term presence, not frequency
                for i, value in enumerate(_seeded_vector(f"word:{word}")):
                    acc[i] += value
        else:
            acc = _seeded_vector(f"text:{text}")
        token_part = _normalize(acc)
        return _normalize(
            [b + _WORD_WEIGHT * t for b, t in zip(_BASE, token_part, strict=True)]
        )


class FakeChatProvider:
    MODEL_NAME = "fake-chat"

    async def complete(self, *, system: str, user: str) -> ChatResult:
        markers = re.findall(r"^\[(\d+)\]", user, flags=re.MULTILINE)
        cites = " ".join(f"[{m}]" for m in markers[:2])
        first_excerpt = re.search(r"^\[1\] (.+)$", user, flags=re.MULTILINE)
        snippet = " ".join(first_excerpt.group(1).split()[:25]) if first_excerpt else "n/a"
        content = f"According to the provided documents: {snippet} {cites}".strip()
        return ChatResult(
            content=content,
            model_name=self.MODEL_NAME,
            prompt_tokens=approx_token_count(system) + approx_token_count(user),
            completion_tokens=approx_token_count(content),
        )
