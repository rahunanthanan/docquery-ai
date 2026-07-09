"""Answer review lifecycle (§7) as an explicit allowed-transition map.

    pending_review ──▶ approved                (terminal)
          │
          ├──────────▶ flagged ──▶ approved | rejected
          │
          └──────────▶ rejected               (terminal)
"""

from app.core.errors import InvalidTransition
from app.qa.models import AnswerStatus

ALLOWED_TRANSITIONS: dict[AnswerStatus, frozenset[AnswerStatus]] = {
    AnswerStatus.pending_review: frozenset(
        {AnswerStatus.approved, AnswerStatus.flagged, AnswerStatus.rejected}
    ),
    AnswerStatus.flagged: frozenset({AnswerStatus.approved, AnswerStatus.rejected}),
    AnswerStatus.approved: frozenset(),
    AnswerStatus.rejected: frozenset(),
}


def allowed_decisions(current: AnswerStatus) -> list[AnswerStatus]:
    return sorted(ALLOWED_TRANSITIONS[current])


def assert_transition(current: AnswerStatus, target: AnswerStatus) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(
            f"An answer in status '{current.value}' cannot move to '{target.value}'."
        )
