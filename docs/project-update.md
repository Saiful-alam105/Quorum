# Quorum — Project Update

Date: 2026-09-12

This is a status-only update for a university project review. It describes
only what is currently present in the repository. No unfinished features
are claimed as completed.

## Current Progress

- Phase 0–4 are completed/working (per `roadmap.md` §7 status table and
  `README.md` "Current Status"):
  - Phase 1 FastAPI skeleton, Phase 2 GitHub App + Authentication,
    Phase 3 GitHub API layer, Phase 4 PostgreSQL.
  - Phase 0 is partially implemented (repo, Python env, FastAPI structure,
    README/roadmap, `.env.example`, `.gitignore`, `requirements.txt` exist;
    Docker/Ollama/local model/CI are still pending).
- GitHub App/OAuth functionality is implemented:
  - OAuth login/callback/me/logout (`src/quorum/auth/`).
  - App private-key/JWT handling (`src/quorum/github/app_auth.py`).
  - Webhook HMAC signature verification (`src/quorum/github/webhook.py`).
- PostgreSQL integration is implemented and verified:
  - All 8 models in `src/quorum/database/models.py`
    (`users`, `repositories`, `pull_requests`, `analysis_runs`,
    `security_findings`, `test_runs`, `coverage_results`, `chat_messages`).
  - Alembic migration `303b9ed314cd` applied against the local database
    on port `5432`; tables/PKs/FKs confirmed.
  - Webhook persistence (`pull_request` / `installation` events) is stored
    via `src/quorum/database/repository.py`.
- Web Dashboard development has progressed through the currently completed
  dashboard chunks (Chunks 0–8 on `feature/web-dashboard`):
  - Foundation, layout/nav, read API, repositories, repository detail/PR list,
    login/auth, dashboard overview, PR review details, settings.
  - The Ask Quorum UI is intentionally deferred until the analysis/chat
    backend exists; the route shows an honest "not available yet" state.
- Remaining work includes the analysis pipeline (Phases 5–8, 13–14),
  agents/LLM/sandbox (Phases 9–12), Ask Quorum backend (Phase 17),
  and remaining roadmap phases (evaluation, hardening/final demo).

## Working Features

Verified against the current tree (`src/quorum/`, `frontend/`, `tests/`):

- FastAPI backend (`src/quorum/main.py`):
  - `GET /`, `GET /health`, `POST /webhooks/github`.
- GitHub webhook handling (`POST /webhooks/github`):
  - `ping`, `pull_request`, `installation`, `installation_repositories` events;
    PR persistence on `opened` / `reopened` / `synchronize`.
- Webhook signature verification (HMAC, `src/quorum/github/webhook.py`).
- GitHub App authentication (private-key loading + JWT,
  `src/quorum/github/app_auth.py`).
- GitHub OAuth login (`src/quorum/auth/routes.py`,
  `src/quorum/auth/github_oauth.py`):
  - `/auth/login`, `/auth/callback`, `/auth/me`, `/auth/logout`.
- Session handling (`src/quorum/auth/sessions.py`).
- GitHub API service layer (`src/quorum/github/api.py`, 9 functions):
  - `get_installation_token`, `get_authenticated_user`, `get_repositories`,
    `get_repository`, `get_pull_request`, `get_pr_files`, `get_pr_diff`,
    `get_pr_comments`, `create_pr_comment`.
- PostgreSQL persistence (SQLAlchemy + Alembic):
  - Models, migration `303b9ed314cd`, webhook persistence.
- React/Vite dashboard (`frontend/`, React + TypeScript + Vite +
  Tailwind CSS + shadcn/ui).
- Dashboard read API used by the frontend (`src/quorum/api/routes.py`):
  - `GET /api/me`, `GET /api/repositories`, `GET /api/repositories/{id}`,
    `GET /api/repositories/{id}/pull-requests`, `GET /api/pull-requests`,
    `GET /api/pull-requests/{id}`.
- Dashboard pages actually implemented (`frontend/src/App.tsx` routes):
  - `/login` (Login), `/` (Dashboard overview), `/repositories`
    (Repositories), `/repositories/:repositoryId` (Repository detail / PR list),
    `/pull-requests` (Pull Requests), `/pull-requests/:pullRequestId`
    (PR review details: real PR metadata; review/summary, security findings,
    generated tests, coverage, and changed-files sections show honest
    "not yet available" states), `/reviews` (Review history),
    `/settings` (Settings).
  - `/ask-quorum` exists only as an intentional deferred placeholder
    ("Ask Quorum is not available yet"); no chatbot backend is claimed.

Not yet implemented: orchestrator, diff/AST analysis, Semgrep stage, LLM
layer (`llm/ollama_provider.py`), Security/Test Writer agents, Docker
sandbox, synthesis/Merge Readiness Score, GitHub review comment posting,
analysis/security/tests/coverage/chat API endpoints, and evaluation harness.

## Current Architecture

Small high-level view of what exists today. No new architecture is introduced.

```text
GitHub
↓
FastAPI
↓
Quorum Backend
↓
PostgreSQL
↓
FastAPI REST API
↓
React Web Dashboard
```

Notes:

- The frontend talks only to the FastAPI REST API.
- It never accesses PostgreSQL, Docker, Ollama, Semgrep, or GitHub server
  secrets directly.
- GitHub OAuth answers "who is this user?"; GitHub App
  installation/authorization answers "which repositories can Quorum analyze?".

## Current Development Status

The project is being developed incrementally:

- One roadmap phase at a time (roadmap §7 order; Phase 16 dashboard work is
  being done early in parallel after PostgreSQL, on `feature/web-dashboard`).
- Large phases are divided into small chunks.
- Each chunk is automated-tested (`pytest`; frontend `npm run build` typecheck).
- Each chunk is manually tested (backend/frontend verify steps in `README.md`).
- Completed chunks are committed/pushed before continuing.
- Only the smallest incomplete task of the current phase is implemented;
  future phases are not built early and no fake data is added.

## Next Planned Work

Per `roadmap.md` §7, the actual next backend phase is:

- Phase 5 — Orchestrator (Days 15–17): the core pipeline entry point
  (`PR → Orchestrator → Diff/AST → Context Builder → Security Agent →
  Test Writer Agent → Synthesis`), using FastAPI background execution and no
  distributed task queue unless later required.

This document does not implement it.
