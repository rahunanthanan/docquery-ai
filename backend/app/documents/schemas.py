"""Document response schemas."""

import uuid
from datetime import datetime

from pydantic import ConfigDict

from app.core.schemas import CamelModel
from app.documents.models import DocStatus


class DocumentOut(CamelModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    status: DocStatus
    page_count: int | None
    error_message: str | None
    created_at: datetime


class DocumentListOut(CamelModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int
