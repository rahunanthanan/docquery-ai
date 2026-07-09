"""Audit log query API tests (§4.2, §8)."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from tests.conftest import set_user_role
from tests.test_documents import _auth_headers, _upload
from tests.test_qa import REVENUE_DOC, _ask, _conversation, _seed_document


def _reviewer(client: TestClient, email: str = "auditor@example.com") -> dict[str, str]:
    headers = _auth_headers(client, email)
    set_user_role(email, "reviewer")
    return headers


def test_audit_requires_reviewer(client: TestClient) -> None:
    user = _auth_headers(client, "plain@example.com")
    assert client.get("/api/v1/audit", headers=user).status_code == 403
    assert client.get("/api/v1/audit").status_code == 401


def test_full_flow_emits_expected_actions(client: TestClient) -> None:
    asker = _auth_headers(client, "asker@example.com")
    _seed_document(client, asker, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, asker)
    _ask(client, asker, conversation_id, "How much did revenue grow?")
    reviewer = _reviewer(client)

    body = client.get("/api/v1/audit?limit=100", headers=reviewer).json()
    actions = {item["action"] for item in body["items"]}
    assert {
        "user.registered",
        "user.login",
        "document.uploaded",
        "question.asked",
        "answer.generated",
    } <= actions
    # newest first
    ids = [item["id"] for item in body["items"]]
    assert ids == sorted(ids, reverse=True)


def test_failed_ingestion_is_audited_as_system(client: TestClient) -> None:
    asker = _auth_headers(client, "asker@example.com")
    _upload(
        client,
        asker,
        filename="broken.docx",
        content=b"PK\x03\x04" + b"\x00" * 32,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    reviewer = _reviewer(client)
    body = client.get(
        "/api/v1/audit?action=document.processing_failed", headers=reviewer
    ).json()
    assert body["total"] == 1
    assert body["items"][0]["actorEmail"] == "system"
    assert "Ingestion failed" in body["items"][0]["metadata"]["error"]


def test_filter_by_action_and_actor(client: TestClient) -> None:
    _auth_headers(client, "alice@example.com")  # registers + logs in
    _auth_headers(client, "bob@example.com")
    reviewer = _reviewer(client)

    logins = client.get("/api/v1/audit?action=user.login", headers=reviewer).json()
    assert logins["total"] == 3  # alice, bob, auditor
    assert all(i["action"] == "user.login" for i in logins["items"])

    alice_only = client.get(
        "/api/v1/audit?actor=alice@example.com", headers=reviewer
    ).json()
    assert alice_only["total"] == 2  # registered + login
    assert all(i["actorEmail"] == "alice@example.com" for i in alice_only["items"])


def test_ip_addresses_round_trip_as_strings(client: TestClient) -> None:
    # regression: asyncpg returns inet as IPv4Address objects, not strings
    import asyncio
    import os

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    async def insert_with_ip() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO audit_events "
                    "(actor_email, action, entity_type, entity_id, ip) VALUES "
                    "('x@example.com', 'user.login', 'user', gen_random_uuid(), '10.0.0.9')"
                )
            )
        await engine.dispose()

    asyncio.run(insert_with_ip())
    reviewer = _reviewer(client)
    body = client.get("/api/v1/audit?actor=x@example.com", headers=reviewer).json()
    assert body["items"][0]["ip"] == "10.0.0.9"


def test_filter_by_entity_and_time_window(client: TestClient) -> None:
    asker = _auth_headers(client, "asker@example.com")
    _seed_document(client, asker, REVENUE_DOC, "revenue.txt")
    reviewer = _reviewer(client)

    documents = client.get("/api/v1/audit?entity=document", headers=reviewer).json()
    assert documents["total"] == 1
    assert documents["items"][0]["action"] == "document.uploaded"

    tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    future = client.get(
        "/api/v1/audit", params={"from": tomorrow}, headers=reviewer
    ).json()
    assert future["total"] == 0

    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    window = client.get(
        "/api/v1/audit", params={"from": yesterday, "to": tomorrow}, headers=reviewer
    ).json()
    assert window["total"] > 0
