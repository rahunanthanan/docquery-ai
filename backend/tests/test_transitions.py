"""Unit tests for the §7 answer transition map (§10: transition map)."""

import pytest

from app.core.errors import InvalidTransition
from app.qa.models import AnswerStatus
from app.review.transitions import allowed_decisions, assert_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (AnswerStatus.pending_review, AnswerStatus.approved),
        (AnswerStatus.pending_review, AnswerStatus.flagged),
        (AnswerStatus.pending_review, AnswerStatus.rejected),
        (AnswerStatus.flagged, AnswerStatus.approved),
        (AnswerStatus.flagged, AnswerStatus.rejected),
    ],
)
def test_legal_transitions(current: AnswerStatus, target: AnswerStatus) -> None:
    assert_transition(current, target)  # must not raise


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (AnswerStatus.approved, AnswerStatus.rejected),
        (AnswerStatus.approved, AnswerStatus.flagged),
        (AnswerStatus.approved, AnswerStatus.approved),
        (AnswerStatus.rejected, AnswerStatus.approved),
        (AnswerStatus.rejected, AnswerStatus.flagged),
        (AnswerStatus.flagged, AnswerStatus.flagged),
        (AnswerStatus.pending_review, AnswerStatus.pending_review),
    ],
)
def test_illegal_transitions_raise(current: AnswerStatus, target: AnswerStatus) -> None:
    with pytest.raises(InvalidTransition):
        assert_transition(current, target)


def test_terminal_states_allow_nothing() -> None:
    assert allowed_decisions(AnswerStatus.approved) == []
    assert allowed_decisions(AnswerStatus.rejected) == []


def test_pending_allows_all_three_decisions() -> None:
    assert set(allowed_decisions(AnswerStatus.pending_review)) == {
        AnswerStatus.approved,
        AnswerStatus.flagged,
        AnswerStatus.rejected,
    }
