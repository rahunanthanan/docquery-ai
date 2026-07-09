"""Audit log query endpoint — reviewer and above (§4.2, §8)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.audit.schemas import AuditEventOut, AuditListOut
from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.db import get_db_session

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Reviewer = Annotated[User, Depends(require_role("reviewer"))]


@router.get("")
async def query_audit_log(
    reviewer: Reviewer,
    session: DbSession,
    entity: Annotated[str | None, Query(max_length=50)] = None,
    actor: Annotated[str | None, Query(max_length=255)] = None,
    action: Annotated[str | None, Query(max_length=100)] = None,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditListOut:
    base = select(AuditEvent)
    if entity is not None:
        base = base.where(AuditEvent.entity_type == entity)
    if actor is not None:
        base = base.where(AuditEvent.actor_email == actor)
    if action is not None:
        base = base.where(AuditEvent.action == action)
    if from_ is not None:
        base = base.where(AuditEvent.created_at >= from_)
    if to is not None:
        base = base.where(AuditEvent.created_at <= to)

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    events = await session.scalars(
        base.order_by(AuditEvent.id.desc()).limit(limit).offset(offset)
    )
    return AuditListOut(
        items=[
            AuditEventOut(
                id=e.id,
                actor_email=e.actor_email,
                action=e.action,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                metadata=e.event_metadata,
                # asyncpg returns inet columns as IPv4Address/IPv6Address objects
                ip=str(e.ip) if e.ip is not None else None,
                created_at=e.created_at,
            )
            for e in events
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )
