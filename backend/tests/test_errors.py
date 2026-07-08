"""Uniform error envelope tests (requirements §9, §10).

Every error the API can produce — AppError subclasses, framework
validation errors, router 404s and unexpected crashes — must return
{"error": {"code", "message", "requestId"}} and echo X-Request-ID.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    AppError,
    InvalidTransition,
    LLMProviderError,
    NotFoundError,
    PermissionDeniedError,
    QuotaExceeded,
    ValidationFailed,
)
from app.main import create_app


def _app_raising(exc: Exception) -> FastAPI:
    app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise exc

    @app.get("/typed")
    def typed(count: int) -> dict[str, int]:
        return {"count": count}

    return app


def _assert_envelope(body: dict[str, dict[str, str]], code: str, message: str) -> None:
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "requestId"}
    assert body["error"]["code"] == code
    assert body["error"]["message"] == message


@pytest.mark.parametrize(
    ("exc", "status", "code"),
    [
        (NotFoundError("missing thing"), 404, "NOT_FOUND"),
        (PermissionDeniedError("not yours"), 403, "PERMISSION_DENIED"),
        (ValidationFailed("bad input"), 422, "VALIDATION_FAILED"),
        (InvalidTransition("cannot approve twice"), 409, "INVALID_TRANSITION"),
        (LLMProviderError("provider down"), 502, "LLM_UNAVAILABLE"),
        (QuotaExceeded("daily limit reached"), 429, "QUOTA_EXCEEDED"),
    ],
)
def test_app_error_subclasses_map_to_envelope(exc: AppError, status: int, code: str) -> None:
    client = TestClient(_app_raising(exc))
    response = client.get("/boom")
    assert response.status_code == status
    body = response.json()
    _assert_envelope(body, code, exc.message)
    assert response.headers["x-request-id"] == body["error"]["requestId"]


def test_per_instance_code_override() -> None:
    client = TestClient(_app_raising(NotFoundError("no such doc", code="DOCUMENT_NOT_FOUND")))
    response = client.get("/boom")
    assert response.status_code == 404
    _assert_envelope(response.json(), "DOCUMENT_NOT_FOUND", "no such doc")


def test_request_validation_error_uses_envelope() -> None:
    client = TestClient(_app_raising(NotFoundError("unused")))
    response = client.get("/typed", params={"count": "not-a-number"})
    assert response.status_code == 422
    _assert_envelope(response.json(), "VALIDATION_FAILED", "Request validation failed.")


def test_unknown_path_uses_envelope() -> None:
    client = TestClient(create_app())
    response = client.get("/nope")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert set(body["error"]) == {"code", "message", "requestId"}


def test_unexpected_exception_returns_internal_error() -> None:
    client = TestClient(_app_raising(RuntimeError("boom")), raise_server_exceptions=False)
    response = client.get("/boom")
    assert response.status_code == 500
    _assert_envelope(response.json(), "INTERNAL_ERROR", "An unexpected error occurred.")
    assert "boom" not in response.text  # internals never leak to clients


def test_client_supplied_request_id_is_echoed() -> None:
    client = TestClient(_app_raising(NotFoundError("missing")))
    response = client.get("/boom", headers={"X-Request-ID": "req-abc-123"})
    assert response.headers["x-request-id"] == "req-abc-123"
    assert response.json()["error"]["requestId"] == "req-abc-123"
