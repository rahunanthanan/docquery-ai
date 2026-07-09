"""Review module API tests: queue RBAC, decision rules, transition
enforcement and audit writes (§4.2, §6, §7, §8)."""

import asyncio
import os
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import set_user_role
from tests.test_documents import _auth_headers
from tests.test_qa import REVENUE_DOC, _ask, _conversation, _seed_document

VALID_COMMENT = "This answer is not grounded in the cited excerpt."


def _reviewer(client: TestClient, email: str = "reviewer@example.com") -> dict[str, str]:
    headers = _auth_headers(client, email)
    set_user_role(email, "reviewer")
    return headers


def _pending_answer(client: TestClient, asker_email: str = "asker@example.com") -> str:
    asker = _auth_headers(client, asker_email)
    _seed_document(client, asker, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, asker)
    body = _ask(client, asker, conversation_id, "How much did quarterly revenue grow?")
    answer: dict[str, Any] = body["answer"]  # type: ignore[assignment]
    answer_id: str = answer["id"]
    return answer_id


def _decide(
    client: TestClient, headers: dict[str, str], answer_id: str, decision: str, **extra: str
) -> Any:
    return client.post(
        f"/api/v1/review/{answer_id}/decision",
        headers=headers,
        json={"decision": decision, **extra},
    )


def _audit_rows(entity_id: str) -> list[tuple[str, str, dict[str, Any]]]:
    async def go() -> list[tuple[str, str, dict[str, Any]]]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT action, actor_email, metadata FROM audit_events "
                    "WHERE entity_id = :id ORDER BY id"
                ),
                {"id": entity_id},
            )
            rows = [(r[0], r[1], r[2]) for r in result]
        await engine.dispose()
        return rows

    return asyncio.run(go())


# ── access control ────────────────────────────────────────────────────────


def test_queue_requires_reviewer_role(client: TestClient) -> None:
    user = _auth_headers(client, "plain@example.com")
    response = client.get("/api/v1/review/queue", headers=user)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert client.get("/api/v1/review/queue").status_code == 401


def test_admin_can_access_queue(client: TestClient) -> None:
    admin = _auth_headers(client, "admin@example.com")
    set_user_role("admin@example.com", "admin")
    assert client.get("/api/v1/review/queue", headers=admin).status_code == 200


# ── queue ─────────────────────────────────────────────────────────────────


def test_queue_shows_all_users_answers_with_allowed_decisions(client: TestClient) -> None:
    answer_id = _pending_answer(client)  # asked by asker@, reviewed by reviewer@
    reviewer = _reviewer(client)

    body = client.get("/api/v1/review/queue", headers=reviewer).json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["answerId"] == answer_id
    assert item["askerEmail"] == "asker@example.com"
    assert item["reviewStatus"] == "pending_review"
    assert set(item["allowedDecisions"]) == {"approved", "flagged", "rejected"}
    assert "revenue" in item["questionText"].lower()


def test_queue_status_filter(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)

    assert (
        client.get("/api/v1/review/queue?status=approved", headers=reviewer).json()["total"] == 0
    )
    _decide(client, reviewer, answer_id, "approved")
    approved = client.get("/api/v1/review/queue?status=approved", headers=reviewer).json()
    assert approved["total"] == 1
    assert approved["items"][0]["allowedDecisions"] == []  # terminal


def test_review_detail_includes_citations(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)

    response = client.get(f"/api/v1/review/{answer_id}", headers=reviewer)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answerId"] == answer_id
    assert body["askerEmail"] == "asker@example.com"
    assert set(body["allowedDecisions"]) == {"approved", "flagged", "rejected"}
    assert len(body["citations"]) >= 1
    citation = body["citations"][0]
    assert citation["marker"] == 1
    assert "revenue" in citation["snippet"].lower()
    assert citation["page"] == 1


def test_review_detail_unknown_answer_is_404(client: TestClient) -> None:
    reviewer = _reviewer(client)
    response = client.get(
        "/api/v1/review/00000000-0000-0000-0000-000000000000", headers=reviewer
    )
    assert response.status_code == 404


def test_review_detail_requires_reviewer(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    asker = _auth_headers(client, "asker@example.com")
    assert client.get(f"/api/v1/review/{answer_id}", headers=asker).status_code == 403


# ── decisions ─────────────────────────────────────────────────────────────


def test_approve_updates_answer_status(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)

    response = _decide(client, reviewer, answer_id, "approved")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["decision"] == "approved"
    assert body["reviewStatus"] == "approved"


def test_flag_then_approve_follows_lifecycle(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)

    flagged = _decide(client, reviewer, answer_id, "flagged", comment=VALID_COMMENT)
    assert flagged.status_code == 201
    assert flagged.json()["reviewStatus"] == "flagged"

    approved = _decide(client, reviewer, answer_id, "approved")
    assert approved.status_code == 201
    assert approved.json()["reviewStatus"] == "approved"


def test_terminal_states_reject_further_decisions(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)
    _decide(client, reviewer, answer_id, "approved")

    response = _decide(client, reviewer, answer_id, "rejected", comment=VALID_COMMENT)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_flag_and_reject_require_comment(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)

    for decision in ("flagged", "rejected"):
        missing = _decide(client, reviewer, answer_id, decision)
        assert missing.status_code == 422
        too_short = _decide(client, reviewer, answer_id, decision, comment="too short")
        assert too_short.status_code == 422


def test_approve_needs_no_comment_but_validates_if_present(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)
    response = _decide(client, reviewer, answer_id, "approved", comment="ok")  # 2 < 10 chars
    assert response.status_code == 422


def test_pending_review_is_not_a_valid_decision(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)
    assert _decide(client, reviewer, answer_id, "pending_review").status_code == 422


def test_decision_on_unknown_answer_is_404(client: TestClient) -> None:
    reviewer = _reviewer(client)
    response = _decide(
        client, reviewer, "00000000-0000-0000-0000-000000000000", "approved"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ANSWER_NOT_FOUND"


def test_rejected_answer_is_hidden_from_asker(client: TestClient) -> None:
    asker = _auth_headers(client, "asker@example.com")
    _seed_document(client, asker, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, asker)
    body = _ask(client, asker, conversation_id, "How much did revenue grow?")
    answer: dict[str, Any] = body["answer"]  # type: ignore[assignment]

    reviewer = _reviewer(client)
    _decide(client, reviewer, answer["id"], "rejected", comment=VALID_COMMENT)

    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=asker).json()
    shown = detail["items"][0]["answer"]
    assert shown["reviewStatus"] == "rejected"
    assert "rejected by a reviewer" in shown["content"]  # §7 notice
    assert "fourteen percent" not in shown["content"]
    assert shown["citations"] == []


def test_decision_history_is_preserved(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)
    _decide(client, reviewer, answer_id, "flagged", comment=VALID_COMMENT)
    _decide(client, reviewer, answer_id, "rejected", comment=VALID_COMMENT)

    async def go() -> int:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.connect() as conn:
            count = await conn.scalar(
                text("SELECT count(*) FROM review_decisions WHERE answer_id = :id"),
                {"id": answer_id},
            )
        await engine.dispose()
        return int(count or 0)

    assert asyncio.run(go()) == 2


# ── audit (§8) ────────────────────────────────────────────────────────────


def test_decisions_write_audit_events(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)
    _decide(client, reviewer, answer_id, "flagged", comment=VALID_COMMENT)
    _decide(client, reviewer, answer_id, "approved")

    rows = _audit_rows(answer_id)
    # the answer entity also carries an answer.generated event from the ask flow
    assert [r[0] for r in rows] == ["answer.generated", "answer.flagged", "answer.approved"]
    decisions = [r for r in rows if r[0].startswith("answer.") and r[0] != "answer.generated"]
    assert decisions[0][1] == "reviewer@example.com"
    assert decisions[0][2]["from_status"] == "pending_review"
    assert decisions[1][2]["from_status"] == "flagged"
    assert decisions[0][2]["has_comment"] is True


def test_audit_events_are_append_only(client: TestClient) -> None:
    answer_id = _pending_answer(client)
    reviewer = _reviewer(client)
    _decide(client, reviewer, answer_id, "approved")

    async def try_update() -> str:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.begin() as conn:
                await conn.execute(text("UPDATE audit_events SET action = 'tampered'"))
        except Exception as exc:
            return str(exc)
        finally:
            await engine.dispose()
        return ""

    assert "append-only" in asyncio.run(try_update())
