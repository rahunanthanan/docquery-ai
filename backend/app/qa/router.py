"""Conversation and question endpoints (§4.2)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import client_ip
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.db import get_db_session
from app.qa import service
from app.qa.rules import NO_ANSWER_NOTICE
from app.qa.schemas import (
    DEFAULT_CONVERSATION_TITLE,
    AskResponse,
    ConversationCreate,
    ConversationDetailOut,
    ConversationListOut,
    ConversationOut,
    QuestionCreate,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["qa"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate, user: CurrentUser, session: DbSession
) -> ConversationOut:
    conversation = await service.create_conversation(
        session, owner=user, title=body.title or DEFAULT_CONVERSATION_TITLE
    )
    return ConversationOut.model_validate(conversation, from_attributes=True)


@router.get("")
async def list_conversations(
    user: CurrentUser,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationListOut:
    conversations, total = await service.list_conversations(
        session, owner=user, limit=limit, offset=offset
    )
    return ConversationListOut(
        items=[
            ConversationOut.model_validate(c, from_attributes=True) for c in conversations
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID, user: CurrentUser, session: DbSession
) -> ConversationDetailOut:
    return await service.conversation_detail(
        session, owner=user, conversation_id=conversation_id
    )


@router.post("/{conversation_id}/questions", status_code=status.HTTP_201_CREATED)
async def ask_question(
    conversation_id: uuid.UUID,
    body: QuestionCreate,
    request: Request,
    user: CurrentUser,
    session: DbSession,
) -> AskResponse:
    question, answer = await service.ask_question(
        session,
        owner=user,
        conversation_id=conversation_id,
        text=body.text,
        ip=client_ip(request),
    )
    return AskResponse(
        question=service.question_out(question),
        answer=answer,
        notice=None if answer is not None else NO_ANSWER_NOTICE,
    )
