# Quorum — Frontend Status (Demo Note)

Date: 2026-09-12. Verified against `frontend/src/App.tsx` and
`frontend/src/pages/`.

Stack: React + TypeScript + Vite + Tailwind CSS + shadcn/ui.

Routes actually present:

- `/login` — Login (GitHub sign-in).
- `/` — Dashboard overview.
- `/repositories` — Repositories list.
- `/repositories/:repositoryId` — Repository detail / PR list.
- `/pull-requests` — Pull Requests list.
- `/pull-requests/:pullRequestId` — PR review details (real PR metadata;
  review summary, security, tests, coverage, changed-files sections show
  honest "not yet available" states until the analysis backend exists).
- `/reviews` — Review history.
- `/settings` — Settings.
- `/ask-quorum` — Deferred placeholder ("Ask Quorum is not available yet").

No fake statistics, findings, or scores are shown in the UI.
