# Quorum — Live Demo Runbook

A truthful end-to-end demo of the implemented Quorum system. Every item shown
is backed by the real backend, database, and analysis pipeline.

## Before the demo

- Start PostgreSQL (port 5432) and ensure `alembic upgrade head` is applied.
- Start the backend: `uvicorn --app-dir src quorum.main:app --reload`
- Start the frontend: `cd frontend && npm run dev`
- Open **http://localhost:5173** (use `localhost`, not `127.0.0.1`).
- Sign in with GitHub (OAuth). Have the Quorum GitHub App installed on a
  repository with at least one analyzed Pull Request.
- Set `OPENAI_API_KEY` so Ask Quorum can answer live.

## Recommended flow

1. **Landing page** (signed out) — product intro, "How it works", "How to use
   Quorum", capabilities, review preview.
2. **Sign in with GitHub** → authenticated dashboard.
3. **Dashboard** — real metrics + recent Pull Requests / findings / reviews.
4. **Pull Requests** — PR review cards; open a PR detail page: status, security
   findings (severity + file/line + evidence), generated tests, coverage,
   Merge Readiness Score.
5. **Findings** — real findings with severity.
6. **Review History** — every analysis run.
7. **Ask Quorum** — open the floating chat (or `/ask-quorum`), select a review,
   ask "What security issues were found?" → structured, grounded answer.
8. **Evaluation** — `python -m evaluation.run` → precision/recall/F1 from the
   labeled dataset.
9. **Tests** — `pytest` and `cd frontend && npm test`.

## Ready artifacts

- Clean demo repository + **known-bad PR** (e.g., `subprocess.call(..., shell=True)`)
- **Known-good PR** (no findings)
- Security finding example, generated-test example, coverage example, chatbot
  example (all produced live from the real PRs above)
- Evaluation results (`evaluation/results/`)

## What NOT to overclaim

- Ask Quorum answers are grounded in the selected review's evidence only.
- Old analysis runs may show "No score" (they predate Merge Readiness) — that is
  honest; re-run analysis on a PR to show a real score.
- The evaluation dataset is a small starter set; grow `evaluation/dataset/`
  toward 15–20 labeled PRs.