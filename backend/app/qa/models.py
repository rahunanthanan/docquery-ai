"""Conversation, question, answer and citation models (requirements §5)."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AnswerStatus(enum.StrEnum):
    pending_review = "pending_review"
    approved = "approved"
    flagged = "flagged"
    rejected = "rejected"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    asked_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), unique=True
    )
    content: Mapped[str] = mapped_column(Text())
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[int] = mapped_column(Integer())
    completion_tokens: Mapped[int] = mapped_column(Integer())
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[int] = mapped_column(Integer())
    review_status: Mapped[AnswerStatus] = mapped_column(
        Enum(AnswerStatus, name="answer_status", values_callable=lambda e: [m.value for m in e]),
        default=AnswerStatus.pending_review,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    answer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), index=True
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"))
    marker: Mapped[int] = mapped_column(Integer())
    similarity: Mapped[Decimal] = mapped_column(Numeric(4, 3))
