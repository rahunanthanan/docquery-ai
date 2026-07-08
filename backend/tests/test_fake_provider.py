"""Unit tests for the deterministic fake embedding provider (§10: LLM boundary)."""

import asyncio
import math

from app.llm.base import EMBEDDING_DIM
from app.llm.fake_provider import FakeEmbeddingProvider


def _embed(texts: list[str]) -> list[list[float]]:
    return asyncio.run(FakeEmbeddingProvider().embed(texts))


def test_embeddings_have_correct_dimension() -> None:
    (vector,) = _embed(["hello"])
    assert len(vector) == EMBEDDING_DIM


def test_embeddings_are_deterministic() -> None:
    assert _embed(["same text"]) == _embed(["same text"])


def test_different_texts_get_different_vectors() -> None:
    a, b = _embed(["first text", "second text"])
    assert a != b


def test_embeddings_are_unit_vectors() -> None:
    (vector,) = _embed(["normalise me"])
    norm = math.sqrt(sum(v * v for v in vector))
    assert math.isclose(norm, 1.0, rel_tol=1e-9)
