"""Review queue and decision logic (§4.2, §6, §7, §8)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_event
from app.auth.models import User
from app.core.errors import NotFoundError
from app.qa.models import Answer, AnswerStatus, Question
from app.review.models import ReviewDecision
from app.review.schemas import DecisionOut, QueueItemOut
from app.review.transitions import allowed_decisions, assert_transition


async def review_queue(
    session: AsyncSession,
    *,
    status: AnswerStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[QueueItemOut], int]:
    base = (
        select(Answer, Question, User.email)
        .join(Question, Answer.question_id == Question.id)
        .join(User, Question.asked_by == User.id)
    )
    if status is not None:
        base = base.where(Answer.review_status == status)
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = (
        await session.execute(
            base.order_by(Answer.created_at, Answer.id).limit(limit).offset(offset)
        )
    ).all()
    items = [
        QueueItemOut(
            answer_id=answer.id,
            question_id=question.id,
            question_text=question.text,
            content=answer.content,
            model_name=answer.model_name,
            review_status=answer.review_status,
            asker_email=email,
            created_at=answer.created_at,
            allowed_decisions=allowed_decisions(answer.review_status),
        )
        for answer, question, email in rows
    ]
    return items, total or 0


async def decide(
    session: AsyncSession,
    *,
    reviewer: User,
    answer_id: uuid.UUID,
    decision: AnswerStatus,
    comment: str | None,
    ip: str | None,
) -> DecisionOut:
    answer = await session.get(Answer, answer_id)
    if answer is None:
        raise NotFoundError("Answer not found.", code="ANSWER_NOT_FOUND")
    previous_status = answer.review_status
    assert_transition(previous_status, decision)  # §7: illegal → 409

    row = ReviewDecision(
        answer_id=answer.id, reviewer_id=reviewer.id, decision=decision, comment=comment
    )
    session.add(row)
    await session.flush()
    answer.review_status = decision

    # §8: audit lands in the same transaction as the status change
    log_event(
        session,
        actor=reviewer,
        action=f"answer.{decision.value}",
        entity_type="answer",
        entity_id=answer.id,
        metadata={
            "decision_id": str(row.id),
            "from_status": previous_status.value,
            "to_status": decision.value,
            "has_comment": comment is not None,
        },
        ip=ip,
    )
    await session.commit()
    await session.refresh(row)
    return DecisionOut(
        id=row.id,
        answer_id=answer.id,
        decision=row.decision,
        comment=row.comment,
        review_status=answer.review_status,
        created_at=row.created_at,
    )
