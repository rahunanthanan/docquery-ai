"""Idempotent demo seed (§5, §12): runs on container start after migrations.

Creates 3 demo users (one per role), 2 sample documents ingested through
the real pipeline, and 4 answered questions left in mixed review states.
Skips entirely if any user already exists, so restarts never duplicate.

Demo credentials (password shared): user@demo.docquery,
reviewer@demo.docquery, admin@demo.docquery / DemoPassword1
"""

import asyncio
import uuid
from pathlib import Path

from sqlalchemy import func, select

from app.auth.models import User, UserRole
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.documents.models import Document
from app.ingestion.service import ingest_document
from app.qa.models import AnswerStatus
from app.qa.service import ask_question, create_conversation
from app.review.service import decide

DEMO_PASSWORD = "DemoPassword1"

SAMPLE_DOCS = {
    "q3-report.md": (
        "# Q3 Financial Report\n\n"
        "Quarterly revenue grew fourteen percent year over year, driven by "
        "subscription renewals and enterprise expansion deals.\n\n"
        "Gross margin improved to 78 percent thanks to infrastructure cost "
        "optimisation completed in August.\n\n"
        "Headcount grew from 120 to 134, concentrated in engineering and "
        "customer success."
    ),
    "risk-register.md": (
        "# Risk Register\n\n"
        "Supply chain delays remain the highest-rated operational risk, with "
        "mitigation contracts signed with two alternate vendors.\n\n"
        "Currency exposure on EUR contracts is hedged through Q2 next year.\n\n"
        "A single-region database deployment is flagged as a resilience gap; "
        "multi-region replication is planned for the next quarter."
    ),
}

QUESTIONS = [
    ("How much did quarterly revenue grow?", AnswerStatus.approved),
    ("What happened to gross margin?", AnswerStatus.flagged),
    ("What is the biggest operational risk?", AnswerStatus.rejected),
    ("How is currency exposure handled?", AnswerStatus.pending_review),
]

REVIEW_COMMENT = "Seed data: demonstrating this state in the review workflow."


async def main() -> None:
    configure_logging()
    async with get_sessionmaker()() as session:
        if await session.scalar(select(func.count()).select_from(User)):
            print("Database already seeded — skipping.")
            return

        users: dict[UserRole, User] = {}
        for role in (UserRole.user, UserRole.reviewer, UserRole.admin):
            user = User(
                email=f"{role.value}@demo.docquery",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=f"Demo {role.value.title()}",
                role=role,
            )
            session.add(user)
            users[role] = user
        await session.commit()
        demo, reviewer = users[UserRole.user], users[UserRole.reviewer]

        upload_dir = Path(get_settings().upload_dir)
        document_ids = []
        for filename, body in SAMPLE_DOCS.items():
            document_id = uuid.uuid4()
            relative = f"{demo.id}/{document_id}.md"
            target = upload_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            session.add(
                Document(
                    id=document_id,
                    owner_id=demo.id,
                    filename=filename,
                    mime_type="text/markdown",
                    size_bytes=len(body.encode()),
                    storage_path=relative,
                )
            )
            document_ids.append(document_id)
        await session.commit()
        for document_id in document_ids:
            await ingest_document(document_id)  # real pipeline: chunks + embeddings

        conversation = await create_conversation(
            session, owner=demo, title="Demo: quarterly report Q&A"
        )
        for text, target_state in QUESTIONS:
            _, answer = await ask_question(
                session, owner=demo, conversation_id=conversation.id, text=text
            )
            if answer is None:
                print(f"warning: no grounded answer for {text!r} — skipping decision")
                continue
            if target_state == AnswerStatus.pending_review:
                continue
            comment = None if target_state == AnswerStatus.approved else REVIEW_COMMENT
            await decide(
                session,
                reviewer=reviewer,
                answer_id=answer.id,
                decision=target_state,
                comment=comment,
                ip=None,
            )

    print(
        "Seeded: 3 users (user|reviewer|admin @demo.docquery, password "
        f"{DEMO_PASSWORD}), {len(SAMPLE_DOCS)} documents, {len(QUESTIONS)} answered questions."
    )


if __name__ == "__main__":
    asyncio.run(main())
