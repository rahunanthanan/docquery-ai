"""QA business logic: conversations, the RAG ask flow, history (§4.3).

Ask flow order matters (§9): the question is committed before any LLM
work, so a provider failure (502 LLM_UNAVAILABLE) never loses user input.
"""

import time
import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.errors import NotFoundError
from app.ingestion.models import Chunk
from app.llm.factory import get_chat_provider, get_embedding_provider
from app.llm.pricing import compute_cost
from app.qa.citations import extract_citations
from app.qa.models import Answer, AnswerStatus, Citation, Conversation, Question
from app.qa.prompts import SYSTEM_PROMPT, build_user_prompt
from app.qa.retrieval import retrieve_chunks
from app.qa.rules import REJECTED_ANSWER_NOTICE
from app.qa.schemas import (
    AnswerOut,
    CitationOut,
    ConversationDetailOut,
    QAItemOut,
    QuestionOut,
)

SNIPPET_CHARS = 200


async def create_conversation(session: AsyncSession, *, owner: User, title: str) -> Conversation:
    conversation = Conversation(owner_id=owner.id, title=title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def list_conversations(
    session: AsyncSession, *, owner: User, limit: int, offset: int
) -> tuple[list[Conversation], int]:
    base = select(Conversation).where(Conversation.owner_id == owner.id)
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = await session.scalars(
        base.order_by(Conversation.created_at.desc(), Conversation.id).limit(limit).offset(offset)
    )
    return list(rows), total or 0


async def get_conversation(
    session: AsyncSession, *, owner: User, conversation_id: uuid.UUID
) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.owner_id == owner.id
        )
    )
    if conversation is None:
        raise NotFoundError("Conversation not found.", code="CONVERSATION_NOT_FOUND")
    return conversation


async def ask_question(
    session: AsyncSession, *, owner: User, conversation_id: uuid.UUID, text: str
) -> tuple[Question, AnswerOut | None]:
    conversation = await get_conversation(
        session, owner=owner, conversation_id=conversation_id
    )
    question = Question(conversation_id=conversation.id, asked_by=owner.id, text=text)
    session.add(question)
    await session.commit()  # §9: saved before any LLM call can fail
    await session.refresh(question)

    (query_embedding,) = await get_embedding_provider().embed([text])
    chunks = await retrieve_chunks(session, owner=owner, query_embedding=query_embedding)
    if not chunks:
        return question, None  # §4.3: no grounded answer — no LLM call

    started = time.perf_counter()
    result = await get_chat_provider().complete(
        system=SYSTEM_PROMPT, user=build_user_prompt(chunks, text)
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    answer = Answer(
        question_id=question.id,
        content=result.content,
        model_name=result.model_name,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cost_usd=compute_cost(result.model_name, result.prompt_tokens, result.completion_tokens),
        latency_ms=latency_ms,
    )
    session.add(answer)
    await session.flush()

    cited = extract_citations(result.content, chunks)
    citation_out: list[CitationOut] = []
    for marker, chunk in cited:
        session.add(
            Citation(
                answer_id=answer.id,
                chunk_id=chunk.chunk_id,
                marker=marker,
                similarity=Decimal(str(round(chunk.similarity, 3))),
            )
        )
        citation_out.append(
            CitationOut(
                marker=marker,
                document_id=chunk.document_id,
                page=chunk.page_number,
                snippet=chunk.content[:SNIPPET_CHARS],
                similarity=round(chunk.similarity, 3),
            )
        )
    await session.commit()
    await session.refresh(answer)
    return question, _answer_out(answer, citation_out)


async def conversation_detail(
    session: AsyncSession, *, owner: User, conversation_id: uuid.UUID
) -> ConversationDetailOut:
    conversation = await get_conversation(
        session, owner=owner, conversation_id=conversation_id
    )
    questions = list(
        await session.scalars(
            select(Question)
            .where(Question.conversation_id == conversation.id)
            .order_by(Question.created_at, Question.id)
        )
    )
    question_ids = [q.id for q in questions]
    answers = {
        a.question_id: a
        for a in await session.scalars(
            select(Answer).where(Answer.question_id.in_(question_ids))
        )
    }
    citation_rows = (
        await session.execute(
            select(Citation, Chunk)
            .join(Chunk, Citation.chunk_id == Chunk.id)
            .where(Citation.answer_id.in_([a.id for a in answers.values()]))
            .order_by(Citation.marker)
        )
    ).all()
    citations_by_answer: dict[uuid.UUID, list[CitationOut]] = {}
    for citation, chunk in citation_rows:
        citations_by_answer.setdefault(citation.answer_id, []).append(
            CitationOut(
                marker=citation.marker,
                document_id=chunk.document_id,
                page=chunk.page_number,
                snippet=chunk.content[:SNIPPET_CHARS],
                similarity=float(citation.similarity),
            )
        )

    items = []
    for question in questions:
        answer = answers.get(question.id)
        answer_out = (
            _answer_out(answer, citations_by_answer.get(answer.id, []))
            if answer is not None
            else None
        )
        items.append(QAItemOut(question=question_out(question), answer=answer_out))
    return ConversationDetailOut(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        items=items,
    )


def question_out(question: Question) -> QuestionOut:
    return QuestionOut(id=question.id, text=question.text, created_at=question.created_at)


def _answer_out(answer: Answer, citations: list[CitationOut]) -> AnswerOut:
    rejected = answer.review_status == AnswerStatus.rejected
    return AnswerOut(
        id=answer.id,
        # §7: rejected answers are hidden from the asker, replaced by a notice
        content=REJECTED_ANSWER_NOTICE if rejected else answer.content,
        model_name=answer.model_name,
        prompt_tokens=answer.prompt_tokens,
        completion_tokens=answer.completion_tokens,
        cost_usd=float(answer.cost_usd),
        latency_ms=answer.latency_ms,
        review_status=answer.review_status,
        created_at=answer.created_at,
        citations=[] if rejected else citations,
    )
