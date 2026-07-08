"""End-to-end ingestion tests: upload → BackgroundTasks pipeline → status
lifecycle and stored vectors (§4.1, §7, §9).

TestClient executes BackgroundTasks synchronously after the response, so a
follow-up GET observes the final document status deterministically.
"""

import asyncio
import os

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.test_documents import DOCX_BYTES, DOCX_MIME, _auth_headers, _upload


def _pdf_with_pages(texts: list[str]) -> bytes:
    """Build a minimal but structurally valid PDF (with xref) that pypdf can parse."""
    n = len(texts)
    font_obj = 3 + 2 * n
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode(),
    ]
    for i, page_text in enumerate(texts):
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {4 + 2 * i} 0 R "
                f"/Resources << /Font << /F1 {font_obj} 0 R >> >> >>"
            ).encode()
        )
        stream = f"BT /F1 12 Tf 72 720 Td ({page_text}) Tj ET".encode()
        objects.append(
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF"
    ).encode()
    return bytes(out)


def _chunk_rows(document_id: str) -> list[tuple[int, int, str]]:
    async def go() -> list[tuple[int, int, str]]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT chunk_index, page_number, content FROM chunks "
                    "WHERE document_id = :id ORDER BY chunk_index"
                ),
                {"id": document_id},
            )
            rows = [(r[0], r[1], r[2]) for r in result]
        await engine.dispose()
        return rows

    return asyncio.run(go())


def test_markdown_upload_becomes_ready_with_chunks(client: TestClient) -> None:
    headers = _auth_headers(client)
    content = ("# Title\n\n" + "Interesting facts. " * 40).encode()
    document_id = _upload(
        client, headers, filename="notes.md", content=content, mime="text/markdown"
    ).json()["id"]

    detail = client.get(f"/api/v1/documents/{document_id}", headers=headers).json()
    assert detail["status"] == "ready"
    assert detail["pageCount"] == 1
    assert detail["errorMessage"] is None

    rows = _chunk_rows(document_id)
    assert len(rows) >= 1
    assert rows[0][0] == 0 and rows[0][1] == 1  # chunk_index from 0, page 1
    assert "Interesting facts." in rows[0][2]


def test_multipage_pdf_sets_page_count_and_page_numbers(client: TestClient) -> None:
    headers = _auth_headers(client)
    pdf = _pdf_with_pages(["Alpha content on page one", "Beta content on page two"])
    document_id = _upload(client, headers, filename="two-pages.pdf", content=pdf).json()["id"]

    detail = client.get(f"/api/v1/documents/{document_id}", headers=headers).json()
    assert detail["status"] == "ready", detail
    assert detail["pageCount"] == 2

    rows = _chunk_rows(document_id)
    assert [r[1] for r in rows] == [1, 2]
    assert "Alpha" in rows[0][2] and "Beta" in rows[1][2]


def test_corrupt_docx_is_marked_failed_not_crashed(client: TestClient) -> None:
    headers = _auth_headers(client)
    # valid zip magic bytes, invalid archive → passes upload validation, fails parsing
    response = _upload(
        client, headers, filename="broken.docx", content=DOCX_BYTES, mime=DOCX_MIME
    )
    assert response.status_code == 202  # §9: ingestion failures never crash the request

    detail = client.get(f"/api/v1/documents/{response.json()['id']}", headers=headers).json()
    assert detail["status"] == "failed"
    assert detail["errorMessage"] is not None and "Ingestion failed" in detail["errorMessage"]
    assert _chunk_rows(response.json()["id"]) == []


def test_delete_removes_vectors(client: TestClient) -> None:
    headers = _auth_headers(client)
    document_id = _upload(
        client, headers, filename="gone.txt", content=b"soon to be deleted", mime="text/plain"
    ).json()["id"]
    assert len(_chunk_rows(document_id)) >= 1

    assert client.delete(f"/api/v1/documents/{document_id}", headers=headers).status_code == 204
    assert _chunk_rows(document_id) == []


def test_embeddings_are_stored_with_correct_dimension(client: TestClient) -> None:
    headers = _auth_headers(client)
    document_id = _upload(
        client, headers, filename="dims.txt", content=b"check the vector size", mime="text/plain"
    ).json()["id"]

    async def go() -> int:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.connect() as conn:
            dim = await conn.scalar(
                text("SELECT vector_dims(embedding) FROM chunks WHERE document_id = :id LIMIT 1"),
                {"id": document_id},
            )
        await engine.dispose()
        return int(dim or 0)

    assert asyncio.run(go()) == 1536
