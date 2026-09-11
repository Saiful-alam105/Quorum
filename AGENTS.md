# AGENTS.md

Quorum is an AI-powered GitHub Pull Request review system with a web dashboard and an evidence-grounded **Ask Quorum** chatbot. It reviews PRs with specialized AI agents (Semgrep evidence, generated tests in a Docker sandbox, measured coverage), produces a deterministic 0–100 Merge Readiness Score, and stores results in PostgreSQL. Python / FastAPI backend, React/TypeScript frontend.

## Read before modifying

- `roadmap.md` is the master instruction file for AI agents. Read it fully before any change. It defines the phased 70-day build order (Phase 0–19, roadmap §7), milestones (§24), and the final architecture (§21).
- `README.md` explains what Quorum is (product model, features, MVP scope); `roadmap.md` is the source of truth for what to build and in what order.
- Implement only the smallest incomplete task of the current phase. Never implement future phases early.

## Current state

- **Phase 0–4 complete.** FastAPI skeleton (`GET /`, `GET /health`, `POST /webhooks/github`); GitHub App + OAuth (`/auth/login`, `/auth/callback`, `/auth/me`, `/auth/logout`) with HMAC webhook verification and App private-key/JWT handling; the full GitHub API service layer (9 functions in `github/api.py` + `github/app_auth.py`); and PostgreSQL (all 8 models in `database/models.py`, Alembic migration `303b9ed314cd`, webhook persistence).
- PostgreSQL has been **verified against the real local database** (migration applied; tables/PKs/FKs confirmed). It runs on port `5432`. Do not report it as unverified.
- **Phase 16 (Quorum Web Dashboard) is being implemented early** (in parallel, after PostgreSQL) on branch `feature/web-dashboard`. Dashboard Chunks 0–8 are complete (foundation, layout/nav, read API, repositories, repository detail/PR list, login/auth, dashboard overview, PR review details, settings). The Ask Quorum UI is **intentionally deferred** until the analysis/chat backend exists — do not fake it.
- Repo layout is still the flat `src/quorum/` tree plus `frontend/`. roadmap §5 prescribes a future `backend/src/quorum/` + `frontend/` layout; inspect the existing tree before creating/moving files and do not migrate until a phase requires it.
- `src/quorum/api/` holds the dashboard REST read API (`/api/me`, `/api/repositories`, `/api/repositories/{id}`, `/api/repositories/{id}/pull-requests`, `/api/pull-requests`, `/api/pull-requests/{id}`).
- **Next backend work:** Phase 5 — Orchestrator (roadmap §7), then Phases 6–14 (the analysis pipeline). Do not build Semgrep, LLM, Docker sandbox, or agents out of order.
- No `pyproject.toml`/`setup.py`/CI yet; `frontend/package.json` exists.

## Development workflow (chunk by chunk)

All remaining phases use the same incremental loop. Never implement a whole phase at once, and never continue automatically.

```text
ONE SMALL CHUNK
    ↓
IMPLEMENT
    ↓
AUTOMATED TEST
    ↓
MANUAL TEST
    ↓
USER CONFIRMATION
    ↓
COMMIT + PUSH
    ↓
NEXT CHUNK
```

- Before coding: state the chunk objective, files to change, dependencies, and the expected manual test.
- After coding: run automated checks, report files changed and results, give exact manual testing steps, then **STOP** and wait for confirmation.
- Commit/push only when the user explicitly asks, and only the intended files.
- Do not implement future phases early; do not create fake data; do not modify unrelated files.

## Commands (Windows / PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1      # activate venv (Python 3.13.7; deps installed)
pip install -r requirements.txt   # install deps
uvicorn --app-dir src quorum.main:app --reload
pytest
```

- `uvicorn --app-dir src quorum.main:app --reload` works from the repo root without install (start from `D:\Quorum` so `.env` is found; `src` must be on the Python path for `import quorum` to work). Tests import `quorum` via a `sys.path` shim in `tests/conftest.py`; add packaging config (`pyproject.toml`/`setup.py`) when it becomes necessary (roadmap Phase 1 DoD is `uvicorn quorum.main:app`).
- `requirements.txt` is a `pip freeze`-style pinned list for the declared stack (FastAPI, uvicorn, pydantic, httpx, PyJWT, SQLAlchemy, Alembic, psycopg, pytest, pytest-cov, python-dotenv). Keep it aligned with roadmap §4; add semgrep/docker/ollama deps only in their phases.

## Hard rules (roadmap §6 do-not list, §17 frontend rules, §22 security principles)

- No overengineering: no Redis, Celery, Kafka/RabbitMQ, Kubernetes, microservices, vector DBs, or paid LLM APIs unless the roadmap explicitly requires them.
- Never execute untrusted repo code or generated tests outside the Docker sandbox.
- Never invent results: don't report tests passing, coverage deltas, or Semgrep findings that weren't actually measured.
- Keep the LLM behind an interface (`llm/ollama_provider.py`); keep context bounded — never send an entire repository to the LLM; treat repo/PR content as untrusted data (prompt-injection defense).
- The LLM must not freely choose the final Merge Readiness Score or finding severity; both require deterministic validation against evidence.
- The Ask Quorum chatbot must be grounded in the selected review only — no cross-repository/cross-review leakage, no generic ChatGPT behavior.
- Frontend talks only to FastAPI REST; it never accesses PostgreSQL, Docker, Ollama, Semgrep, or GitHub server secrets directly.
- Keep GitHub → Orchestrator → Analysis → Agents → Sandbox → Synthesis separated.
- Use FastAPI `BackgroundTasks` for background work; no external task queues.
- Git: work on `feature/*` branches, not `main`; small commits; never commit `.env`, `*.pem`/`*.key`, or local model files (`.gitignore` already covers these).