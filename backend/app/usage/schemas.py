"""Usage/cost stats schemas (§4.2)."""

from typing import Literal

from app.core.schemas import CamelModel


class UsageRowOut(CamelModel):
    key: str  # a day (YYYY-MM-DD) or a user email, depending on groupBy
    answers: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    avg_latency_ms: float


class UsageTotalsOut(CamelModel):
    answers: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class UsageOut(CamelModel):
    group_by: Literal["day", "user"]
    rows: list[UsageRowOut]
    totals: UsageTotalsOut
