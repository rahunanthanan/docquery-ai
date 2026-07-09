"""Token/cost aggregation over answers (§4.1 usage, §4.2)."""

from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.qa.models import Answer, Question
from app.usage.schemas import UsageOut, UsageRowOut, UsageTotalsOut


async def usage_stats(session: AsyncSession, *, group_by: Literal["day", "user"]) -> UsageOut:
    aggregates = (
        func.count(Answer.id),
        func.coalesce(func.sum(Answer.prompt_tokens), 0),
        func.coalesce(func.sum(Answer.completion_tokens), 0),
        func.coalesce(func.sum(Answer.cost_usd), 0),
        func.coalesce(func.avg(Answer.latency_ms), 0),
    )
    if group_by == "day":
        day = func.to_char(func.date_trunc("day", Answer.created_at), "YYYY-MM-DD")
        base = select(day.label("key"), *aggregates)
    else:
        base = (
            select(User.email.label("key"), *aggregates)
            .join(Question, Answer.question_id == Question.id)
            .join(User, Question.asked_by == User.id)
        )

    rows = (await session.execute(base.group_by("key").order_by("key"))).all()
    usage_rows = [
        UsageRowOut(
            key=row_key,
            answers=count,
            prompt_tokens=int(prompt_sum),
            completion_tokens=int(completion_sum),
            cost_usd=float(cost_sum),
            avg_latency_ms=round(float(latency_avg), 1),
        )
        for row_key, count, prompt_sum, completion_sum, cost_sum, latency_avg in rows
    ]
    return UsageOut(
        group_by=group_by,
        rows=usage_rows,
        totals=UsageTotalsOut(
            answers=sum(r.answers for r in usage_rows),
            prompt_tokens=sum(r.prompt_tokens for r in usage_rows),
            completion_tokens=sum(r.completion_tokens for r in usage_rows),
            cost_usd=round(sum(r.cost_usd for r in usage_rows), 6),
        ),
    )
