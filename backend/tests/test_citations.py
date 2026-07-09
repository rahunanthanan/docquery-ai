"""Unit tests for citation marker mapping (§10: citation mapping)."""

import uuid

from app.qa.citations import extract_citations
from app.qa.retrieval import RetrievedChunk


def _chunk(content: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        page_number=1,
        content=content,
        similarity=0.9,
    )


CHUNKS = [_chunk("alpha"), _chunk("beta"), _chunk("gamma")]


def test_markers_map_to_chunks_in_first_mention_order() -> None:
    result = extract_citations("claim [2], then [1].", CHUNKS)
    assert [(m, c.content) for m, c in result] == [(2, "beta"), (1, "alpha")]


def test_duplicate_markers_are_deduplicated() -> None:
    result = extract_citations("[1] and again [1] and [1]", CHUNKS)
    assert len(result) == 1


def test_out_of_range_markers_are_ignored() -> None:
    result = extract_citations("[0] invalid, [4] too big, [3] fine", CHUNKS)
    assert [(m, c.content) for m, c in result] == [(3, "gamma")]


def test_no_markers_means_no_citations() -> None:
    assert extract_citations("an answer without any markers", CHUNKS) == []
