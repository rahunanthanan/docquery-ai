"""Provider selection via the LLM_PROVIDER env var (§4.3).

Embeddings always come from OpenAI's text-embedding-3-small (or the fake
provider): Anthropic offers no embeddings API, so LLM_PROVIDER=anthropic
pairs Anthropic chat with OpenAI embeddings and needs both keys.
"""

from app.core.config import get_settings
from app.core.errors import LLMProviderError
from app.llm.anthropic_provider import AnthropicChatProvider
from app.llm.base import ChatProvider, EmbeddingProvider
from app.llm.fake_provider import FakeChatProvider, FakeEmbeddingProvider
from app.llm.openai_provider import OpenAIChatProvider, OpenAIEmbeddingProvider


def _require(value: str | None, name: str) -> str:
    if not value:
        raise LLMProviderError(f"{name} is not set for the configured LLM provider.")
    return value


def get_chat_provider() -> ChatProvider:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return FakeChatProvider()
    if settings.llm_provider == "openai":
        return OpenAIChatProvider(
            api_key=_require(settings.openai_api_key, "OPENAI_API_KEY"),
            model=settings.openai_chat_model,
        )
    return AnthropicChatProvider(
        api_key=_require(settings.anthropic_api_key, "ANTHROPIC_API_KEY"),
        model=settings.anthropic_chat_model,
    )


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return FakeEmbeddingProvider()
    return OpenAIEmbeddingProvider(
        api_key=_require(settings.openai_api_key, "OPENAI_API_KEY"),
        model=settings.openai_embedding_model,
    )
