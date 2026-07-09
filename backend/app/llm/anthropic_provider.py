"""Anthropic chat provider (§4.3).

Anthropic has no embeddings API — embeddings stay on OpenAI (or the fake
provider); see llm/factory.py.
"""

from app.llm.base import ChatResult
from app.llm.http import post_json

_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
_MAX_TOKENS = 1024


class AnthropicChatProvider:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        self._model = model

    async def complete(self, *, system: str, user: str) -> ChatResult:
        data = await post_json(
            _MESSAGES_URL,
            headers=self._headers,
            payload={
                "model": self._model,
                "max_tokens": _MAX_TOKENS,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        content = "".join(
            block["text"] for block in data["content"] if block["type"] == "text"
        )
        return ChatResult(
            content=content,
            model_name=self._model,
            prompt_tokens=data["usage"]["input_tokens"],
            completion_tokens=data["usage"]["output_tokens"],
        )
