"""Unit tests for the §9 LLM HTTP policy: 2 retries with backoff on 429/5xx."""

import asyncio
from typing import Any

import httpx
import pytest

from app.core.errors import LLMProviderError
from app.llm.http import post_json


def _run(handler: Any) -> dict[str, Any]:
    return asyncio.run(
        post_json(
            "https://llm.example/api",
            headers={},
            payload={},
            transport=httpx.MockTransport(handler),
            backoff_base=0,  # no real sleeping in tests
        )
    )


def test_retries_5xx_then_succeeds() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    assert _run(handler) == {"ok": True}
    assert len(calls) == 3  # initial + 2 retries


def test_gives_up_after_two_retries() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503)

    with pytest.raises(LLMProviderError):
        _run(handler)
    assert len(calls) == 3


def test_429_is_retried() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(429) if len(calls) == 1 else httpx.Response(200, json={})

    assert _run(handler) == {}
    assert len(calls) == 2


def test_4xx_fails_immediately_without_retry() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401)

    with pytest.raises(LLMProviderError):
        _run(handler)
    assert len(calls) == 1


def test_network_error_surfaces_as_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(LLMProviderError):
        _run(handler)
