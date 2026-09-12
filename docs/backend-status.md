# Quorum — Backend Status (Demo Note)

Date: 2026-09-12. Verified against `src/quorum/`.

Implemented and working:

- FastAPI app (`src/quorum/main.py`): `GET /`, `GET /health`,
  `POST /webhooks/github`.
- Webhook handling: `ping`, `pull_request`, `installation`,
  `installation_repositories`; PR persistence on `opened` / `reopened` /
  `synchronize`.
- Signature verification: HMAC (`src/quorum/github/webhook.py`).
- GitHub App auth: private-key loading + JWT
  (`src/quorum/github/app_auth.py`).
- GitHub API service layer (`src/quorum/github/api.py`, 9 functions):
  `get_installation_token`, `get_authenticated_user`, `get_repositories`,
  `get_repository`, `get_pull_request`, `get_pr_files`, `get_pr_diff`,
  `get_pr_comments`, `create_pr_comment` (mocked tests; not yet consumed
  by a pipeline).

Not started: orchestrator, diff/AST, Semgrep stage, LLM layer, agents,
Docker sandbox, synthesis/score, GitHub review comment posting.
