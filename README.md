# Quorum

AI-powered GitHub Pull Request review system with a web dashboard and an evidence-grounded **Ask Quorum** chatbot.

Quorum reviews Pull Requests with specialized AI agents (static-analysis evidence, generated tests run in a Docker sandbox, measured coverage), produces a deterministic 0–100 Merge Readiness Score, and stores results in PostgreSQL.

> **Measure, don't merely claim.** Quorum must not claim a test passed unless it actually passed, that coverage improved unless it was measured, or that a security issue exists without supporting evidence.

## What Quorum Does

- Receives GitHub Pull Request events through webhooks.
- Analyzes the changed code (diff, Python AST, Semgrep evidence).
- Generates and executes tests inside an isolated Docker sandbox.
- Measures coverage before/after and computes a deterministic Merge Readiness Score.
- Stores results in PostgreSQL and posts a review summary back to GitHub.
- Provides a React web dashboard and an evidence-grounded Ask Quorum chatbot.

## Key Features

- GitHub Pull Request integration (webhooks + REST API)
- AI-assisted code/security analysis
- Generated tests with real execution and verification
- Coverage measurement and delta
- Deterministic Merge Readiness Score
- Quorum Web Dashboard
- Ask Quorum — grounded in a selected review's evidence

> Features beyond the currently implemented phases are planned by `roadmap.md`. Until the analysis pipeline exists, the dashboard's analysis views show honest "not yet available" states rather than fake data.

## How Users Use Quorum

1. Open the Quorum Web Dashboard.
2. Sign in with GitHub (GitHub OAuth authenticates the user).
3. Install/authorize the Quorum GitHub App.
4. Select the repositories Quorum is allowed to access.
5. Quorum receives Pull Request events automatically from GitHub.
6. Quorum runs its existing analysis pipeline on the Pull Request.
7. The user sees security findings, generated-test results, coverage, and the Merge Readiness result in the dashboard and as GitHub PR feedback.
8. The user can ask questions about the review through Ask Quorum.

> Users do not need to install Quorum or its analysis components locally. The Quorum backend runs the analysis infrastructure. Local installation is only relevant to Quorum development/self-hosted development environments.

## Architecture

```text
GitHub
  │  (webhooks / REST API)
  ▼
FastAPI
  │
  ▼
Quorum Analysis Pipeline
  │
  ▼
PostgreSQL
  │
  ▼
FastAPI REST API
  │
  ▼
React Web Dashboard
```

The frontend communicates **only** with the FastAPI REST API. It never accesses PostgreSQL, Docker, Ollama, Semgrep, or GitHub server secrets directly.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Data | PostgreSQL, SQLAlchemy, Alembic |
| GitHub | GitHub App, webhooks, REST API (`httpx`, `PyJWT`) |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Analysis (planned) | Semgrep, Ollama (Qwen2.5-Coder), Docker sandbox |
| Tests | pytest, pytest-cov |

## Project Structure

```text
Quorum/
├── src/quorum/
│   ├── main.py          # FastAPI app, /health, /webhooks/github
│   ├── config.py        # settings loaded from .env
│   ├── api/             # dashboard REST API (/api/...)
│   ├── auth/            # GitHub OAuth login + sessions
│   ├── database/        # SQLAlchemy models, engine, repository helpers
│   └── github/          # GitHub API client, App JWT, webhook signing
├── frontend/            # React + Vite + TypeScript dashboard
├── tests/               # backend tests (pytest)
├── alembic/             # database migrations
├── roadmap.md           # phased build plan (source of truth)
├── AGENTS.md            # rules/workflow for AI coding agents
├── requirements.txt
└── .env.example
```

## Getting Started

### 1. Clone

```bash
git clone <repository-url>
cd Quorum
```

### 2. Python environment

The project targets Python 3.13.x. Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Environment variables

Copy the template and fill in real values (never commit `.env`):

```powershell
Copy-Item .env.example .env
```

Configure at least:

- `GITHUB_WEBHOOK_SECRET` — secret shared with the GitHub App webhook.
- `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH` — the GitHub App id and the filesystem path to its generated private key (`.pem`). Keep the key out of Git (`.gitignore` covers `*.pem` and `secrets/`).
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_APP_SLUG` — used by the GitHub login flow.
- `GITHUB_REDIRECT_URI` — OAuth callback (default `http://localhost:8000/auth/callback`).
- `FRONTEND_URL` — frontend origin the OAuth callback redirects to after login (default `http://localhost:5173`).
- `DATABASE_URL` — PostgreSQL connection string, e.g. `postgresql+psycopg://USER:PASSWORD@localhost:5432/quorum`.

### 5. PostgreSQL

- Start PostgreSQL locally (default port `5432`).
- Create the database named in `DATABASE_URL` (the example uses `quorum`).
- Apply migrations:

```powershell
alembic upgrade head
```

### 6. Start the backend

From the repository root:

```powershell
uvicorn --app-dir src quorum.main:app --reload
```

### 7. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

### 8. Verify the application

- Backend root: <http://localhost:8000/>
- Health: <http://localhost:8000/health> → `{"status":"ok"}`
- Frontend: <http://localhost:5173/>
- Sign in: <http://localhost:5173/login> (or the header "Sign in")

### 9. Run tests

Backend:

```powershell
pytest
```

Frontend (typecheck + production build; there are no frontend unit tests yet):

```powershell
cd frontend
npm run build
```

### 10. GitHub App local development

To test **real** GitHub webhook delivery, expose the local backend with a tunnel such as Cloudflare Tunnel and point the GitHub App webhook at it. Signature verification is already implemented and tested; a tunnel is not required for local-only development.

## Current Status

- **Phase 0–4:** implemented and verified — FastAPI skeleton, GitHub App + OAuth, GitHub API service layer, and PostgreSQL (models, migration, webhook persistence). (Phase 0 setup items such as Docker, Ollama, and CI are still pending.)
- **Phase 16 Dashboard:** in progress — foundation through Settings are implemented (Chunks 0–8) on the `feature/web-dashboard` branch.
- **Phase 5–14:** remaining backend analysis pipeline (orchestrator, diff/AST, Semgrep, LLM layer, agents, Docker sandbox, synthesis, GitHub comment).
- **Ask Quorum:** pending — requires the analysis/chat backend.

## Documentation

- `roadmap.md` — the phased 70-day build plan and detailed specification (source of truth for what to build and in what order).
- `AGENTS.md` — development rules and the chunk-by-chunk workflow for AI coding agents.
