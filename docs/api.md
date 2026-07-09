# API reference

Base URL: `http://localhost:8000` · interactive docs at `/api/docs`.

## Conventions

- **JSON is camelCase** in both directions (`fullName`, `reviewStatus`).
- **Auth**: `Authorization: Bearer <access token>`; the refresh token rides an
  httpOnly cookie scoped to `/api/v1/auth`.
- **Roles** form a hierarchy: `user < reviewer < admin` — a required role
  admits every role above it. Roles are re-read from the database on every
  request.
- **Pagination**: `limit` (≤ 100) and `offset`; responses carry
  `items`, `total`, `limit`, `offset`.
- **Errors** always use one envelope:

```json
{ "error": { "code": "DOCUMENT_NOT_FOUND", "message": "Document not found.", "requestId": "…" } }
```

Common codes: `VALIDATION_FAILED` 422 · `NOT_AUTHENTICATED` / `TOKEN_EXPIRED` /
`UNAUTHORIZED` 401 · `PERMISSION_DENIED` 403 · `NOT_FOUND` 404 ·
`CONFLICT` 409 · `INVALID_TRANSITION` 409 · `QUOTA_EXCEEDED` 429 ·
`LLM_UNAVAILABLE` 502 · `INTERNAL_ERROR` 500.

## Endpoints

### Auth (public)

| Method & path | Purpose | Notes |
|---|---|---|
| `POST /api/v1/auth/register` | Create account → 201 user | password ≥ 10 chars, letter + number; duplicate email → 409 `EMAIL_ALREADY_REGISTERED` (case-insensitive) |
| `POST /api/v1/auth/login` | → access token + user; sets refresh cookie | wrong credentials → 401 `INVALID_CREDENTIALS`; disabled → `ACCOUNT_DISABLED` |
| `POST /api/v1/auth/refresh` | Rotate tokens (cookie) | new access token + rotated cookie |
| `POST /api/v1/auth/logout` | 204; clears the refresh cookie | |

### Documents (user+)

| Method & path | Purpose | Notes |
|---|---|---|
| `POST /api/v1/documents` | Multipart upload → 202 | PDF/DOCX/TXT/MD, magic-byte checked, ≤ 20 MB, ≤ 25 docs/user (429); triggers ingestion |
| `GET /api/v1/documents` | Own documents, paginated | newest first |
| `GET /api/v1/documents/{id}` | Detail + `chunkCount` | owner-scoped; foreign/missing → 404 `DOCUMENT_NOT_FOUND` |
| `DELETE /api/v1/documents/{id}` | 204; soft delete + vector removal | |

Document `status`: `uploaded → processing → ready | failed` (with
`errorMessage`).

### Q&A (user+)

| Method & path | Purpose | Notes |
|---|---|---|
| `POST /api/v1/conversations` | Start conversation → 201 | optional `title` (≤ 200) |
| `GET /api/v1/conversations` | Own conversations, paginated | |
| `GET /api/v1/conversations/{id}` | Full history | rejected answers masked with a notice |
| `POST /api/v1/conversations/{id}/questions` | Ask → 201 `{question, answer, notice}` | text 3–2,000 chars; `answer: null` + notice when nothing grounds; question survives LLM failures (502) |

Answers carry `citations[]` (`marker`, `documentId`, `page`, `snippet`,
`similarity`), token counts, `costUsd`, `latencyMs` and `reviewStatus`
(starts at `pending_review`).

### Review (reviewer+)

| Method & path | Purpose | Notes |
|---|---|---|
| `GET /api/v1/review/queue?status=` | All users' answers, paginated | items include `allowedDecisions` |
| `GET /api/v1/review/{answerId}` | Detail incl. cited chunks | |
| `POST /api/v1/review/{answerId}/decision` | approve / flag / reject → 201 | comment 10–1,000 required unless approving; illegal transition → 409 |

Lifecycle: `pending_review → approved | flagged | rejected`;
`flagged → approved | rejected`; `approved`/`rejected` are terminal.

### Audit (reviewer+)

| Method & path | Purpose | Notes |
|---|---|---|
| `GET /api/v1/audit?entity=&actor=&action=&from=&to=` | Query append-only log | newest first, paginated |

Logged actions: `user.registered`, `user.login`, `user.role_changed`,
`user.deactivated`/`user.reactivated`, `document.uploaded`,
`document.deleted`, `document.processing_failed`, `question.asked`,
`answer.generated`, `answer.approved|flagged|rejected`.

### Admin (admin)

| Method & path | Purpose | Notes |
|---|---|---|
| `GET /api/v1/admin/users` | List accounts, paginated | |
| `PATCH /api/v1/admin/users/{id}` | Change `role` / `isActive` | self-modification → 422 `CANNOT_MODIFY_SELF` |
| `GET /api/v1/admin/usage?groupBy=day\|user` | Token & cost stats | rows + totals |

### System (public)

| Method & path | Purpose |
|---|---|
| `GET /api/v1/health` | Liveness: status, environment, LLM provider |
