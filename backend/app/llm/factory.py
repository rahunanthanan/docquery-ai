"""Provider selection via the LLM_PROVIDER env var (§4.3)."""

from app.core.config import get_settings
from app.core.errors import LLMProviderError
from app.llm.base import EmbeddingProvider
from app.llm.fake_provider import FakeEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    provider = get_settings().llm_provider
    if provider == "fake":
        return FakeEmbeddingProvider()
    # OpenAI/Anthropic providers arrive with the QA module (Task 6).
    raise LLMProviderError(f"Embedding provider '{provider}' is not available yet.")
