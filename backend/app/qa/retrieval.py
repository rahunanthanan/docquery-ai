"""pgvector cosine retrieval, scoped to the asking user's documents (§4.3)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.documents.models import DocStatus, Document
from app.ingestion.models import Chunk
from app.qa.rules import SIMILARITY_THRESHOLD, TOP_K


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    content: str
    similarity: float


async def retrieve_chunks(
    session: AsyncSession, *, owner: User, query_embedding: list[float]
) -> list[RetrievedChunk]:
    distance = Chunk.embedding.cosine_distance(query_embedding)
    rows = await session.execute(
        select(Chunk.id, Chunk.document_id, Chunk.page_number, Chunk.content, distance)
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.owner_id == owner.id,  # never retrieve across users
            Document.deleted_at.is_(None),
            Document.status == DocStatus.ready,
        )
        .order_by(distance)
        .limit(TOP_K)
    )
    retrieved = []
    for chunk_id, document_id, page_number, content, dist in rows:
        similarity = 1.0 - float(dist)
        if similarity >= SIMILARITY_THRESHOLD:  # §4.3: drop weak matches
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    page_number=page_number,
                    content=content,
                    similarity=similarity,
                )
            )
    return retrieved
