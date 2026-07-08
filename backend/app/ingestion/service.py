"""Ingestion pipeline: parse → chunk → embed → store vectors (§4.1, §7, §9).

Runs via FastAPI BackgroundTasks in v1, which is fine for a single-process
demo. Documented upgrade path (§9): move `ingest_document` behind a worker
queue (e.g. arq or Celery) — it owns its own session and takes only a
document id, so only the dispatch site in the documents router changes.

Failures never propagate: the document is marked `failed` with a
human-readable error_message (§9) and the exception is logged.
"""

import uuid
from pathlib import Path

import structlog

from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.documents.models import DocStatus, Document
from app.ingestion.chunking import approx_token_count, chunk_text
from app.ingestion.models import Chunk
from app.ingestion.parsers import parse_document
from app.llm.factory import get_embedding_provider

logger = structlog.get_logger()


async def ingest_document(document_id: uuid.UUID) -> None:
    async with get_sessionmaker()() as session:
        document = await session.get(Document, document_id)
        if document is None or document.deleted_at is not None:
            return
        document.status = DocStatus.processing
        await session.commit()

        try:
            path = Path(get_settings().upload_dir) / document.storage_path
            pages = parse_document(path, document.mime_type)
            page_chunks = [
                (page_number, content)
                for page_number, text in pages
                for content in chunk_text(text)
            ]
            embeddings = (
                await get_embedding_provider().embed([content for _, content in page_chunks])
                if page_chunks
                else []
            )
            session.add_all(
                Chunk(
                    document_id=document.id,
                    chunk_index=index,
                    page_number=page_number,
                    content=content,
                    token_count=approx_token_count(content),
                    embedding=embedding,
                )
                for index, ((page_number, content), embedding) in enumerate(
                    zip(page_chunks, embeddings, strict=True)
                )
            )
            document.page_count = len(pages)
            document.status = DocStatus.ready
            await session.commit()
            logger.info(
                "document_ingested",
                document_id=str(document_id),
                pages=len(pages),
                chunks=len(page_chunks),
            )
        except Exception as exc:
            await session.rollback()
            document = await session.get(Document, document_id)
            if document is not None:
                document.status = DocStatus.failed
                document.error_message = f"Ingestion failed: {exc}"[:500]
                await session.commit()
            logger.exception("ingestion_failed", document_id=str(document_id))
