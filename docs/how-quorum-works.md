# How Quorum Works — From Pull Request to Final Result

A simple walkthrough of Quorum for readers new to the project.

---

## What is Quorum?

Quorum is an **AI-powered code reviewer for GitHub**. When a developer opens a
**Pull Request (PR)** — a proposed code change — Quorum automatically:

1. reads the changed code,
2. looks for **security problems**,
3. **writes and runs tests** to check the code,
4. measures how much of the code the tests cover,
5. gives the PR a **score from 0 to 100** (how ready it is to merge),
6. posts a summary on GitHub and shows everything in a **web dashboard**.

The idea is: *measure, don't merely claim* — nothing is reported unless it was
actually checked.

---

## The Big Picture

```text
Developer creates a Pull Request
              ↓
GitHub sends Quorum a notification (webhook)
              ↓
Quorum's backend saves the PR and starts the analysis
              ↓
Analysis pipeline (the "reviewer")
              ↓
Results stored in the database
              ↓
Developer sees the results (GitHub + Quorum dashboard)
```

---

## Step by Step

### 1. The developer creates a Pull Request

The developer pushes code changes to GitHub and opens a Pull Request — the same
thing they would do on any GitHub project. **Nothing extra is needed.**

### 2. GitHub notifies Quorum (webhook)

GitHub automatically sends a message ("a PR was opened") to Quorum's backend
endpoint: `POST /webhooks/github`.

Quorum checks the message came from GitHub (using a **secret signature**), so
nobody can fake it. It then saves the PR in its database.

### 3. Quorum starts the analysis (orchestrator)

A small coordinator called the **orchestrator** runs the steps below, one after
another. It is like a manager that hands each task to the right specialist.

### 4. Read the changed code (diff)

Quorum asks GitHub for the **diff** — the exact lines that were added, changed,
or removed. This keeps the analysis focused only on what the PR touched.

### 5. Understand the Python structure (AST)

For Python files, Quorum parses the code to find the **functions and classes
that were modified**. This is like reading the outline of the file so it knows
*what* changed, not just *where*.

### 6. Prepare a focused context

Quorum gathers only the relevant parts of the code (changed functions + a
little surrounding context). It **does not send the whole repository** to the AI
— it keeps the analysis focused and fast.

### 7. Security scan (Semgrep)

Quorum runs **Semgrep**, a static analysis tool, over the changed files. Semgrep
looks for known dangerous patterns — for example `subprocess.call(cmd,
shell=True)` or `eval(data)`. These become **security evidence**.

### 8. Security Agent (AI reasoning)

A large-language-model (LLM) **Security Agent** reads the Semgrep evidence and
the changed code, and explains each finding in plain words: what the issue is,
where it is, why it matters. It must stay true to the evidence — it cannot
invent issues.

### 9. Test Writer Agent (AI writes tests)

Another LLM agent, the **Test Writer**, writes pytest tests for the modified
functions.

### 10. Tests run in an isolated sandbox (Docker)

The generated tests are executed inside a **temporary Docker container** that
has **no network**, a **memory limit**, a **time limit**, and is automatically
cleaned up. This keeps untrusted code safe — it can never touch the main
machine.

### 11. Coverage is measured

The sandbox measures how much of the changed code the tests actually executed
(**coverage**), before and after the new tests, and reports the difference
(e.g., `72% → 81%`).

### 12. Merge Readiness Score

A **deterministic formula** combines everything:

- security findings (severity),
- test results (did they pass?),
- coverage (was it measured and improved?)

into one **score from 0 to 100** and a recommendation (e.g., "Ready to merge").
The formula is fixed — the AI does **not** choose the score.

### 13. Results are saved

All results (findings, tests, coverage, score) are stored in **PostgreSQL**, so
they are available later.

### 14. Feedback is given

Quorum does two things:

- **Posts a summary comment** on the GitHub Pull Request.
- **Shows everything in the Quorum dashboard**: analysis status, findings with
  severity and file/line, generated tests, coverage, and the score.

### 15. Ask Quorum (the chatbot)

The developer can ask questions in plain language ("What security issues were
found?") and Quorum answers using **only that PR's stored evidence** — it never
guesses or uses other projects' data.

---

## The Components at a Glance

| Part | Job | Analogy |
|---|---|---|
| GitHub Webhook | tells Quorum a PR exists | the postman |
| Orchestrator | runs the pipeline steps in order | the manager |
| Diff + AST | finds what changed | the editor's highlights |
| Context builder | keeps the AI focused | a briefing note |
| Semgrep | finds dangerous patterns | the security checklist |
| Security Agent (LLM) | explains findings | the security specialist |
| Test Writer (LLM) | writes tests | the QA engineer |
| Docker sandbox | runs tests safely | the isolation room |
| Coverage | measures what was tested | the checklist checker |
| Synthesis | computes the 0–100 score | the grader |
| PostgreSQL | stores everything | the filing cabinet |
| Dashboard + GitHub comment | shows results | the report card |
| Ask Quorum | answers questions about a review | the help desk |

---

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (SQLAlchemy + Alembic migrations)
- **GitHub:** GitHub App, OAuth login, Webhooks, REST API
- **Security analysis:** Semgrep
- **AI/LLM:** OpenAI models (security + test writing + chat)
- **Test execution:** Docker sandbox (pytest + pytest-cov)
- **Frontend:** React + TypeScript + Vite + Tailwind

---

## Where the user sees results

1. **GitHub** — a summary comment on the Pull Request.
2. **Quorum dashboard** — a full page per PR: status, findings, tests, coverage,
   score.
3. **Review History** — every past analysis.
4. **Findings** — all security findings across repositories.
5. **Ask Quorum** — plain-language questions about a specific review.

---

## One-line summary

> A developer opens a Pull Request → Quorum's backend runs a safe, evidence-based
> pipeline (diff → context → security scan → AI analysis → generated tests in a
> sandbox → coverage) → it produces a deterministic 0–100 Merge Readiness Score
> → the results appear on GitHub and in the Quorum dashboard, and you can ask
> the AI questions about the review.