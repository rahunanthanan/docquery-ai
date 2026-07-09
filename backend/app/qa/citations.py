"""Map [1]-style markers in the model's answer to retrieved chunks (§4.3).

Unit-tested per §10 (citation mapping): duplicates are de-duplicated,
out-of-range markers ignored, first-mention order preserved.
"""

import re
from collections.abc import Sequence

from app.qa.retrieval import RetrievedChunk

_MARKER_PATTERN = re.compile(r"\[(\d+)\]")


def extract_citations(
    content: str, chunks: Sequence[RetrievedChunk]
) -> list[tuple[int, RetrievedChunk]]:
    seen: set[int] = set()
    citations: list[tuple[int, RetrievedChunk]] = []
    for match in _MARKER_PATTERN.finditer(content):
        marker = int(match.group(1))
        if marker in seen or not 1 <= marker <= len(chunks):
            continue
        seen.add(marker)
        citations.append((marker, chunks[marker - 1]))
    return citations
