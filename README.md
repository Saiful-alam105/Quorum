# Quorum

AI-powered GitHub Pull Request review and analysis system with a public landing page, an authenticated web dashboard, and an evidence-grounded **Ask Quorum** assistant.

Quorum reviews Pull Requests with specialized AI agents (static-analysis evidence, generated tests run in a Docker sandbox, measured coverage), produces a deterministic 0–100 Merge Readiness Score, stores results in PostgreSQL, and posts a review summary back to GitHub.

> **Measure, don't merely claim.** Quorum must not claim a test passed unless it actually passed, that coverage improved unless it was measured, or that a security issue exists without supporting evidence.

## What Quorum Does

- Provides a public **landing page** that introduces the product before login.
- Signs users in with **GitHub OAuth** and connects repositories through the **Quorum GitHub App**.
- Receives GitHub Pull Request events through **webhooks**.
- Analyzes changed code (diff, Python AST, Semgrep evidence, context management).
- Generates and executes tests inside an isolated **Docker sandbox** and measures coverage before/after.
- Computes a deterministic **Merge Readiness Score** (0–100) from measured evidence.
- Stores results in **PostgreSQL** and posts a review summary back to GitHub.
- Provides an authenticated **React web dashboard** with repositories, Pull Requests, findings, Review History, and Settings.
- **Ask Quorum** (chatbot) is planned: the UI placeholder exists; the grounded chat backend is not yet implemented.

## How Users Use Quorum

```text
Public Landing Page
        ↓
Sign in with GitHub (OAuth)
        ↓
Install / authorize the Quorum GitHub App and select repositories
        ↓
Open or update a Pull Request in GitHub
        ↓
Quorum's backend analyzes the Pull Request
        ↓
Results appear in the Quorum dashboard and as GitHub PR feedback
        ↓
Return later to Review History for previous analyses
```

> Users do not install or run Quorum's analysis components. The backend runs the pipeline; local installation is only a development/demo detail.

## Architecture

```text
GitHub
  │  (webhooks / REST API / OAuth)
  ▼
FastAPI
  │
  ▼
Quorum Analysis Pipeline (Orchestrator)
  │  Diff + AST → Context → Analysis → Synthesis
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
| GitHub | GitHub App, OAuth, webhooks, REST API (`httpx`, `PyJWT`) |
| Analysis | Semgrep, LLM layer (OpenAI), Docker sandbox |
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn-style design tokens |
| Backend tests | pytest, pytest-cov |
| Frontend tests | Vitest, React Testing Library |

### LLM providers

Quorum talks to the LLM through a common `LLMProvider` interface. The active provider is OpenAI (`LLM_PROVIDER=openai`), with per-role models:

- Security Agent → `gpt-5.6-terra`
- Test Writer → `gpt-5.6-terra`
- Ask Quorum → `gpt-5.6-luna`

A single `OPENAI_API_KEY` authenticates all roles (server-side only). A local Ollama provider also exists in the codebase but is not in use.

## Project Structure

```text
Quorum/
├── src/quorum/
│   ├── main.py          # FastAPI app, /health, /webhooks/github
│   ├── config.py        # settings loaded from .env
│   ├── api/             # dashboard REST API (/api/...)
│   ├── auth/            # GitHub OAuth login + sessions
│   ├── github/          # GitHub API client, App JWT, webhook signing, sync
│   ├── orchestrator/    # analysis pipeline runner + stages
│   ├── agents/          # security agent, test writer, synthesis, review comment
│   ├── analysis/        # diff, AST, context management, Semgrep
│   ├── llm/             # LLM provider interface + OpenAI/Ollama providers
│   ├── sandbox/         # Docker sandbox for generated tests
│   └── database/        # SQLAlchemy models, engine, repository helpers
├── frontend/            # React + Vite + TypeScript dashboard
│   └── src/
│       ├── components/  # shared UI, status/severity, landing sections
│       ├── pages/       # dashboard + landing pages
│       └── lib/         # API client, navigation, format helpers
├── tests/               # backend tests (pytest)
├── alembic/             # database migrations
├── roadmap.md           # phased build plan (source of truth)
├── AGENTS.md            # rules/workflow for AI coding agents
├── requirements.txt
└── .env.example
```

## Landing Page (public)

The root route (`/`) is a public landing page for visitors who are not signed in. It introduces Quorum and includes:

- a hero with a "Continue with GitHub" call-to-action
- a "How Quorum works" pipeline
- a "How to Use Quorum" step-by-step journey
- capabilities and a review-experience preview
- security/testing and "Why Quorum" sections
- a final call-to-action

The landing page and dashboard share the same dark, GitHub-inspired visual language. After login, the same route shows the authenticated dashboard.

## Web Dashboard (authenticated)

A dark, developer-focused interface centered on repositories and Pull Requests:

- **Dashboard** — overview metrics and recent Pull Requests, findings, and reviews
- **Repositories** — connected repositories and per-repository Pull Requests
- **Pull Requests** — PR list and a detailed review page (status, findings, tests, coverage, Merge Readiness Score)
- **Findings** — security findings across repositories with severity information
- **Review History** — every analysis run Quorum has produced
- **Settings** — GitHub account, connected repositories, sign out
- **Ask Quorum** — placeholder page (chatbot not implemented yet)

## Getting Started

### 1. Clone

```bash
git clone <repository-url>
cd Quorum
```

### 2. Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 4. Environment variables

Copy the template and fill in real values (never commit `.env`):

```powershell
Copy-Item .env.example .env
```

At minimum configure `GITHUB_WEBHOOK_SECRET`, `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`, `FRONTEND_URL`, and `DATABASE_URL` (see `.env.example`). For analysis, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.

### 5. PostgreSQL

- Start PostgreSQL locally (default port `5432`) and create the database named in `DATABASE_URL`.
- Apply migrations:

```powershell
alembic upgrade head
```

### 6. Start the backend

```powershell
uvicorn --app-dir src quorum.main:app --reload
```

### 7. Start the frontend

```powershell
cd frontend
npm run dev
```

### 8. Access the application

- Frontend: <http://localhost:5173> — the landing page; sign in with GitHub to reach the dashboard.
- Backend: <http://localhost:8000> — health check at `/health`.

> **Note:** use `http://localhost` consistently (not `127.0.0.1`). The GitHub OAuth state cookie is host-scoped, so mixing `localhost` and `127.0.0.1` breaks sign-in.

## Running Tests

Backend:

```powershell
pytest
```

Frontend (component tests, typecheck, and production build):

```powershell
cd frontend
npm test
npm run build
```

## Current Status

- **Phase 0–14 — complete:** FastAPI skeleton, GitHub App + OAuth, GitHub API layer, PostgreSQL, orchestrator, diff/AST, context management, Semgrep, LLM layer, Security Agent, Docker sandbox, Test Writer, Merge Readiness synthesis, GitHub review comment.
- **Phase 15 (dashboard backend API) — complete:** user-scoped read APIs for repositories, Pull Requests, analysis/security/tests/coverage, reviews, and findings.
- **Phase 16 (web dashboard) — complete except Ask Quorum:** the authenticated dashboard and public landing page are implemented; the Ask Quorum UI is a placeholder page.
- **Ask Quorum (roadmap Phase 17) — planned:** the grounded chat backend is not implemented yet.
- **Phase 18 (evaluation harness) and Phase 19 (hardening/demo) — planned.**

## Documentation

- `roadmap.md` — the phased 70-day build plan and detailed specification (source of truth for what to build and in what order).
- `AGENTS.md` — development rules and the chunk-by-chunk workflow for AI coding agents.