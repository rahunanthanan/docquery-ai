"""Review request/response schemas — decision rules from §6."""

import uuid
from datetime import datetime

from pydantic import model_validator

from app.core.schemas import CamelModel
from app.qa.models import AnswerStatus


class DecisionCreate(CamelModel):
    decision: AnswerStatus
    comment: str | None = None

    @model_validator(mode="after")
    def decision_rules(self) -> "DecisionCreate":
        if self.decision == AnswerStatus.pending_review:
            raise ValueError("Decision must be approved, flagged or rejected.")
        if self.comment is not None:
            self.comment = self.comment.strip() or None
        if self.decision != AnswerStatus.approved and self.comment is None:
            # §6: comment required (10–1,000 chars) when decision ≠ approved
            raise ValueError("A comment is required when flagging or rejecting.")
        if self.comment is not None and not 10 <= len(self.comment) <= 1000:
            raise ValueError("Comment must be between 10 and 1,000 characters.")
        return self


class QueueItemOut(CamelModel):
    answer_id: uuid.UUID
    question_id: uuid.UUID
    question_text: str
    content: str
    model_name: str
    review_status: AnswerStatus
    asker_email: str
    created_at: datetime
    # §6: the UI renders only what the API allows
    allowed_decisions: list[AnswerStatus]


class QueueOut(CamelModel):
    items: list[QueueItemOut]
    total: int
    limit: int
    offset: int


class DecisionOut(CamelModel):
    id: uuid.UUID
    answer_id: uuid.UUID
    decision: AnswerStatus
    comment: str | None
    review_status: AnswerStatus
    created_at: datetime
