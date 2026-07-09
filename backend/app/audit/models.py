"""Append-only audit event model (requirements §5, §8).

A database trigger (migration 0005) rejects UPDATE and DELETE on this
table, so the append-only guarantee holds even for the owning role.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    actor_email: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100))  # e.g. answer.approved
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    # attribute named event_metadata because `metadata` is reserved on Base
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB())
    ip: Mapped[str | None] = mapped_column(INET())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
