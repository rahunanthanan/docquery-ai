"""Provider-agnostic LLM interfaces (§4.3).

Everything model-related sits behind these protocols so the whole app —
including CI — runs with the deterministic fake provider and zero API keys.
Chat/completion protocols join in Task 6.
"""

from typing import Protocol

EMBEDDING_DIM = 1536  # §5: chunks.embedding vector(1536)


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one EMBEDDING_DIM-length unit vector per input text."""
        ...
