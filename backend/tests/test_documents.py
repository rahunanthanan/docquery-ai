"""Documents API tests: upload validation, quotas, pagination, ownership,
soft delete (requirements §4.2, §6, §7).

conftest sets MAX_UPLOAD_BYTES=1 MB and MAX_DOCUMENTS_PER_USER=5 so the
quota and size tests stay fast.
"""

import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF\n"
DOCX_BYTES = b"PK\x03\x04" + b"\x00" * 32  # docx = zip container
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _auth_headers(client: TestClient, email: str = "docs@example.com") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "documents pass 1", "fullName": "Doc Owner"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "documents pass 1"}
    )
    return {"Authorization": f"Bearer {login.json()['accessToken']}"}


def _upload(
    client: TestClient,
    headers: dict[str, str],
    filename: str = "report.pdf",
    content: bytes = PDF_BYTES,
    mime: str = "application/pdf",
) -> httpx.Response:
    return client.post(
        "/api/v1/documents", headers=headers, files={"file": (filename, content, mime)}
    )


# ── upload ────────────────────────────────────────────────────────────────


def test_upload_pdf_returns_202_and_stores_file(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = _upload(client, headers)
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["filename"] == "report.pdf"
    assert body["status"] == "uploaded"
    assert body["sizeBytes"] == len(PDF_BYTES)
    assert body["pageCount"] is None
    stored = list(Path(os.environ["UPLOAD_DIR"]).rglob(f"{body['id']}*"))
    assert len(stored) == 1 and stored[0].read_bytes() == PDF_BYTES


@pytest.mark.parametrize(
    ("filename", "content", "mime"),
    [
        ("notes.txt", b"plain text notes", "text/plain"),
        ("readme.md", "# markdown with unicode — ✓".encode(), "text/markdown"),
        ("contract.docx", DOCX_BYTES, DOCX_MIME),
    ],
)
def test_upload_accepts_all_whitelisted_types(
    client: TestClient, filename: str, content: bytes, mime: str
) -> None:
    headers = _auth_headers(client)
    response = _upload(client, headers, filename=filename, content=content, mime=mime)
    assert response.status_code == 202, response.text


def test_upload_rejects_unsupported_mime(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = _upload(client, headers, filename="pic.png", content=b"\x89PNG", mime="image/png")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_rejects_magic_byte_mismatch(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = _upload(client, headers, content=b"just text pretending to be a pdf")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FILE_CONTENT_MISMATCH"


def test_upload_rejects_binary_masquerading_as_text(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = _upload(
        client, headers, filename="fake.txt", content=b"\xff\xfe\x00\x01", mime="text/plain"
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FILE_CONTENT_MISMATCH"


def test_upload_rejects_oversize_file(client: TestClient) -> None:
    headers = _auth_headers(client)
    oversize = PDF_BYTES + b"\x00" * (1024 * 1024)  # conftest caps at 1 MB
    response = _upload(client, headers, content=oversize)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_upload_rejects_empty_file(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = _upload(client, headers, content=b"")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EMPTY_FILE"


def test_upload_quota_exceeded_is_429(client: TestClient) -> None:
    headers = _auth_headers(client)
    for i in range(5):  # conftest quota
        assert _upload(client, headers, filename=f"doc{i}.pdf").status_code == 202
    response = _upload(client, headers, filename="one-too-many.pdf")
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "QUOTA_EXCEEDED"


def test_deleted_documents_free_quota(client: TestClient) -> None:
    headers = _auth_headers(client)
    ids = []
    for i in range(5):
        ids.append(_upload(client, headers, filename=f"doc{i}.pdf").json()["id"])
    client.delete(f"/api/v1/documents/{ids[0]}", headers=headers)
    assert _upload(client, headers, filename="replacement.pdf").status_code == 202


def test_upload_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents", files={"file": ("a.pdf", PDF_BYTES, "application/pdf")}
    )
    assert response.status_code == 401


# ── list ──────────────────────────────────────────────────────────────────


def test_list_paginates_newest_first(client: TestClient) -> None:
    headers = _auth_headers(client)
    for name in ("first.pdf", "second.pdf", "third.pdf"):
        _upload(client, headers, filename=name)

    page1 = client.get("/api/v1/documents?limit=2", headers=headers).json()
    assert page1["total"] == 3
    assert [d["filename"] for d in page1["items"]] == ["third.pdf", "second.pdf"]

    page2 = client.get("/api/v1/documents?limit=2&offset=2", headers=headers).json()
    assert [d["filename"] for d in page2["items"]] == ["first.pdf"]


def test_list_rejects_limit_over_100(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = client.get("/api/v1/documents?limit=101", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_list_only_shows_own_documents(client: TestClient) -> None:
    owner = _auth_headers(client, "owner@example.com")
    other = _auth_headers(client, "other@example.com")
    _upload(client, owner)
    body = client.get("/api/v1/documents", headers=other).json()
    assert body["total"] == 0 and body["items"] == []


# ── detail ────────────────────────────────────────────────────────────────


def test_detail_returns_processing_status(client: TestClient) -> None:
    headers = _auth_headers(client)
    document_id = _upload(client, headers).json()["id"]
    response = client.get(f"/api/v1/documents/{document_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"


def test_detail_of_someone_elses_document_is_404(client: TestClient) -> None:
    owner = _auth_headers(client, "owner@example.com")
    other = _auth_headers(client, "other@example.com")
    document_id = _upload(client, owner).json()["id"]
    response = client.get(f"/api/v1/documents/{document_id}", headers=other)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_detail_unknown_id_is_404(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = client.get(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404


def test_detail_invalid_uuid_is_422(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = client.get("/api/v1/documents/not-a-uuid", headers=headers)
    assert response.status_code == 422


# ── delete ────────────────────────────────────────────────────────────────


def test_delete_soft_deletes(client: TestClient) -> None:
    headers = _auth_headers(client)
    document_id = _upload(client, headers).json()["id"]

    response = client.delete(f"/api/v1/documents/{document_id}", headers=headers)
    assert response.status_code == 204

    assert client.get(f"/api/v1/documents/{document_id}", headers=headers).status_code == 404
    assert client.get("/api/v1/documents", headers=headers).json()["total"] == 0
    # repeat delete: already gone
    assert client.delete(f"/api/v1/documents/{document_id}", headers=headers).status_code == 404


def test_delete_someone_elses_document_is_404(client: TestClient) -> None:
    owner = _auth_headers(client, "owner@example.com")
    other = _auth_headers(client, "other@example.com")
    document_id = _upload(client, owner).json()["id"]
    assert client.delete(f"/api/v1/documents/{document_id}", headers=other).status_code == 404
    # still visible to its owner
    assert client.get(f"/api/v1/documents/{document_id}", headers=owner).status_code == 200
