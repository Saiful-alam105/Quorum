# Quorum — Architecture Overview (Demo Note)

Date: 2026-09-12. Status-only note; no new architecture introduced.

Current high-level flow (what exists today):

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

Notes (from `README.md` / `roadmap.md`):

- Frontend talks only to the FastAPI REST API.
- It never accesses PostgreSQL, Docker, Ollama, Semgrep, or GitHub
  server secrets directly.
- Analysis pipeline, agents, sandbox, and Ask Quorum backend are planned
  phases, not yet implemented.
