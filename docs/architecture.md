# Architecture

DocQuery AI is a RAG document Q&A service with a human review workflow and an
append-only audit trail. Two deployables (FastAPI backend, Next.js frontend)
share one Postgres + pgvector database and one Docker Compose file.

```
┌──────────────┐   camelCase JSON    ┌──────────────────────────────┐
│  Next.js 15  │ ──────────────────▶ │  FastAPI                     │
│  App Router  │   Bearer access +   │  auth · documents · qa       │
│  TanStack Q  │   httpOnly refresh  │  ingestion · review · audit  │
└──────────────┘                     │  users · usage · llm · core  │
                                     └───────┬──────────────┬───────┘
                                             │              │
                                    ┌────────▼───────┐  ┌───▼───────────────┐
                                    │ Postgres 17 +  │  │ LLMProvider       │
                                    │ pgvector (HNSW)│  │ fake│openai│      │
                                    └────────────────┘  │ anthropic         │
                                                        └───────────────────┘
```

## Request lifecycle (backend)

1. **Request-context middleware** binds a request id (client `X-Request-ID` or
   generated) into structlog contextvars and echoes it on the response; every
   log line is one JSON object with method/path/status/latency.
2. **Routing → dependency layer.** `get_current_user` decodes the access token
   and re-reads the user row (role and active status are never trusted from
   the token); `require_role(min)` enforces the user < reviewer < admin
   hierarchy.
3. **Service layer** holds all business logic; routers stay thin. Audit rows
   are staged by services and committed in the same transaction as the domain
   change they record.
4. **One error envelope.** Every failure — `AppError` subclasses, validation
   errors, router 404s, unexpected crashes — becomes
   `{"error": {"code", "message", "requestId"}}` via central handlers.

## Auth model

- Access token: JWT, 15 min, carries `sub`/`role`/`exp`/`jti`, held in
  frontend memory only.
- Refresh token: JWT (7 days) in an httpOnly cookie scoped to
  `/api/v1/auth`, rotated on every refresh. Logout clears the cookie.
- The frontend API client silently refreshes once on 401, then redirects to
  `/login` (§9); auth endpoints are excluded from the refresh loop.

## RAG pipeline

```
upload ──▶ BackgroundTasks: parse (pypdf/docx/text) ─▶ chunk (1200 chars,
           200 overlap) ─▶ embed (provider) ─▶ chunks table (vector 1536)
           status: uploaded → processing → ready | failed(error_message)

ask ──▶ question saved FIRST ─▶ embed question ─▶ pgvector cosine top-6,
        owner-scoped, ≥ 0.35 ─▶ zero hits: notice, no LLM call
        ─▶ prompt = system rules + numbered excerpts + question
        ─▶ ChatProvider (30s timeout, 2 retries on 429/5xx)
        ─▶ [n] markers → citations {chunk, marker, similarity}
        ─▶ answer persisted at pending_review with tokens/cost/latency
```

Saving the question before any LLM work means a provider outage (502
`LLM_UNAVAILABLE`) never loses user input.

**Provider abstraction:** `EmbeddingProvider` and `ChatProvider` protocols with
OpenAI, Anthropic and deterministic fake implementations, selected by
`LLM_PROVIDER`. The fake provider makes the entire app — and CI — run with
zero API keys: embeddings are bag-of-words vectors around a shared base
direction (lexical overlap ranks first), and chat echoes the top excerpt with
citation markers. Anthropic has no embeddings API, so Anthropic chat pairs
with OpenAI embeddings.

## Review & audit

- Answer lifecycle is an explicit transition map
  (`review/transitions.py`): `pending_review → approved | flagged | rejected`,
  `flagged → approved | rejected`; illegal moves → 409 `INVALID_TRANSITION`.
  The queue exposes `allowedDecisions` so the UI renders only legal actions.
- Every decision keeps its `review_decisions` row (history preserved) and
  writes an audit event in the same transaction.
- `audit_events` is append-only, enforced by a database trigger that rejects
  UPDATE/DELETE — stronger than role grants, since the dev app connects as
  the table owner. Rejected answers are masked from the asker's view.

## Storage & operations

- Files live under `UPLOAD_DIR` at `{owner_id}/{document_id}.{ext}` — the
  user-supplied filename is display-only metadata, so path traversal is
  impossible by construction. Soft delete + immediate vector removal.
- Migrations (Alembic, async) and the idempotent demo seed run on container
  start: `docker compose up --build` yields a working, seeded app.
- **Worker-queue upgrade path:** ingestion runs via FastAPI BackgroundTasks in
  v1. `ingest_document(document_id)` owns its session and takes only an id,
  so moving it behind arq/Celery changes a single dispatch site.

## Testing

- Backend API tests run against a real Postgres (`docquery_test`, recreated
  and migrated by Alembic per session) — no mocked DB. RBAC is parameterised
  across all roles × endpoints; the LLM boundary is tested with the fake
  provider and an httpx MockTransport for the retry policy.
- Frontend: Jest + RTL for the API client (refresh/envelope behavior), form
  validation, citation rendering and error states.
- Gates on every push: ruff, mypy --strict, pytest (coverage artifact),
  eslint, tsc --noEmit, Jest, and both Docker builds.
