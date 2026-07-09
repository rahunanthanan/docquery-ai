"""QA request/response schemas (§4.2, §6)."""

import uuid
from datetime import datetime

from pydantic import field_validator

from app.core.schemas import CamelModel
from app.qa.models import AnswerStatus

DEFAULT_CONVERSATION_TITLE = "New conversation"


class ConversationCreate(CamelModel):
    title: str | None = None

    @field_validator("title")
    @classmethod
    def title_rules(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if len(stripped) > 200:
            raise ValueError("Title must be at most 200 characters.")
        return stripped


class ConversationOut(CamelModel):
    id: uuid.UUID
    title: str
    created_at: datetime


class ConversationListOut(CamelModel):
    items: list[ConversationOut]
    total: int
    limit: int
    offset: int


class QuestionCreate(CamelModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_rules(cls, value: str) -> str:
        # §6: 3–2,000 chars, stripped; reject whitespace-only
        stripped = value.strip()
        if len(stripped) < 3 or len(stripped) > 2000:
            raise ValueError("Question must be between 3 and 2,000 characters.")
        return stripped


class QuestionOut(CamelModel):
    id: uuid.UUID
    text: str
    created_at: datetime


class CitationOut(CamelModel):
    marker: int
    document_id: uuid.UUID
    page: int
    snippet: str
    similarity: float


class AnswerOut(CamelModel):
    id: uuid.UUID
    content: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: int
    review_status: AnswerStatus
    created_at: datetime
    citations: list[CitationOut]


class AskResponse(CamelModel):
    question: QuestionOut
    answer: AnswerOut | None
    notice: str | None = None


class QAItemOut(CamelModel):
    question: QuestionOut
    answer: AnswerOut | None


class ConversationDetailOut(CamelModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    items: list[QAItemOut]
