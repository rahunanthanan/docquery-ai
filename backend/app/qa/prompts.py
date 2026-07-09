"""Prompt assembly: system rules + numbered chunks + question (§4.3)."""

from app.qa.retrieval import RetrievedChunk

SYSTEM_PROMPT = (
    "You answer questions strictly from the provided document excerpts. "
    "Cite every claim with the bracketed number of the excerpt it comes from, "
    "like [1] or [2]. If the excerpts do not contain the answer, say that "
    "the documents do not cover it — never invent information."
)


def build_user_prompt(chunks: list[RetrievedChunk], question: str) -> str:
    numbered = "\n\n".join(f"[{i}] {chunk.content}" for i, chunk in enumerate(chunks, start=1))
    return f"Document excerpts:\n\n{numbered}\n\nQuestion: {question}"
