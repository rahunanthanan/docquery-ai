"""Deterministic text chunking (§4.1, unit-tested per §10).

Greedy paragraph packing: paragraphs are joined until a chunk would
exceed MAX_CHUNK_CHARS; a single oversized paragraph is hard-split with
CHUNK_OVERLAP_CHARS of overlap so no sentence is lost at a boundary.
Character-based sizing keeps the algorithm model-agnostic; token counts
are approximated at ~4 chars/token for usage accounting.
"""

MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200


def approx_token_count(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_text(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHUNK_CHARS:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while True:
                chunks.append(paragraph[start : start + MAX_CHUNK_CHARS])
                if start + MAX_CHUNK_CHARS >= len(paragraph):
                    break
                start += MAX_CHUNK_CHARS - CHUNK_OVERLAP_CHARS
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > MAX_CHUNK_CHARS:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks
