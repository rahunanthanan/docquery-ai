# DocQuery AI — Document Q&A & Review Assistant

**Requirement Document v1.0** · Author: Rahunanthanan Thangavel · Status: Approved for build

A production-style RAG application: users upload documents, ask questions grounded in those documents, and receive AI answers with citations. Every AI answer passes through a **human-in-the-loop review workflow** (approve / flag / reject) with a full audit trail — bringing regulated-banking review discipline to a GenAI product.

---

## 1. Product Requirement Document

### 1.1 Problem Statement
Teams working with policy documents, contracts and operational manuals waste time manually searching PDFs. Generic chatbots hallucinate and give unverifiable answers. Organisations in regulated industries cannot adopt AI answers without traceability and human oversight.

### 1.2 Solution
A self-hosted web application where:
1. Users upload documents (PDF, DOCX, TXT, MD).
2. Documents are chunked, embedded (pgvector) and indexed per workspace.
3. Users ask questions; the system retrieves relevant chunks and generates answers via OpenAI/Claude APIs with **inline citations** (document + page + snippet).
4. Reviewers audit AI answers through a review queue; every decision is logged.
5. Admins manage users, monitor token usage and cost.

### 1.3 Goals
- Grounded answers with verifiable citations (no citation → answer marked "unsupported").
- Human review workflow modelled on maker/checker patterns.
- Full audit history of uploads, questions, answers and review decisions.
- Cost visibility: token usage tracked per query and per user.

### 1.4 Non-Goals (v1)
- No fine-tuning, no multi-tenant SaaS billing, no real-time collaboration, no OCR of scanned images (text-based PDFs only), no SSO (JWT email/password only — SSO listed as roadmap).

### 1.5 Success Criteria (portfolio framing)
- Clean repo a hiring manager can run with `docker compose up`.
- Seed data + demo credentials so the app is explorable in under 2 minutes.
- CI green: lint, type-check, unit tests (frontend + backend).

---

## 2. User Roles & Permissions

| Capability | User | Reviewer | Admin |
|---|---|---|---|
| Register / login | ✅ | ✅ | ✅ |
| Upload documents to own workspace | ✅ | ✅ | ✅ |
| Delete own documents | ✅ | ✅ | ✅ |
| Ask questions / view own Q&A history | ✅ | ✅ | ✅ |
| View review queue (all answers) | ❌ | ✅ | ✅ |
| Approve / flag / reject answers | ❌ | ✅ | ✅ |
| View audit log | ❌ | ✅ (read) | ✅ |
| Manage users & roles | ❌ | ❌ | ✅ |
| View usage & cost dashboard | ❌ | ❌ | ✅ |

- Roles stored on the `users` table (`role` enum). Enforced server-side via FastAPI dependency (`require_role("reviewer")`), never trusted from the client.
- JWT access token (15 min) + refresh token (7 days, httpOnly cookie). Access token carries `sub`, `role`, `exp`.

---

## 3. Frontend Pages & Components (Next.js 14, App Router, TypeScript)

### 3.1 Routes
| Route | Page | Access |
|---|---|---|
| `/login`, `/register` | Auth pages | Public |
| `/documents` | Document library: upload, list, status, delete | User+ |
| `/documents/[id]` | Document detail: metadata, chunk count, processing status | User+ |
| `/chat` | Q&A interface: ask question, streamed answer, citation panel | User+ |
| `/chat/[conversationId]` | Existing conversation | Owner |
| `/review` | Review queue with filters (pending / flagged / all) | Reviewer+ |
| `/review/[answerId]` | Review detail: question, answer, retrieved chunks, decision form | Reviewer+ |
| `/admin/users` | User management | Admin |
| `/admin/usage` | Token/cost dashboard (charts by day, by user) | Admin |
| `/audit` | Audit log table with filters | Reviewer+ |

### 3.2 Key Components
- `DocumentUploader` — drag-drop, client-side type/size validation, progress state.
- `DocumentTable` — status badges (uploaded → processing → ready → failed).
- `ChatWindow` / `MessageBubble` / `CitationCard` — answer text with numbered citation chips; clicking a chip opens the source snippet + page number.
- `ReviewQueueTable`, `ReviewDecisionForm` (approve/flag/reject + mandatory comment on flag/reject).
- `UsageChart` (Recharts), `AuditLogTable`, `RoleGuard` wrapper, `EmptyState`, `ErrorBoundary`, `SkeletonLoader`.

### 3.3 State & Data Layer
- **TanStack Query** for server state (caching, retries, invalidation). No Redux here — deliberate: server-state-heavy app, showcases modern data-fetching patterns.
- Thin `api/` service layer (typed fetch wrappers, zod-parsed responses). Components never call `fetch` directly.
- Auth context provider reading the access token from memory; refresh via interceptor on 401.

---

## 4. Backend Modules & API Endpoints (FastAPI, Python 3.12)

### 4.1 Modules
```
auth/        # register, login, refresh, JWT utils, role dependencies
documents/   # upload, list, delete; triggers ingestion
ingestion/   # parse (pypdf, python-docx), chunk, embed, store vectors
qa/          # retrieval (pgvector similarity), prompt assembly, LLM call, citation mapping
review/      # review queue, decisions, status transitions
audit/       # append-only audit writer + query endpoints
usage/       # token/cost aggregation
users/       # admin user management
core/        # config, db session, exceptions, middleware, logging
```

### 4.2 Endpoints
| Method & Path | Purpose | Role |
|---|---|---|
| `POST /api/v1/auth/register` | Create account | Public |
| `POST /api/v1/auth/login` | Issue access + refresh tokens | Public |
| `POST /api/v1/auth/refresh` | Rotate tokens | Cookie |
| `POST /api/v1/documents` | Upload file (multipart) → 202 Accepted | User |
| `GET /api/v1/documents` | List own documents (paginated) | User |
| `GET /api/v1/documents/{id}` | Detail + processing status | Owner |
| `DELETE /api/v1/documents/{id}` | Soft-delete + remove vectors | Owner |
| `POST /api/v1/conversations` | Start conversation | User |
| `GET /api/v1/conversations` / `{id}` | List / fetch history | Owner |
| `POST /api/v1/conversations/{id}/questions` | Ask question → answer + citations | Owner |
| `GET /api/v1/review/queue?status=` | Paginated review queue | Reviewer |
| `POST /api/v1/review/{answerId}/decision` | approve / flag / reject | Reviewer |
| `GET /api/v1/audit?entity=&actor=&from=&to=` | Query audit log | Reviewer |
| `GET /api/v1/admin/users` / `PATCH .../{id}` | Manage users/roles | Admin |
| `GET /api/v1/admin/usage?groupBy=day\|user` | Token & cost stats | Admin |
| `GET /api/v1/health` | Liveness/readiness | Public |

### 4.3 RAG Pipeline (qa module)
1. Embed question (same model as ingestion, `text-embedding-3-small` or provider-agnostic interface).
2. pgvector cosine similarity, top-k = 6, filtered to the user's documents; drop chunks below similarity threshold (0.35).
3. If zero chunks pass threshold → return "no grounded answer found" (no LLM call, no hallucination).
4. Assemble prompt: system rules + numbered chunks + question. LLM behind a `LLMProvider` interface (OpenAI + Anthropic implementations, selected via env var).
5. Post-process: map `[1]`-style markers to chunk metadata → citation objects `{documentId, page, snippet}`.
6. Persist question, answer, citations, token counts, latency. Answer enters review workflow at `pending_review`.

---

## 5. Database Schema (PostgreSQL 16 + pgvector)

```sql
users(id uuid PK, email citext UNIQUE, password_hash, full_name,
      role user_role DEFAULT 'user',            -- enum: user|reviewer|admin
      is_active bool, created_at, updated_at)

documents(id uuid PK, owner_id FK users, filename, mime_type,
      size_bytes, storage_path, status doc_status,  -- uploaded|processing|ready|failed
      page_count int, error_message text NULL,
      deleted_at timestamptz NULL, created_at, updated_at)

chunks(id uuid PK, document_id FK ON DELETE CASCADE, chunk_index int,
      page_number int, content text, token_count int,
      embedding vector(1536),
      UNIQUE(document_id, chunk_index))
-- index: CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);

conversations(id uuid PK, owner_id FK users, title, created_at)

questions(id uuid PK, conversation_id FK, asked_by FK users,
      text, created_at)

answers(id uuid PK, question_id FK UNIQUE, content text,
      model_name, prompt_tokens int, completion_tokens int,
      cost_usd numeric(10,6), latency_ms int,
      review_status answer_status DEFAULT 'pending_review',
      -- enum: pending_review|approved|flagged|rejected
      created_at)

citations(id uuid PK, answer_id FK, chunk_id FK, marker int,
      similarity numeric(4,3))

review_decisions(id uuid PK, answer_id FK, reviewer_id FK users,
      decision answer_status, comment text NULL, created_at)
-- history preserved: answers.review_status = latest decision

audit_events(id bigserial PK, actor_id FK users NULL, actor_email,
      action text,            -- e.g. document.uploaded, answer.approved
      entity_type, entity_id uuid, metadata jsonb, ip inet, created_at)
-- append-only: no UPDATE/DELETE grants for the app role
```

Migrations via **Alembic**; seed script creates 3 demo users (one per role), 2 sample documents and 4 answered questions in mixed review states.

---

## 6. Validation Rules

**Backend (Pydantic v2 — source of truth):**
- Email RFC-valid, unique (409 on conflict). Password ≥ 10 chars, at least 1 letter + 1 number; hashed with bcrypt (12 rounds).
- Upload: mime whitelist (`application/pdf`, docx, `text/plain`, `text/markdown`), max 20 MB, max 25 documents per user (v1 quota). Magic-byte check, not just extension.
- Question text: 3–2,000 chars, stripped; reject if only whitespace.
- Review decision: `decision ∈ {approved, flagged, rejected}`; `comment` **required** (10–1,000 chars) when decision ≠ approved.
- All IDs validated as UUID; pagination `limit ≤ 100`.

**Frontend (zod — UX mirror, never trusted):**
- Same rules mirrored in zod schemas shared across form components; inline field errors; submit disabled while invalid or pending.

**Business rules live in the backend** (`qa/rules.py`, `review/transitions.py`) — the UI only renders what the API allows (e.g. the decision buttons come from an `allowed_decisions` field on the queue item).

---

## 7. Status Workflows

**Document lifecycle**
```
uploaded ──▶ processing ──▶ ready
                 │
                 └────▶ failed  (error_message set; retry allowed once)
```

**Answer review lifecycle**
```
pending_review ──▶ approved            (terminal)
      │
      ├──────────▶ flagged ──▶ approved | rejected   (reviewer follow-up)
      │
      └──────────▶ rejected            (terminal; answer hidden from asker's
                                        conversation view, replaced by notice)
```
Transitions enforced in `review/transitions.py` via an explicit allowed-transition map; illegal transition → 409 `INVALID_TRANSITION`.

---

## 8. Audit Logging

- Append-only `audit_events` table; DB role used by the app has INSERT/SELECT only.
- Written via a single `audit.log(actor, action, entity, metadata)` service called from route handlers (not ORM hooks — explicit is greppable).
- Logged actions: `user.registered`, `user.login`, `user.role_changed`, `document.uploaded`, `document.deleted`, `document.processing_failed`, `question.asked`, `answer.generated`, `answer.approved|flagged|rejected`.
- Metadata JSONB stores diffs/context (e.g. old_role → new_role, token counts, decision comment id). Never store raw passwords or full document text.
- `/audit` UI: filter by actor, action, entity, date range; CSV export.

---

## 9. Error Handling Strategy

**Backend**
- Central exception hierarchy: `AppError(code, http_status, message)` → subclasses `NotFoundError`, `PermissionDeniedError`, `ValidationFailed`, `InvalidTransition`, `LLMProviderError`, `QuotaExceeded`.
- Single FastAPI exception handler returns a uniform envelope:
  `{"error": {"code": "DOCUMENT_NOT_FOUND", "message": "...", "requestId": "..."}}`
- LLM calls: 30 s timeout, 2 retries with exponential backoff on 429/5xx; provider errors surface as 502 `LLM_UNAVAILABLE` — user's question is saved so nothing is lost.
- Ingestion failures mark the document `failed` with a human-readable `error_message`; never crash the request thread (ingestion runs as FastAPI `BackgroundTasks` in v1; documented upgrade path to a worker queue).
- Structured JSON logging (request id, user id, latency) via `structlog`.

**Frontend**
- Every data view has explicit loading (skeleton), empty and error states.
- TanStack Query retries idempotent GETs (2×); mutations never auto-retry.
- Global `ErrorBoundary` + toast for mutation errors, mapping API error codes to friendly copy in one `errorMessages.ts` map.
- 401 → silent refresh → retry once → redirect to `/login`.

---

## 10. Testing Strategy

| Layer | Tools | Coverage focus |
|---|---|---|
| Backend unit | Pytest | chunking logic, citation mapping, transition map, quota rules, cost calculation |
| Backend API | Pytest + httpx + test Postgres (Docker service in CI) | auth flows, RBAC on every protected route, review decision rules, uniform error envelope |
| LLM boundary | Fake `LLMProvider` implementation | pipeline tested deterministically, zero API cost in CI |
| Frontend unit | Jest + React Testing Library | `CitationCard`, `ReviewDecisionForm` validation, error-state rendering, api service parsing |
| Type safety | `mypy --strict` (backend), `tsc --noEmit` (frontend) | CI-gated |

Target: meaningful coverage of business logic (not a vanity % on boilerplate). RBAC tests parameterised across all roles × protected endpoints.

---

## 11. Folder Structure (monorepo)

```
docquery-ai/
├── README.md            ├── docker-compose.yml
├── .github/workflows/ci.yml
├── backend/
│   ├── app/
│   │   ├── main.py, core/ (config.py, db.py, security.py, errors.py, logging.py)
│   │   ├── auth/  documents/  ingestion/  qa/  review/  audit/  usage/  users/
│   │   │     └── (each: router.py, service.py, schemas.py, models.py)
│   │   └── llm/ (base.py, openai_provider.py, anthropic_provider.py, fake_provider.py)
│   ├── alembic/  tests/  scripts/seed.py
│   ├── pyproject.toml  Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/ (route groups per §3.1)
│   │   ├── components/ (ui/, documents/, chat/, review/, admin/)
│   │   ├── lib/api/ (client.ts, documents.ts, qa.ts, review.ts …)
│   │   ├── lib/schemas/ (zod)   hooks/   providers/
│   ├── __tests__/  package.json  Dockerfile
└── docs/ (screenshots/, architecture.md, api.md)
```

---

## 12. Docker Setup

`docker-compose.yml` services:
- **db** — `pgvector/pgvector:pg16`, volume, healthcheck `pg_isready`.
- **backend** — multi-stage Dockerfile (uv/pip install → slim runtime, non-root user), depends_on db healthy, runs Alembic migrations on start via entrypoint.
- **frontend** — multi-stage (deps → build → `node:20-slim` runtime, Next.js standalone output).
- `.env.example` documents every variable (`DATABASE_URL`, `JWT_SECRET`, `LLM_PROVIDER=openai|anthropic|fake`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, quotas).
- `LLM_PROVIDER=fake` lets anyone demo the app **without any API key** — big portfolio win.
- One command: `docker compose up --build` → seeded app on `localhost:3000`.

---

## 13. GitHub Actions CI (`.github/workflows/ci.yml`)

Jobs (run in parallel where possible):
1. **backend-lint-type** — ruff + mypy --strict
2. **backend-test** — Pytest with a `pgvector` service container; coverage report artifact
3. **frontend-lint-type** — eslint + `tsc --noEmit`
4. **frontend-test** — Jest
5. **docker-build** — build both images (no push) to prove Dockerfiles stay green
- Triggers: push to `main`, all PRs. Branch protection: all jobs required.
- Badge in README.

---

## 14. Step-by-Step Implementation Plan

| # | Task | Output |
|---|---|---|
| 1 | Repo scaffold, compose, .env.example, README skeleton, CI skeleton | `docker compose up` runs empty apps |
| 2 | Backend core: config, db session, error envelope, structlog, health endpoint | `/health` green |
| 3 | Auth module + users table + Alembic init + JWT + role dependencies | register/login/refresh tested |
| 4 | Documents module: upload, storage, list, delete + quotas + validation | Pytest green |
| 5 | Ingestion: parse → chunk → embed (provider interface + fake) → pgvector | seeded doc becomes `ready` |
| 6 | QA module: retrieval, prompt, LLM providers, citations, usage capture | grounded answer w/ citations |
| 7 | Review module: queue, decisions, transition map + audit writes | RBAC + transition tests |
| 8 | Audit + usage endpoints, seed script | demo data complete |
| 9 | Frontend foundation: API client, auth flow, providers, RoleGuard, layout | login works end-to-end |
| 10 | Documents UI (upload/list/detail) with loading/empty/error states | |
| 11 | Chat UI + citation panel | |
| 12 | Review queue + decision form; audit table; admin pages + usage charts | |
| 13 | Jest tests, screenshots for README, polish, final CI hardening | portfolio-ready |

Each task = one focused PR-sized commit with a conventional-commit message — the git history itself becomes part of the showcase.
