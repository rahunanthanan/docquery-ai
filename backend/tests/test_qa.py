"""QA module API tests: conversations, the RAG ask flow, citations, usage
capture and failure modes (§4.2, §4.3, §6, §9)."""

import pytest
from fastapi.testclient import TestClient

from app.core.errors import LLMProviderError
from app.llm.base import ChatResult
from tests.test_documents import _auth_headers, _upload

REVENUE_DOC = (
    b"Quarterly revenue grew fourteen percent year over year, driven by "
    b"subscription renewals and enterprise expansion deals."
)
CAT_DOC = b"The cat sat on the mat while the dog slept by the fireplace."


def _conversation(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/conversations", headers=headers, json={})
    assert response.status_code == 201, response.text
    conversation_id: str = response.json()["id"]
    return conversation_id


def _ask(
    client: TestClient, headers: dict[str, str], conversation_id: str, text: str
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/questions", headers=headers, json={"text": text}
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


def _seed_document(client: TestClient, headers: dict[str, str], content: bytes, name: str) -> str:
    doc = _upload(client, headers, filename=name, content=content, mime="text/plain").json()
    detail = client.get(f"/api/v1/documents/{doc['id']}", headers=headers).json()
    assert detail["status"] == "ready"
    document_id: str = doc["id"]
    return document_id


# ── conversations ─────────────────────────────────────────────────────────


def test_create_conversation_with_default_title(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = client.post("/api/v1/conversations", headers=headers, json={})
    assert response.status_code == 201
    assert response.json()["title"] == "New conversation"


def test_create_conversation_with_custom_title(client: TestClient) -> None:
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/conversations", headers=headers, json={"title": "  Budget questions  "}
    )
    assert response.json()["title"] == "Budget questions"


def test_list_conversations_is_owner_scoped(client: TestClient) -> None:
    mine = _auth_headers(client, "mine@example.com")
    other = _auth_headers(client, "other@example.com")
    _conversation(client, mine)
    assert client.get("/api/v1/conversations", headers=mine).json()["total"] == 1
    assert client.get("/api/v1/conversations", headers=other).json()["total"] == 0


def test_foreign_conversation_is_404(client: TestClient) -> None:
    owner = _auth_headers(client, "owner@example.com")
    other = _auth_headers(client, "other@example.com")
    conversation_id = _conversation(client, owner)
    response = client.get(f"/api/v1/conversations/{conversation_id}", headers=other)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


# ── ask: grounded path ────────────────────────────────────────────────────


def test_ask_returns_grounded_answer_with_citations(client: TestClient) -> None:
    headers = _auth_headers(client)
    document_id = _seed_document(client, headers, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, headers)

    body = _ask(client, headers, conversation_id, "How much did quarterly revenue grow?")
    answer = body["answer"]
    assert body["notice"] is None
    assert answer is not None
    assert "[1]" in answer["content"]
    assert answer["reviewStatus"] == "pending_review"  # §4.3 step 6
    assert answer["modelName"] == "fake-chat"
    assert answer["promptTokens"] > 0 and answer["completionTokens"] > 0
    assert answer["costUsd"] == 0.0  # fake provider is free
    assert answer["latencyMs"] >= 0

    citations = answer["citations"]
    assert len(citations) >= 1
    assert citations[0]["marker"] == 1
    assert citations[0]["documentId"] == document_id
    assert citations[0]["page"] == 1
    assert "revenue" in citations[0]["snippet"].lower()
    assert 0.35 <= citations[0]["similarity"] <= 1.0


def test_retrieval_ranks_lexically_relevant_document_first(client: TestClient) -> None:
    headers = _auth_headers(client)
    revenue_id = _seed_document(client, headers, REVENUE_DOC, "revenue.txt")
    _seed_document(client, headers, CAT_DOC, "cats.txt")
    conversation_id = _conversation(client, headers)

    body = _ask(
        client, headers, conversation_id, "What drove quarterly revenue growth this year?"
    )
    top_citation = body["answer"]["citations"][0]
    assert top_citation["documentId"] == revenue_id


def test_ask_never_retrieves_other_users_documents(client: TestClient) -> None:
    owner = _auth_headers(client, "owner@example.com")
    asker = _auth_headers(client, "asker@example.com")
    _seed_document(client, owner, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, asker)

    body = _ask(client, asker, conversation_id, "How much did quarterly revenue grow?")
    assert body["answer"] is None  # asker has no documents → nothing to ground on
    assert body["notice"] == "No grounded answer was found in your documents."


def test_history_returns_questions_answers_and_citations(client: TestClient) -> None:
    headers = _auth_headers(client)
    _seed_document(client, headers, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, headers)
    _ask(client, headers, conversation_id, "How much did revenue grow?")

    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=headers).json()
    assert len(detail["items"]) == 1
    item = detail["items"][0]
    assert item["question"]["text"] == "How much did revenue grow?"
    assert item["answer"]["citations"][0]["marker"] == 1


# ── ask: ungrounded and failure paths ─────────────────────────────────────


def test_no_documents_means_notice_and_saved_question(client: TestClient) -> None:
    headers = _auth_headers(client)
    conversation_id = _conversation(client, headers)

    body = _ask(client, headers, conversation_id, "What does the report say?")
    assert body["answer"] is None
    assert body["notice"] == "No grounded answer was found in your documents."

    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=headers).json()
    assert len(detail["items"]) == 1  # question persisted
    assert detail["items"][0]["answer"] is None


def test_llm_failure_returns_502_and_keeps_question(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ExplodingChatProvider:
        async def complete(self, *, system: str, user: str) -> ChatResult:
            raise LLMProviderError("provider is down")

    monkeypatch.setattr("app.qa.service.get_chat_provider", ExplodingChatProvider)

    headers = _auth_headers(client)
    _seed_document(client, headers, REVENUE_DOC, "revenue.txt")
    conversation_id = _conversation(client, headers)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/questions",
        headers=headers,
        json={"text": "How much did revenue grow?"},
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_UNAVAILABLE"

    # §9: the question was saved before the LLM call, so nothing is lost
    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=headers).json()
    assert len(detail["items"]) == 1
    assert detail["items"][0]["answer"] is None


def test_ask_on_foreign_conversation_is_404(client: TestClient) -> None:
    owner = _auth_headers(client, "owner@example.com")
    other = _auth_headers(client, "other@example.com")
    conversation_id = _conversation(client, owner)
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/questions",
        headers=other,
        json={"text": "Can I read this?"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("text", ["hi", "   ", "x" * 2001])
def test_question_text_validation(client: TestClient, text: str) -> None:
    headers = _auth_headers(client)
    conversation_id = _conversation(client, headers)
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/questions", headers=headers, json={"text": text}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_conversations_require_auth(client: TestClient) -> None:
    assert client.post("/api/v1/conversations", json={}).status_code == 401
    assert client.get("/api/v1/conversations").status_code == 401
