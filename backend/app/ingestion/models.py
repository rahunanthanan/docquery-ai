"""Chunk model with pgvector embedding (requirements §5)."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.llm.base import EMBEDDING_DIM


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_chunk_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer())
    page_number: Mapped[int] = mapped_column(Integer())
    content: Mapped[str] = mapped_column(Text())
    token_count: Mapped[int] = mapped_column(Integer())
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
