"""Audit query response schemas (§4.2)."""

import uuid
from datetime import datetime
from typing import Any

from app.core.schemas import CamelModel


class AuditEventOut(CamelModel):
    id: int
    actor_email: str
    action: str
    entity_type: str
    entity_id: uuid.UUID
    metadata: dict[str, Any] | None
    ip: str | None
    created_at: datetime


class AuditListOut(CamelModel):
    items: list[AuditEventOut]
    total: int
    limit: int
    offset: int
