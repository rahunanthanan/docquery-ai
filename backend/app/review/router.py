"""Review endpoints — reviewer role and above (§2, §4.2)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import client_ip
from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.db import get_db_session
from app.qa.models import AnswerStatus
from app.review import service
from app.review.schemas import DecisionCreate, DecisionOut, QueueOut, ReviewDetailOut

router = APIRouter(prefix="/api/v1/review", tags=["review"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Reviewer = Annotated[User, Depends(require_role("reviewer"))]


@router.get("/queue")
async def review_queue(
    reviewer: Reviewer,
    session: DbSession,
    status: Annotated[AnswerStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> QueueOut:
    items, total = await service.review_queue(
        session, status=status, limit=limit, offset=offset
    )
    return QueueOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/{answer_id}")
async def review_detail(
    answer_id: uuid.UUID, reviewer: Reviewer, session: DbSession
) -> ReviewDetailOut:
    return await service.review_detail(session, answer_id=answer_id)


@router.post("/{answer_id}/decision", status_code=status.HTTP_201_CREATED)
async def decide(
    answer_id: uuid.UUID,
    body: DecisionCreate,
    request: Request,
    reviewer: Reviewer,
    session: DbSession,
) -> DecisionOut:
    return await service.decide(
        session,
        reviewer=reviewer,
        answer_id=answer_id,
        decision=body.decision,
        comment=body.comment,
        ip=client_ip(request),
    )
