"""File parsing: bytes on disk → per-page text (§4.1).

DOCX and plain-text formats have no page concept, so their whole content
counts as page 1 — citations for them point at the document, not a page.
"""

from pathlib import Path

import docx
from pypdf import PdfReader

from app.documents.service import DOCX_MIME


def parse_document(path: Path, mime: str) -> list[tuple[int, str]]:
    """Return (page_number, text) pairs, page numbers 1-based."""
    if mime == "application/pdf":
        reader = PdfReader(str(path))
        return [
            (number, page.extract_text() or "")
            for number, page in enumerate(reader.pages, start=1)
        ]
    if mime == DOCX_MIME:
        paragraphs = docx.Document(str(path)).paragraphs
        return [(1, "\n\n".join(p.text for p in paragraphs))]
    return [(1, path.read_text(encoding="utf-8"))]
