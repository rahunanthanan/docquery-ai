"""Single audit writer (§8): explicit calls from services, not ORM hooks.

`log_event` only stages the row — the caller commits, so the audit write
lands in the same transaction as the domain change it records.
"""

import ipaddress
import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.auth.models import User


def client_ip(request: Request) -> str | None:
    """The requester's IP if it is one — the inet column rejects anything
    else (e.g. Starlette's TestClient reports the literal host 'testclient')."""
    host = request.client.host if request.client else None
    if host is None:
        return None
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return None
    return host


def log_event(
    session: AsyncSession,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    metadata: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor.id if actor is not None else None,
        actor_email=actor.email if actor is not None else "system",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        event_metadata=metadata,
        ip=ip,
    )
    session.add(event)
    return event
