# Contributing

## Commit style — Conventional Commits

```
<type>(<scope>): <summary>
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`.
Scopes: `backend`, `frontend`, `infra`, `docs`.

Examples:
- `feat(backend): add JWT auth with role dependencies`
- `chore(infra): scaffold monorepo with compose and CI`

## Quality gates (must pass before pushing)

Backend (`cd backend`): `ruff check .` · `mypy` · `pytest`
Frontend (`cd frontend`): `npx next lint` · `npm run typecheck` · `npm test`

CI enforces all six on every push and PR.
