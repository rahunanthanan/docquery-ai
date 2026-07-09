"""Per-model pricing for cost capture on answers (§5 cost_usd, §10).

Rates are USD per million tokens (input, output). Unknown models cost 0
rather than failing — cost tracking must never block an answer.
"""

from decimal import Decimal

PRICING_PER_MTOK: dict[str, tuple[Decimal, Decimal]] = {
    "fake-chat": (Decimal("0"), Decimal("0")),
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "gpt-4o": (Decimal("2.50"), Decimal("10.00")),
    "claude-haiku-4-5-20251001": (Decimal("1.00"), Decimal("5.00")),
    "claude-sonnet-4-5": (Decimal("3.00"), Decimal("15.00")),
}

_ZERO = (Decimal("0"), Decimal("0"))


def compute_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    input_rate, output_rate = PRICING_PER_MTOK.get(model_name, _ZERO)
    cost = (prompt_tokens * input_rate + completion_tokens * output_rate) / Decimal(1_000_000)
    return cost.quantize(Decimal("0.000001"))
