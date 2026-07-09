"""Provider-agnostic LLM interfaces (§4.3).

Everything model-related sits behind these protocols so the whole app —
including CI — runs with the deterministic fake provider and zero API keys.
"""

from dataclasses import dataclass
from typing import Protocol

EMBEDDING_DIM = 1536  # §5: chunks.embedding vector(1536)


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one EMBEDDING_DIM-length unit vector per input text."""
        ...


@dataclass(frozen=True)
class ChatResult:
    content: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int


class ChatProvider(Protocol):
    async def complete(self, *, system: str, user: str) -> ChatResult:
        """Run one system+user completion and report token usage."""
        ...
