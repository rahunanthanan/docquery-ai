"""Document endpoints: upload, list, detail, delete (§4.2)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import client_ip
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db_session
from app.documents import service
from app.documents.schemas import DocumentDetailOut, DocumentListOut, DocumentOut
from app.ingestion.service import ingest_document

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile,
    background: BackgroundTasks,
    request: Request,
    user: CurrentUser,
    session: DbSession,
) -> DocumentOut:
    document = await service.upload_document(
        session, owner=user, upload=file, ip=client_ip(request)
    )
    background.add_task(ingest_document, document.id)  # §9: v1 runs ingestion in-process
    return DocumentOut.model_validate(document)


@router.get("")
async def list_documents(
    user: CurrentUser,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,  # §6: limit ≤ 100
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DocumentListOut:
    documents, total = await service.list_documents(
        session, owner=user, limit=limit, offset=offset
    )
    return DocumentListOut(
        items=[DocumentOut.model_validate(d) for d in documents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{document_id}")
async def get_document(
    document_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> DocumentDetailOut:
    document = await service.get_document(session, owner=user, document_id=document_id)
    count = await service.chunk_count(session, document_id=document.id)
    return DocumentDetailOut(
        **DocumentOut.model_validate(document).model_dump(), chunk_count=count
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, request: Request, user: CurrentUser, session: DbSession
) -> None:
    await service.delete_document(
        session, owner=user, document_id=document_id, ip=client_ip(request)
    )
