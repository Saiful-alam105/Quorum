# Quorum — Database Schema Status (Demo Note)

Date: 2026-09-12. Verified against `src/quorum/database/models.py`
and `alembic/`.

Tables (all 8 models exist):

- `users`, `repositories`, `pull_requests`, `analysis_runs`,
  `security_findings`, `test_runs`, `coverage_results`, `chat_messages`.

Migration:

- `303b9ed314cd` applied to local PostgreSQL on port `5432`;
  tables/PKs/FKs confirmed (per `roadmap.md` §7).

Persistence currently used for:

- Webhook-driven repository / pull-request upserts
  (`src/quorum/database/repository.py`).
- User association + user-level repository/review access isolation.

No review/test/coverage/chat rows are produced yet — the analysis
pipeline that would write them is not implemented.
