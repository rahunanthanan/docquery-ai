"""Unit tests for the deterministic chunker (§10: chunking logic)."""

from app.ingestion.chunking import (
    CHUNK_OVERLAP_CHARS,
    MAX_CHUNK_CHARS,
    approx_token_count,
    chunk_text,
)


def test_empty_and_whitespace_input_produce_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\n   \n") == []


def test_short_text_is_a_single_chunk() -> None:
    assert chunk_text("hello world") == ["hello world"]


def test_small_paragraphs_are_packed_together() -> None:
    text = "first paragraph\n\nsecond paragraph"
    assert chunk_text(text) == ["first paragraph\n\nsecond paragraph"]


def test_paragraphs_split_when_exceeding_max() -> None:
    paragraph = "x" * 700
    chunks = chunk_text(f"{paragraph}\n\n{paragraph}\n\n{paragraph}")
    assert len(chunks) == 3  # 700+700 > 1200, so one paragraph per chunk
    assert all(len(c) <= MAX_CHUNK_CHARS for c in chunks)


def test_oversized_paragraph_hard_splits_with_overlap() -> None:
    blob = "".join(str(i % 10) for i in range(3000))
    chunks = chunk_text(blob)
    assert len(chunks) > 1
    assert all(len(c) <= MAX_CHUNK_CHARS for c in chunks)
    for left, right in zip(chunks, chunks[1:], strict=False):
        assert left[-CHUNK_OVERLAP_CHARS:] == right[:CHUNK_OVERLAP_CHARS]


def test_no_content_is_lost() -> None:
    paragraphs = [f"paragraph number {i} " + "word " * 30 for i in range(20)]
    text = "\n\n".join(paragraphs)
    joined = "".join(chunk_text(text))
    for i in range(20):
        assert f"paragraph number {i}" in joined


def test_chunking_is_deterministic() -> None:
    text = "para one\n\n" + "y" * 2500 + "\n\npara three"
    assert chunk_text(text) == chunk_text(text)


def test_approx_token_count_is_positive() -> None:
    assert approx_token_count("") == 1
    assert approx_token_count("abcd" * 100) == 100
