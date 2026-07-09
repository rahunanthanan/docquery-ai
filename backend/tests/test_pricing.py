"""Unit tests for cost calculation (§10: cost calculation)."""

from decimal import Decimal

from app.llm.pricing import compute_cost


def test_known_model_cost() -> None:
    # gpt-4o-mini: $0.15/M input, $0.60/M output
    cost = compute_cost("gpt-4o-mini", prompt_tokens=1_000_000, completion_tokens=500_000)
    assert cost == Decimal("0.450000")


def test_fake_model_is_free() -> None:
    assert compute_cost("fake-chat", 10_000, 10_000) == Decimal("0")


def test_unknown_model_costs_zero_instead_of_failing() -> None:
    assert compute_cost("some-future-model", 1000, 1000) == Decimal("0")


def test_cost_is_quantized_to_six_decimals() -> None:
    cost = compute_cost("gpt-4o-mini", prompt_tokens=1, completion_tokens=1)
    assert str(cost) == "0.000001"  # rounded from 0.00000075
