"""Shared HTTP policy for real LLM providers (§9).

30-second timeout; two retries with exponential backoff, but only on
429/5xx. Anything else — including timeouts — surfaces immediately as
LLMProviderError, which the error envelope turns into 502 LLM_UNAVAILABLE.
"""

import asyncio
from typing import Any

import httpx

from app.core.errors import LLMProviderError

TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 2


async def post_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    transport: httpx.AsyncBaseTransport | None = None,  # injectable for tests
    backoff_base: float = 1.0,
) -> dict[str, Any]:
    last_status: int | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=transport) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"LLM provider request failed ({type(exc).__name__})."
            ) from exc
        if response.status_code < 400:
            data: dict[str, Any] = response.json()
            return data
        if response.status_code != 429 and response.status_code < 500:
            raise LLMProviderError(f"LLM provider returned {response.status_code}.")
        last_status = response.status_code
        if attempt < MAX_RETRIES:
            await asyncio.sleep(backoff_base * 2**attempt)
    raise LLMProviderError(
        f"LLM provider unavailable after retries (last status {last_status})."
    )
