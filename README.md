<div align="center">

<img src="frontend/public/favicon.svg" width="84" alt="Quorum logo" />

# Quorum

**AI-powered GitHub Pull Request review that measures evidence — not opinions.**

Scans every pull request for security issues, generates and runs real tests in a
sandbox, measures coverage, and turns it all into a deterministic **Merge
Readiness Score (0–100)** with an evidence-grounded assistant.

![Backend tests](https://img.shields.io/badge/backend%20tests-679%20passing-brightgreen)
![Frontend tests](https://img.shields.io/badge/frontend%20tests-119%20passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Docker](https://img.shields.io/badge/Docker-sandbox-2496ED)

</div>

---

## Overview

Quorum is a web application that automatically reviews GitHub Pull Requests. When
a pull request is opened or updated, Quorum runs an analysis pipeline and reports
what it actually **measured**:

- **Static security analysis** with [Semgrep](https://semgrep.dev/), reasoned over by an LLM Security Agent.
- **Automated test generation** with an LLM Test Writer, executed inside a hardened **Docker sandbox**.
- **Coverage measurement** before and after the generated tests.
- A **deterministic Merge Readiness Score (0–100)** computed from the measured evidence.
- A concise **review comment posted back to the pull request** on GitHub.

Results are stored in PostgreSQL and presented through a React dashboard, which
also includes **Ask Quorum** — an assistant that answers questions about a
specific review using only that review's evidence.

> **Core principle — _measure, don't merely claim_.** Quorum never reports a test
> as passing, a coverage improvement, or a security issue unless it was actually
> measured and is traceable to evidence.

---

## Key Features

**GitHub integration**
- Sign in with **GitHub OAuth**; repository access is granted through a **GitHub App** installation.
- Repository **discovery**, one-click **Connect / Disconnect** (GitHub App install popup with confirmation banners).
- **Create**, **merge**, and **close** pull requests directly from the dashboard.
- **Webhook**-driven analysis (`pull_request` events) with **HMAC signature verification**.

**Automated analysis pipeline**
- Diff extraction and **Python AST** analysis of changed files.
- Bounded **context management** (the whole repository is never sent to a model).
- **Semgrep** static security scan → **Security Agent** (LLM) with evidence-traceable findings.
- **Test Writer Agent** (LLM) → generated `pytest` tests executed in a **Docker sandbox**.
- **Coverage** measured before/after with a computed delta.

**Results & dashboard**
- Deterministic **Merge Readiness Score** with a persisted breakdown (security / tests / coverage).
- Review page with security findings, generated test outcomes, and coverage.
- **Review History**, security **Findings**, repository workspace, and settings.
- **Ask Quorum** chatbot grounded strictly in the selected review.
- Live-sync: repositories refresh on view; analysis results appear without a manual refresh.

---

## How It Works

```
Open / update PR on GitHub
        │  (webhook, HMAC-verified)
        ▼
   FastAPI backend ── schedules background analysis
        │
        ▼
   Orchestrator review pipeline
        ├── Diff + AST extraction
        ├── Context building (bounded)
        ├── Semgrep security scan
        ├── Security Agent (LLM)  ── evidence-traceable findings
        ├── Test Writer (LLM) ──► Docker sandbox ── pytest ── coverage
        └── Synthesis ──► deterministic Merge Readiness Score
        │
        ├──► PostgreSQL (persist run, findings, tests, coverage)
        └──► GitHub review comment on the PR
                 │
                 ▼
        React dashboard + Ask Quorum
```

---

## Architecture

Quorum uses a strict layered architecture. The React dashboard communicates
**only** with the FastAPI REST API; it never accesses PostgreSQL, Docker,
Semgrep, the LLM, or GitHub server secrets directly. The backend is the system
boundary.

```
        ┌──────────────┐
        │    GitHub    │  OAuth · webhooks · REST API
        └──────┬───────┘
               │
        ┌──────▼───────────────────────────────┐
        │            FastAPI backend           │
        │  Auth · Webhook (HMAC) · REST API    │
        └──────┬───────────────────────────────┘
               │
        ┌──────▼───────────────────────────────┐
        │        Orchestrator pipeline         │
        │  Diff+AST → Context → Analysis →     │
        │  Synthesis                           │
        └───┬────────┬──────────┬──────────────┘
            │        │          │
     ┌──────▼──┐ ┌───▼────┐ ┌───▼──────────┐
     │ Semgrep │ │ OpenAI │ │ Docker       │
     │         │ │  LLM   │ │ sandbox      │
     └─────────┘ └────────┘ └──────────────┘
               │
        ┌──────▼───────┐
        │  PostgreSQL  │
        └──────┬───────┘
               │ REST API only
        ┌──────▼───────────────┐
        │  React web dashboard │
        └──────────────────────┘
```

A full architecture description, user-flow diagram, and use-case model are
available in the project report under [`report/`](report/) (compiled PDF:
`report/main.pdf`).

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.13, FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic |
| GitHub | GitHub App, GitHub OAuth, Webhooks, REST API (`httpx`, `PyJWT`) |
| Analysis | Semgrep (static security), Python `ast`, LLM layer |
| LLM | OpenAI (`gpt-5.6-terra` for security/tests, `gpt-5.6-luna` for chat); optional Ollama provider (dormant) |
| Sandbox | Docker (`quorum-sandbox` image with pytest + pytest-cov) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend tests | pytest, pytest-cov |
| Frontend tests | Vitest, React Testing Library |
| Dev webhook tunnel | Cloudflare Quick Tunnel |

### LLM providers

The LLM is accessed through a common `LLMProvider` interface; agents never depend
on a concrete provider. The active provider is **OpenAI**, configured per role:

- Security Agent → `gpt-5.6-terra`
- Test Writer → `gpt-5.6-terra`
- Ask Quorum → `gpt-5.6-luna`

A single `OPENAI_API_KEY` (server-side only) authenticates all roles. A local
`OllamaProvider` exists in the codebase but is not currently used.

---

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
├── tests/               # backend tests (pytest)
├── evaluation/          # evaluation harness (metrics + labeled dataset)
├── alembic/             # database migrations
├── report/              # software project report (LaTeX + compiled PDF)
├── scripts/             # start-tunnel.ps1, sync_github_webhook.py
├── roadmap.md           # phased build plan
├── AGENTS.md            # rules/workflow for AI coding agents
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Prerequisites

- Python 3.13, Node.js/npm, PostgreSQL (running locally), Docker, and Semgrep
  (`pip install semgrep` installs it into the virtualenv).

### 1. Clone and create the environment

```bash
git clone https://github.com/Saiful-alam105/Quorum.git
cd Quorum

python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 3. Configure environment

```powershell
Copy-Item .env.example .env
```

Fill in `GITHUB_WEBHOOK_SECRET`, `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`,
`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`,
`FRONTEND_URL`, and `DATABASE_URL`. For analysis, set `LLM_PROVIDER=openai` and
`OPENAI_API_KEY`.

### 4. Database

Create the database named in `DATABASE_URL`, then apply migrations:

```powershell
alembic upgrade head
```

### 5. Run the backend

```powershell
uvicorn --app-dir src quorum.main:app --reload
```

### 6. Run the frontend

```powershell
cd frontend
npm run dev
```

- Frontend: <http://localhost:5173>
- Backend health: <http://localhost:8000/health>

> **Note:** use `http://localhost` consistently (not `127.0.0.1`) — the GitHub
> OAuth state cookie is host-scoped, so mixing the two breaks sign-in.

### 7. Receive GitHub webhooks locally (development)

GitHub must reach the local backend, so expose it through a Cloudflare quick
tunnel and sync the GitHub App webhook automatically:

```powershell
.\scripts\start-tunnel.ps1            # start tunnel + point the webhook at it
.\scripts\start-tunnel.ps1 -Stop      # stop the tunnel
```

Set the GitHub App **Setup URL** to
`http://localhost:5173/auth/install-callback`.

---

## Configuration

Key environment variables (see `.env.example` for the full list):

| Variable | Purpose |
| --- | --- |
| `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH` | GitHub App authentication |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI` | GitHub OAuth |
| `GITHUB_WEBHOOK_SECRET` | Webhook signature verification |
| `FRONTEND_URL` | Where the backend redirects after auth |
| `DATABASE_URL` | PostgreSQL connection string |
| `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_*_MODEL` | LLM provider and per-role models |
| `SEMGREP_RULESET`, `SEMGREP_TIMEOUT_SECONDS` | Semgrep configuration |
| `SANDBOX_IMAGE`, `SANDBOX_TIMEOUT_SECONDS`, `SANDBOX_MEMORY_LIMIT` | Docker sandbox hardening |
| `GITHUB_TIMEOUT_SECONDS`, `GITHUB_RETRIES` | GitHub API timeout and retry policy |

---

## Running Tests

Backend (from the repository root):

```powershell
pytest
```

Frontend (from `frontend/`):

```powershell
npm test          # component tests (Vitest)
npm run typecheck # TypeScript
npm run build     # production build
```

Current status: **679 backend tests passing** (9 skipped) and **119 frontend tests passing**.

---

## Project Status

All planned roadmap phases (0–19) are complete. The most recent work is a
repository/workflow upgrade: repository discovery, popup connect/disconnect with
persistent disconnects, create-and-merge pull requests from the dashboard,
live-sync, duplicate-analysis protection, and robustness improvements (GitHub
API retries/timeouts, Semgrep fallback, docs-only scoring).

See [`roadmap.md`](roadmap.md) for the full phased plan and status.

---

## Documentation

| Document | Contents |
| --- | --- |
| [`roadmap.md`](roadmap.md) | Phased build plan and detailed specification |
| [`AGENTS.md`](AGENTS.md) | Development rules and workflow |
| [`report/main.pdf`](report/main.pdf) | Software project report (architecture, use cases, screenshots) |
| [`report/SCREENSHOTS_NEEDED.md`](report/SCREENSHOTS_NEEDED.md) | Screenshot checklist for the report |

---

## Team

| Member | ID |
| --- | --- |
| Saiful Alam | 0112320105 |
| Sabbir Ahmed | 011222279 |

**Course:** CSE 3422 — Software Engineering Laboratory, Section C
**Faculty:** Zobaer Ibn Razzaque

---

Academic project. All product behavior described here reflects the current
implementation.
