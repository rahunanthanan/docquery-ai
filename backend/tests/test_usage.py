"""Admin usage/cost stats tests (§4.2)."""

from fastapi.testclient import TestClient

from tests.conftest import set_user_role
from tests.test_documents import _auth_headers
from tests.test_qa import REVENUE_DOC, _ask, _conversation, _seed_document


def _answers_for(client: TestClient, email: str, n: int) -> None:
    headers = _auth_headers(client, email)
    _seed_document(client, headers, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, headers)
    for i in range(n):
        _ask(client, headers, conversation_id, f"Question number {i}: how did revenue grow?")


def test_usage_requires_admin(client: TestClient) -> None:
    reviewer = _auth_headers(client, "reviewer@example.com")
    set_user_role("reviewer@example.com", "reviewer")
    assert client.get("/api/v1/admin/usage", headers=reviewer).status_code == 403
    assert client.get("/api/v1/admin/usage").status_code == 401


def test_usage_grouped_by_user(client: TestClient) -> None:
    _answers_for(client, "alice@example.com", 2)
    _answers_for(client, "bob@example.com", 1)
    admin = _auth_headers(client, "admin@example.com")
    set_user_role("admin@example.com", "admin")

    body = client.get("/api/v1/admin/usage?groupBy=user", headers=admin).json()
    assert body["groupBy"] == "user"
    by_key = {row["key"]: row for row in body["rows"]}
    assert by_key["alice@example.com"]["answers"] == 2
    assert by_key["bob@example.com"]["answers"] == 1
    assert all(row["promptTokens"] > 0 for row in body["rows"])
    assert body["totals"]["answers"] == 3
    assert body["totals"]["promptTokens"] == sum(r["promptTokens"] for r in body["rows"])


def test_usage_grouped_by_day(client: TestClient) -> None:
    _answers_for(client, "alice@example.com", 2)
    admin = _auth_headers(client, "admin@example.com")
    set_user_role("admin@example.com", "admin")

    body = client.get("/api/v1/admin/usage?groupBy=day", headers=admin).json()
    assert body["groupBy"] == "day"
    assert len(body["rows"]) == 1  # everything just happened today
    assert body["rows"][0]["answers"] == 2
    assert body["rows"][0]["costUsd"] == 0.0  # fake provider


def test_usage_invalid_group_by_is_422(client: TestClient) -> None:
    admin = _auth_headers(client, "admin@example.com")
    set_user_role("admin@example.com", "admin")
    assert client.get("/api/v1/admin/usage?groupBy=hour", headers=admin).status_code == 422


def test_usage_with_no_answers_is_empty(client: TestClient) -> None:
    admin = _auth_headers(client, "admin@example.com")
    set_user_role("admin@example.com", "admin")
    body = client.get("/api/v1/admin/usage", headers=admin).json()
    assert body["rows"] == [] and body["totals"]["answers"] == 0
