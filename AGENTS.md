# AGENTS.md

Quorum is an AI-powered GitHub Pull Request review system with a web dashboard and an evidence-grounded **Ask Quorum** chatbot. It reviews PRs with specialized AI agents (Semgrep evidence, generated tests in a Docker sandbox, measured coverage), produces a deterministic 0–100 Merge Readiness Score, and stores results in PostgreSQL. Python / FastAPI backend, React/TypeScript frontend.

## Read before modifying

- `roadmap.md` is the master instruction file for AI agents. Read it fully before any change. It defines the phased 70-day build order (Phase 0–19, roadmap §7), milestones (§24), and the final architecture (§21).
- `README.md` explains what Quorum is (product model, features, MVP scope); `roadmap.md` is the source of truth for what to build and in what order.
- Implement only the smallest incomplete task of the current phase. Never implement future phases early.

## Current state

- Phase 0 (Project Setup) is complete. Phase 1 (FastAPI Skeleton) is implemented and tested: `GET /`, `GET /health`, `POST /webhooks/github` with HMAC signature verification, `src/quorum/config.py` (reads `GITHUB_WEBHOOK_SECRET`), and tests (13 passing).
- Repo layout is still the flat `src/quorum/` tree. roadmap §5 prescribes `backend/src/quorum/` + `frontend/`; inspect the existing tree before creating/moving files and do not migrate until the phase that requires it.
- No `pyproject.toml`/`setup.py`/CI/`package.json`/`frontend/` exist yet. `.env.example` defines `GITHUB_WEBHOOK_SECRET`; `proposal.md` is empty.
- Next task (Phase 2 — GitHub App + Authentication, roadmap §7): GitHub App registration, webhook secret/private key handling, minimum repo permissions, GitHub login + App authorization flow for the dashboard. Signature verification is already done. Do not build Semgrep, LLM, Docker, PostgreSQL, or agents yet.

## Commands (Windows / PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1      # activate venv (Python 3.13.7; deps installed)
pip install -r requirements.txt   # install deps
uvicorn src.quorum.main:app --reload
pytest
```

- `uvicorn src.quorum.main:app --reload` works from the repo root without install. Tests import `quorum` via a `sys.path` shim in `tests/conftest.py`; add packaging config (`pyproject.toml`/`setup.py`) when it becomes necessary (roadmap Phase 1 DoD is `uvicorn quorum.main:app`).
- `requirements.txt` is a `pip freeze`-style pinned list for the declared stack only (FastAPI, uvicorn, pydantic, httpx, pytest, pytest-cov, python-dotenv). Keep it aligned with roadmap §4; add DB/semgrep/docker deps only in their phases.

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