"""Seed script tests: idempotent demo data in the promised shape (§5, §12)."""

import asyncio

from fastapi.testclient import TestClient

from scripts.seed import DEMO_PASSWORD
from scripts.seed import main as seed_main


def _seed() -> None:
    asyncio.run(seed_main())


def test_seed_creates_demo_data_and_is_idempotent(client: TestClient) -> None:
    _seed()
    _seed()  # second run must be a no-op

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.docquery", "password": DEMO_PASSWORD},
    )
    assert login.status_code == 200, login.text
    admin = {"Authorization": f"Bearer {login.json()['accessToken']}"}

    users = client.get("/api/v1/admin/users?limit=100", headers=admin).json()
    assert users["total"] == 3
    assert {u["role"] for u in users["items"]} == {"user", "reviewer", "admin"}

    queue = client.get("/api/v1/review/queue?limit=100", headers=admin).json()
    assert queue["total"] == 4
    statuses = {i["reviewStatus"] for i in queue["items"]}
    assert statuses == {"approved", "flagged", "rejected", "pending_review"}


def test_seeded_documents_are_ready_and_queryable(client: TestClient) -> None:
    _seed()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@demo.docquery", "password": DEMO_PASSWORD},
    )
    demo = {"Authorization": f"Bearer {login.json()['accessToken']}"}

    documents = client.get("/api/v1/documents", headers=demo).json()
    assert documents["total"] == 2
    assert all(d["status"] == "ready" for d in documents["items"])

    conversations = client.get("/api/v1/conversations", headers=demo).json()
    assert conversations["total"] == 1
    detail = client.get(
        f"/api/v1/conversations/{conversations['items'][0]['id']}", headers=demo
    ).json()
    assert len(detail["items"]) == 4

    # the demo user can keep asking questions against the seeded documents
    response = client.post(
        f"/api/v1/conversations/{conversations['items'][0]['id']}/questions",
        headers=demo,
        json={"text": "What was said about headcount growth?"},
    )
    assert response.status_code == 201
    assert response.json()["answer"] is not None
