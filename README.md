# DocQuery AI

![CI](https://github.com/rahunanthanan/docquery-ai/actions/workflows/ci.yml/badge.svg)

**A production-style RAG document Q&A and review assistant.** Upload documents, ask questions, and get AI answers grounded in your files with inline citations — with a **human-in-the-loop review workflow** (approve / flag / reject), an **append-only audit trail**, role-based access control, Docker packaging and a full CI pipeline.

Built to demonstrate how the review and audit discipline of regulated banking platforms applies to GenAI products.

## Stack

| Layer    | Technology                                                                           |
| -------- | ------------------------------------------------------------------------------------ |
| Frontend | Next.js 15 (App Router), React 19, TypeScript (strict)                               |
| Backend  | FastAPI, Python 3.12, Pydantic v2                                                    |
| Database | PostgreSQL 17 + pgvector                                                             |
| AI       | Provider-agnostic LLM interface — OpenAI, Anthropic, or a built-in `fake` provider   |
| Infra    | Docker Compose, GitHub Actions CI                                                    |
| Quality  | ruff, mypy `--strict`, pytest · eslint, `tsc --noEmit`, Jest + React Testing Library |

> **No API keys required to run.** The default `LLM_PROVIDER=fake` serves deterministic responses so the whole app is explorable — and testable in CI — without OpenAI or Anthropic credentials.

## Quick start

Prerequisites: Docker + Docker Compose.

```bash
git clone https://github.com/rahunanthanan/docquery-ai.git
cd docquery-ai
cp .env.example .env
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend API docs → http://localhost:8000/api/docs
- Health check → http://localhost:8000/api/v1/health

## Local development (without Docker)

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload        # http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

Quality gates:

```bash
cd backend  && ruff check . && mypy && pytest
cd frontend && npx next lint && npm run typecheck && npm test
```

## Project status & roadmap

This repository is built incrementally in reviewable, commit-sized tasks (see [CONTRIBUTING.md](CONTRIBUTING.md) for conventions).

- [x] **Task 1 — Scaffold**: monorepo, Docker Compose, CI, quality tooling
- [ ] Task 2 — Backend core: error envelope, structured logging
- [ ] Task 3 — Auth: JWT, refresh tokens, RBAC (user / reviewer / admin)
- [ ] Task 4 — Document upload & storage with quotas
- [ ] Task 5 — Ingestion: parse → chunk → embed → pgvector
- [ ] Task 6 — RAG Q&A with citations and cost tracking
- [ ] Task 7 — Human review workflow with status transitions
- [ ] Task 8 — Audit log & usage dashboard APIs, seed data
- [ ] Tasks 9–13 — Frontend features: documents, chat, review queue, admin

### Task 1 acceptance checklist

- [x] `docker compose up --build` starts frontend, backend and database
- [x] Frontend opens at `localhost:3000`
- [x] Backend starts without errors (`/api/v1/health` returns `ok`)
- [x] Database container reports healthy (`pg_isready` healthcheck)
- [x] `.env.example` documents every variable; local defaults work out of the box
- [x] CI workflow exists (backend + frontend + docker-build jobs)
- [x] README has setup instructions
- [x] No secrets committed (`.env` git-ignored; only `.env.example` tracked)

## Screenshots

_Screenshots will be added as features land (see `docs/screenshots/`)._

## Architecture notes

- **Monorepo**: `backend/` and `frontend/` are independent deployables sharing one compose file and one CI pipeline with per-app jobs.
- **Config as code**: every environment variable is declared in `backend/app/core/config.py` (Pydantic Settings) and mirrored in `.env.example` — no hidden knobs.
- **Non-root containers**: both Dockerfiles are multi-stage builds running as unprivileged users; the frontend ships Next.js standalone output for a minimal runtime image.

## License

MIT
