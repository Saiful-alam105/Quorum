# Quorum — University Demo Checklist (Demo Note)

Date: 2026-09-12. Honest show/do-not-show list. No fake artifacts.

Can show live:

- `GET /health` returning `{"status":"ok"}`.
- GitHub OAuth login/logout and `/api/me`.
- Repositories / repository detail / pull-request list pages with real DB rows.
- PR detail page metadata with "not yet available" analysis sections.
- `git log` incremental chunk history; `pytest` run.

Do NOT show as working (not implemented):

- Semgrep findings, generated tests, coverage deltas, Merge Readiness
  scores, GitHub review comments, Ask Quorum answers.
- No fake screenshots, metrics, test results, users, PRs, or AI findings.

Next backend milestone to mention: Phase 5 — Orchestrator.
