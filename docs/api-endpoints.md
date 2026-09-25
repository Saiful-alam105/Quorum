# Quorum — Implemented API Endpoints (Demo Note)

Date: 2026-09-24. Verified against `src/quorum/main.py`,
`src/quorum/auth/routes.py`, `src/quorum/api/routes.py`.

Core:

- `GET /` — service info.
- `GET /health` — `{"status":"ok"}`.
- `POST /webhooks/github` — GitHub events (signature-verified).

Auth (GitHub OAuth + sessions):

- `GET /auth/login`, `GET /auth/callback`, `GET /auth/me`,
  `POST /auth/logout` (see `src/quorum/auth/`).

Dashboard read API (session-protected, user-scoped):

- `GET /api/me`
- `GET /api/repositories`
- `GET /api/repositories/{id}`
- `GET /api/repositories/{id}/pull-requests`
- `GET /api/pull-requests`
- `GET /api/pull-requests/{id}`
- `GET /api/pull-requests/{id}/analysis` — analysis runs for a PR
- `GET /api/pull-requests/{id}/security` — findings for the latest run
- `GET /api/pull-requests/{id}/tests` — test runs for the latest run
- `GET /api/pull-requests/{id}/coverage` — coverage for the latest run
- `GET /api/reviews` — analysis runs across the user's repositories
- `GET /api/reviews/{id}` — single review with findings/tests/coverage

Not yet implemented: chat endpoints (`GET`/`POST /api/reviews/{id}/chat`,
roadmap Phase 17 / Phase 16 Ask Quorum).
