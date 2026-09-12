# Quorum — Implemented API Endpoints (Demo Note)

Date: 2026-09-12. Verified against `src/quorum/main.py`,
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

Not yet implemented: analysis/security/tests/coverage/reviews/chat
endpoints (roadmap Phase 15 remainder, Phase 17).
