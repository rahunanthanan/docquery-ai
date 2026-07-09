"""OpenAI chat + embedding providers (§4.3)."""

from app.llm.base import ChatResult
from app.llm.http import post_json

_CHAT_URL = "https://api.openai.com/v1/chat/completions"
_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"


class OpenAIChatProvider:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._model = model

    async def complete(self, *, system: str, user: str) -> ChatResult:
        data = await post_json(
            _CHAT_URL,
            headers=self._headers,
            payload={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        return ChatResult(
            content=data["choices"][0]["message"]["content"],
            model_name=self._model,
            prompt_tokens=data["usage"]["prompt_tokens"],
            completion_tokens=data["usage"]["completion_tokens"],
        )


class OpenAIEmbeddingProvider:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        data = await post_json(
            _EMBEDDINGS_URL,
            headers=self._headers,
            payload={"model": self._model, "input": texts},
        )
        return [item["embedding"] for item in data["data"]]
