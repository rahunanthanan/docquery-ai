"""Document upload, listing and soft-delete business logic (§4, §6, §7).

Files are stored on disk under ``settings.upload_dir`` at a UUID-based
path — the user-supplied filename is display-only metadata, so path
traversal is impossible by construction.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import get_settings
from app.core.errors import NotFoundError, QuotaExceeded, ValidationFailed
from app.documents.models import Document

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

ALLOWED_MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    DOCX_MIME: ".docx",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


def _matches_magic_bytes(mime: str, content: bytes) -> bool:
    """§6: check content, not just the declared type or extension."""
    if mime == "application/pdf":
        return content.startswith(b"%PDF-")
    if mime == DOCX_MIME:
        return content.startswith(b"PK\x03\x04")  # docx is a zip container
    try:  # text/plain, text/markdown: must be valid UTF-8
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


async def upload_document(session: AsyncSession, *, owner: User, upload: UploadFile) -> Document:
    settings = get_settings()

    active = await session.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.owner_id == owner.id, Document.deleted_at.is_(None))
    )
    if active is not None and active >= settings.max_documents_per_user:
        raise QuotaExceeded(
            f"Document limit reached ({settings.max_documents_per_user} per user)."
        )

    mime = upload.content_type or ""
    extension = ALLOWED_MIME_EXTENSIONS.get(mime)
    if extension is None:
        raise ValidationFailed(
            "Unsupported file type. Allowed: PDF, DOCX, plain text, Markdown.",
            code="UNSUPPORTED_FILE_TYPE",
        )

    content = await upload.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes // (1024 * 1024)
        raise ValidationFailed(
            f"File exceeds the maximum size of {max_mb} MB.", code="FILE_TOO_LARGE"
        )
    if not content:
        raise ValidationFailed("File is empty.", code="EMPTY_FILE")
    if not _matches_magic_bytes(mime, content):
        raise ValidationFailed(
            "File content does not match its declared type.", code="FILE_CONTENT_MISMATCH"
        )

    document_id = uuid.uuid4()
    relative_path = f"{owner.id}/{document_id}{extension}"
    target = Path(settings.upload_dir) / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    document = Document(
        id=document_id,
        owner_id=owner.id,
        filename=upload.filename or f"upload{extension}",
        mime_type=mime,
        size_bytes=len(content),
        storage_path=relative_path,
    )
    session.add(document)
    try:
        await session.commit()
    except Exception:
        target.unlink(missing_ok=True)  # never leave orphan files behind
        raise
    await session.refresh(document)
    return document


async def list_documents(
    session: AsyncSession, *, owner: User, limit: int, offset: int
) -> tuple[list[Document], int]:
    base = select(Document).where(Document.owner_id == owner.id, Document.deleted_at.is_(None))
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = await session.scalars(
        base.order_by(Document.created_at.desc(), Document.id).limit(limit).offset(offset)
    )
    return list(rows), total or 0


async def get_document(
    session: AsyncSession, *, owner: User, document_id: uuid.UUID
) -> Document:
    document = await session.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner.id,  # someone else's doc looks identical to a missing one
            Document.deleted_at.is_(None),
        )
    )
    if document is None:
        raise NotFoundError("Document not found.", code="DOCUMENT_NOT_FOUND")
    return document


async def delete_document(
    session: AsyncSession, *, owner: User, document_id: uuid.UUID
) -> None:
    document = await get_document(session, owner=owner, document_id=document_id)
    document.deleted_at = datetime.now(UTC)
    # Task 5 adds vector cleanup here once the chunks table exists (§4.2).
    await session.commit()
