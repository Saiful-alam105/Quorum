# Quorum — Detailed Implementation Roadmap

## 1. Project Goal

Build Quorum, an AI-powered GitHub Pull Request review system with a web dashboard and an evidence-grounded chatbot.

Quorum should:

- receive GitHub Pull Request events;
- analyze changed code;
- use Python AST analysis and Semgrep evidence;
- use a local LLM through Ollama for security reasoning and test generation;
- execute generated tests inside a Docker sandbox;
- measure test and coverage results;
- calculate a deterministic Merge Readiness Score from 0–100;
- store review results in PostgreSQL;
- post a review summary back to GitHub;
- provide a React-based Quorum Web Dashboard;
- provide an **Ask Quorum** chatbot grounded in the selected repository, Pull Request, and analysis results;
- evaluate itself against a manually labeled Pull Request dataset.

### Core principle

> **Measure, don't merely claim.**

Quorum must not claim that a test passed unless it actually passed, that coverage improved unless it was measured, or that a security issue exists without supporting evidence.

---

# 2. Product Model

Quorum has two user-facing interfaces:

```text
                         QUORUM
                            │
             ┌──────────────┴──────────────┐
             │                             │
       GitHub Interface              Quorum Web App
             │                             │
     PR comments/results        Dashboard + Reviews + Chatbot
```

GitHub remains the source of Pull Request events and the place where Quorum posts review summaries.

The Quorum Web Dashboard is the visual control center for reviewing repositories, Pull Requests, security findings, generated tests, coverage, review history, and Ask Quorum conversations.

---

# 3. Authentication and GitHub Authorization

Users should sign into Quorum using their GitHub account rather than a separate Quorum username/password system.

Conceptual flow:

```text
User opens Quorum
        ↓
Continue with GitHub
        ↓
GitHub authentication/authorization
        ↓
Quorum identifies the GitHub user
        ↓
User authorizes Quorum/GitHub App for repositories
        ↓
Quorum Dashboard
```

Keep these concepts separate:

### Login / identity

Answers:

> Who is this user?

### GitHub App authorization

Answers:

> Which repositories can Quorum access and review?

Use the minimum GitHub permissions required by the application.

Do not store GitHub passwords.

Do not expose GitHub private keys to the frontend.

---

# 4. Tech Stack

All core technologies should be free, open-source, or locally runnable for the student MVP.

| Layer | Technology | Purpose |
|---|---|---|
| Backend language | Python 3.12/3.13 | Main backend, analysis, orchestration, testing |
| Backend | FastAPI | REST API and GitHub webhook server |
| Server | Uvicorn | Runs FastAPI |
| Frontend | React | Web dashboard UI |
| Frontend language | TypeScript | Type-safe frontend development |
| Frontend build | Vite | Fast frontend development/build |
| Styling | Tailwind CSS | UI styling |
| Components | shadcn/ui | Reusable accessible UI components |
| API communication | REST/HTTP | Frontend ↔ FastAPI communication |
| LLM runtime | Ollama | Local LLM inference |
| Coding model | Qwen2.5-Coder | Code reasoning and test generation |
| GitHub | GitHub App + Webhooks + REST API | PR integration |
| Security | Semgrep Community CLI | Static security evidence |
| Code analysis | Python `ast` | Structural analysis of changed Python code |
| Testing | pytest | Test execution |
| Coverage | pytest-cov | Coverage measurement |
| Sandbox | Docker | Isolated execution of generated tests |
| Database | PostgreSQL | Persistent application/review/chat data |
| ORM | SQLAlchemy | Database access |
| Migrations | Alembic | Database migrations |
| Validation | Pydantic | Request/response/data validation |
| HTTP client | httpx | GitHub and Ollama communication |
| Version control | Git + GitHub | Source control |
| CI | GitHub Actions | Automated tests/checks |
| Local webhook tunnel | Cloudflare Tunnel | Expose local FastAPI during development |

### LLM architecture

Keep the LLM behind an interface:

```text
LLMProvider
    │
    └── OllamaProvider
            │
            └── Qwen2.5-Coder
```

This allows the model to be replaced later without rewriting the agents.

Do not add paid LLM APIs to the MVP.

---

# 5. Repository Structure

Maintain one main GitHub repository:

```text
Quorum/
├── README.md
├── roadmap.md
├── AGENTS.md
├── .gitignore
├── .env.example
├── requirements.txt
├── package.json
│
├── backend/
│   └── src/
│       └── quorum/
│           ├── main.py
│           ├── config.py
│           ├── api/
│           │   ├── health.py
│           │   ├── webhooks.py
│           │   ├── repositories.py
│           │   ├── pull_requests.py
│           │   ├── reviews.py
│           │   └── chat.py
│           ├── auth/
│           ├── github/
│           ├── orchestrator/
│           ├── agents/
│           │   ├── security/
│           │   ├── test_writer/
│           │   └── synthesis/
│           ├── analysis/
│           │   ├── diff.py
│           │   ├── ast_parser.py
│           │   ├── context_builder.py
│           │   ├── semgrep.py
│           │   └── coverage.py
│           ├── llm/
│           │   ├── base.py
│           │   └── ollama_provider.py
│           ├── sandbox/
│           ├── database/
│           └── schemas/
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── layouts/
│       ├── services/
│       ├── hooks/
│       ├── types/
│       └── App.tsx
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── evaluation/
│   ├── dataset/
│   ├── scripts/
│   └── results/
│
├── prompts/
├── docker/
├── docs/
└── .github/
    └── workflows/
```

The exact structure may evolve during implementation. AI coding agents must inspect the existing repository before creating or moving files.

---

# 6. Development Rules for OpenCode / AI Coding Agents

Before implementing a task, the coding agent should:

1. Read `README.md`.
2. Read `roadmap.md`.
3. Read `AGENTS.md` if present.
4. Inspect the existing source tree.
5. Identify the current roadmap phase.
6. Implement only the requested phase/task.
7. Avoid unrelated refactoring.
8. Add or update tests.
9. Run relevant tests.
10. Report what changed and what remains.

### Do not

- skip roadmap phases without a reason;
- add paid services when a free/local option exists;
- introduce Redis, Celery, Kafka, Kubernetes, microservices, or vector databases without a documented requirement;
- send the whole repository to an LLM by default;
- execute repository or generated code directly on the host;
- expose secrets to the frontend;
- hardcode tokens or private keys;
- let the LLM arbitrarily choose the final score;
- allow the chatbot to answer from unrelated/global context when a review-specific answer is required.

---

# 7. 70-Day Roadmap

## Phase 0 — Project Setup (Day 1)

Tasks:

- [ ] Create/maintain GitHub repository.
- [ ] Create Python environment.
- [ ] Create FastAPI backend structure.
- [ ] Create React/Vite frontend structure.
- [ ] Create `README.md`.
- [ ] Create `roadmap.md`.
- [ ] Create `.env.example`.
- [ ] Create `.gitignore`.
- [ ] Create `requirements.txt`.
- [ ] Install Docker.
- [ ] Install Ollama.
- [ ] Install a supported local coding model.
- [ ] Add basic CI.

Definition of done:

```text
Python ✓
Git ✓
Docker ✓
Ollama ✓
Node/npm ✓
React/Vite ✓
```

---

# Phase 1 — FastAPI Skeleton (Days 2–3)

Create:

```text
GET /
GET /health
POST /webhooks/github
```

Add tests.

Definition of done:

```bash
uvicorn quorum.main:app --reload
```

works and `/health` returns HTTP 200.

---

# Phase 2 — GitHub App + Authentication (Days 4–8)

Implement:

- [ ] GitHub App registration.
- [ ] Webhook configuration.
- [ ] Webhook secret.
- [ ] App private key handling.
- [ ] Minimum repository permissions.
- [ ] Pull Request event subscription.
- [ ] Issue-comment event subscription.
- [ ] GitHub webhook signature verification.
- [ ] GitHub user authentication flow for the web dashboard.
- [ ] GitHub App/repository authorization flow.
- [ ] Secure backend-side token handling.
- [ ] Install the App on a test repository.

Milestone:

```text
GitHub user
    ↓
Quorum login
    ↓
GitHub authorization
    ↓
Quorum identifies user/repositories
```

---

# Phase 3 — GitHub API Layer (Days 9–11)

Implement a GitHub service layer for:

```text
get_installation_token()
get_authenticated_user()
get_repositories()
get_repository()
get_pull_request()
get_pr_files()
get_pr_diff()
get_pr_comments()
create_pr_comment()
```

Keep GitHub communication out of frontend code.

Definition of done:

The backend can authenticate, read repositories/PRs, and post a test PR comment.

---

# Phase 4 — PostgreSQL (Days 12–14)

Create initial models for:

```text
users
repositories
pull_requests
analysis_runs
security_findings
test_runs
coverage_results
chat_messages
```

Use:

- SQLAlchemy
- Alembic

Definition of done:

A repository/PR/review can be stored and retrieved by the backend.

---

# Phase 5 — Orchestrator (Days 15–17)

Build the core pipeline:

```text
PR
 ↓
Orchestrator
 ├── Diff extraction
 ├── AST extraction
 ├── Context Builder
 ├── Security Agent
 ├── Test Writer Agent
 └── Synthesis
```

Long-running work must not block the webhook response.

Use FastAPI background execution initially. Do not introduce a distributed task queue unless required later.

---

# Phase 6 — Diff + AST Analysis (Days 18–22)

Extract:

- [ ] changed files
- [ ] added/removed lines
- [ ] modified functions
- [ ] modified classes
- [ ] arguments
- [ ] decorators
- [ ] source ranges
- [ ] surrounding function context
- [ ] relevant existing tests

Definition of done:

The system can identify the modified Python functions and their relevant structural context.

---

# Phase 7 — Context Window Management (Days 23–25)

This is a required architectural component.

Quorum must never send an entire repository to an LLM by default.

Pipeline:

```text
Repository
    ↓
PR Diff
    ↓
Changed Files
    ↓
Changed Functions
    ↓
AST Analysis
    ↓
Semgrep / relevant evidence
    ↓
Relevant Tests / Dependencies
    ↓
Filter
    ↓
Rank
    ↓
Semantic Chunking
    ↓
Fixed Context Budget
    ↓
LLM
```

### Agent-specific context

Security Agent:

```text
Changed Code
+
AST Context
+
Semgrep Findings
```

Test Writer:

```text
Modified Functions
+
AST Context
+
Relevant Tests
+
Required Dependencies
```

Synthesis:

```text
Security Result
+
Test Result
+
Coverage Result
```

### Requirements

- [ ] Define maximum context/token budgets.
- [ ] Prefer changed functions/files over the entire repository.
- [ ] Chunk large files semantically.
- [ ] Preserve file/line metadata.
- [ ] Avoid duplicating the same context in multiple prompt sections.
- [ ] Aggregate chunk-level results before synthesis.
- [ ] Test with deliberately oversized Pull Requests.

A larger PR should cause more filtering/chunking/aggregation, not an unbounded prompt.

---

# Phase 8 — Semgrep Security Analysis (Days 26–28)

Pipeline:

```text
PR code
 ↓
Semgrep
 ↓
JSON findings
```

Store:

```text
rule ID
severity
file
line
message
code location
```

The Security Agent must reason over actual Semgrep evidence.

The LLM must not invent a Semgrep finding.

---

# Phase 9 — LLM Layer (Days 29–30)

Create:

```text
llm/base.py
llm/ollama_provider.py
```

Interface:

```python
class LLMProvider:
    async def generate(self, prompt: str) -> str:
        ...
```

Run the selected coding model through Ollama.

Definition of done:

Python can send a bounded prompt to Ollama and receive a structured model response.

---

# Phase 10 — Security Review Agent (Days 31–34)

Input:

```text
PR diff
AST context
Semgrep findings
```

Output should use a strict structured schema, for example:

```json
{
  "findings": [
    {
      "severity": "high",
      "title": "...",
      "file": "...",
      "line": 42,
      "evidence": "...",
      "explanation": "...",
      "confidence": 0.0
    }
  ]
}
```

Requirements:

- [ ] Evidence must be traceable to input.
- [ ] File and line references must be preserved.
- [ ] Avoid unsupported claims.
- [ ] Validate LLM output with Pydantic.

---

# Phase 11 — Docker Sandbox (Days 35–37)

Generated tests and untrusted repository code must execute inside a temporary Docker container.

Requirements:

- [ ] no network;
- [ ] memory limit;
- [ ] process limit;
- [ ] hard timeout;
- [ ] temporary filesystem;
- [ ] non-privileged execution;
- [ ] container cleanup.

Definition of done:

A valid test passes and an intentionally unsafe/infinite test is terminated safely.

---

# Phase 12 — Test Writer Agent (Days 38–43)

Input:

```text
PR diff
AST context
modified function
relevant existing tests
```

Pipeline:

```text
LLM
 ↓
Generated pytest
 ↓
Syntax validation
 ↓
Docker Sandbox
 ↓
pytest
 ↓
pytest-cov
```

Measure:

```text
coverage_before
coverage_after
coverage_delta
```

Store test execution results.

---

# Phase 13 — Result Synthesis + Merge Readiness (Days 44–46)

Combine:

```text
Security result
+
Test result
+
Coverage result
```

into:

```text
Merge Readiness Score: 0–100
```

The scoring formula must be deterministic and documented.

The LLM must not freely invent the final score.

Definition of done:

The same structured evidence produces the same score.

---

# Phase 14 — GitHub Review Comment + Core MVP (Days 47–49)

Post a concise review summary:

```text
## Quorum Review

### Merge Readiness
82/100

### Security
1 High
1 Medium

### Tests
Generated tests: 3
Passed: 2
Failed: 1

### Coverage
72% → 81%
Delta: +9%

### Recommendation
...
```

Definition of done:

```text
GitHub PR
 ↓
Quorum analysis
 ↓
Evidence
 ↓
Score
 ↓
GitHub comment
```

---

# Phase 15 — Quorum Web Dashboard Backend API (Days 50–52)

Before building the React pages, expose backend APIs for the frontend.

Initial endpoints:

```text
GET    /api/me

GET    /api/repositories
GET    /api/repositories/{id}

GET    /api/pull-requests
GET    /api/pull-requests/{id}

GET    /api/pull-requests/{id}/analysis
GET    /api/pull-requests/{id}/security
GET    /api/pull-requests/{id}/tests
GET    /api/pull-requests/{id}/coverage

GET    /api/reviews
GET    /api/reviews/{id}

GET    /api/reviews/{id}/chat
POST   /api/reviews/{id}/chat
```

Rules:

- React communicates only with FastAPI.
- React does not directly access PostgreSQL.
- React does not directly call Ollama.
- React does not directly call GitHub using server secrets.
- Backend enforces user/repository authorization.
- API responses use Pydantic schemas.

---

# Phase 16 — Quorum Web Dashboard (Days 53–58)

The dashboard is now a required MVP feature.

Use:

```text
React
+
TypeScript
+
Vite
+
Tailwind CSS
+
shadcn/ui
```

## 16.1 Main Dashboard

Purpose:

Give the user a quick overview of their Quorum activity.

Suggested layout:

```text
┌─────────────────────────────────────────────────────────────┐
│ QUORUM                                      User / Settings  │
├──────────────┬──────────────────────────────────────────────┤
│ Dashboard    │ Welcome to Quorum                            │
│ Repositories │                                               │
│ Pull Requests│  Repositories   Reviews   Warnings           │
│ Reviews      │      12           8          2                │
│ Ask Quorum   │                                               │
│ Settings     │ Recent Reviews                                │
│              │ ┌───────────────────────────────────────────┐ │
│              │ │ PR #42  Add authentication       82/100  │ │
│              │ │ Security ⚠ Tests ✓ Coverage ✓            │ │
│              │ ├───────────────────────────────────────────┤ │
│              │ │ PR #41  Payment validation       94/100  │ │
│              │ │ Security ✓ Tests ✓ Coverage ✓            │ │
│              │ └───────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────┘
```

Must show real backend data.

Do not create fake statistics in the final implementation.

---

## 16.2 Repository Page

Purpose:

Show a repository and its Pull Requests.

Example:

```text
Repository: user/my-project

Pull Requests

#42  Add authentication          Score 82
#41  Fix payment validation      Score 94
#40  Update documentation        Score 98
```

Features:

- repository name and GitHub link;
- Pull Request list;
- review status;
- Merge Readiness Score;
- last review time;
- link to PR review details.

---

## 16.3 PR Review Details — MOST IMPORTANT PAGE

This is the primary Quorum showcase page.

Show:

```text
PR #42 — Add authentication

Merge Readiness
82 / 100

Security       Tests       Coverage
⚠              ✓           ✓
```

Sections:

### Review summary

- score;
- recommendation;
- analysis status;
- review timestamp.

### Security findings

Show:

- severity;
- title;
- file;
- line;
- evidence;
- AI explanation.

### Generated tests

Show:

- test names;
- generated status;
- pass/fail status;
- execution details.

### Coverage

Show:

```text
Before: 72%
After: 81%
Delta: +9%
```

### Changed files

Show analyzed files and relevant review information.

### GitHub link

Provide a link back to the original Pull Request.

The page must visualize the project's core idea:

```text
AI reasoning
      ↓
Evidence
      ↓
Verification
      ↓
Measured result
      ↓
Merge Readiness
```

---

## 16.4 Security Findings Page

Purpose:

Give a detailed view of security findings.

Example:

```text
Security Issue

SQL Injection

Severity: HIGH

File:
auth/database.py

Line:
42

Evidence:
Semgrep finding details...

AI Analysis:
Explanation based on the finding and changed code...

Recommendation:
Use parameterized queries.

[ View Pull Request ]
```

Rules:

- findings must come from stored backend analysis;
- frontend must not invent security findings;
- preserve file and line references;
- show the source evidence used by the Security Agent.

---

## 16.5 Test Generation Page

Purpose:

Show what Quorum generated and what actually happened.

Example:

```text
Generated Tests

Function:
authenticate_user()

Generated test:
test_invalid_password()

Status:
✓ PASSED

Execution:
Docker Sandbox

Coverage:
Before 72%
After 81%
Delta +9%
```

Show:

- generated test names;
- execution status;
- stdout/stderr where appropriate;
- execution duration;
- coverage result;
- failure reason for failed tests.

The frontend must distinguish clearly between:

```text
Generated
Executed
Passed
Failed
```

---

## 16.6 Ask Quorum — Chatbot

Purpose:

Allow the user to ask questions about a specific review/repository.

Example:

```text
User:
Why did PR #42 receive a score of 82?

Quorum:
The PR received 82 because the security analysis
identified a high-severity issue, while generated
tests passed for most modified functions and coverage
increased from 72% to 81%.
```

Suggested questions:

- Why did this PR receive this score?
- Which files caused the score to decrease?
- What security issues were found?
- Why is this finding dangerous?
- What tests did Quorum generate?
- Why did this generated test fail?
- How did coverage change?
- What changed in this Pull Request?

---

## 16.7 Ask Quorum Must NOT Be Generic ChatGPT

The chatbot must be grounded in the selected Quorum context.

Required context:

```text
User question
+
Current repository
+
Current Pull Request
+
Analysis run
+
PR diff
+
Security findings
+
Test results
+
Coverage
```

Conceptual flow:

```text
User Question
      ↓
Identify selected review
      ↓
Retrieve relevant stored evidence
      ↓
Build bounded context
      ↓
Ollama / LLM
      ↓
Grounded response
```

Do not implement:

```text
User Question
      ↓
Generic LLM
```

The chatbot should answer about actual Quorum analysis, not pretend to know facts that are not present.

It must not use unrelated repository/review data.

It must preserve the same context-window rules used by the review agents.

---

## 16.8 Review History Page

Purpose:

Show previous Quorum reviews.

Example:

```text
Review History

Repository: my-project

PR     Title                    Score    Status
#42    Add authentication       82       Review
#41    Payment validation       94       Ready
#40    Documentation            98       Ready
#39    Refactor API             76       Warning
```

Features:

- filter by repository;
- filter by score/status;
- open a previous review;
- see review timestamp;
- access associated analysis details;
- continue an Ask Quorum conversation for a review.

PostgreSQL provides the persistent data for this page.

---

## 16.9 Settings Page

Minimum settings:

- GitHub account information;
- connected repositories;
- GitHub App authorization status;
- Quorum/analysis preferences that are actually implemented;
- logout.

Do not build complex configuration screens without a backend feature behind them.

---

# 17. Frontend Architecture Rules

The frontend is a presentation and interaction layer.

Use:

```text
React
  │
  │ REST/HTTP
  ▼
FastAPI
  │
  ├── PostgreSQL
  ├── GitHub
  ├── Ollama
  ├── Semgrep
  └── Docker
```

Never use:

```text
React → PostgreSQL
React → Docker
React → Ollama
React → GitHub private API with secrets
```

Backend responsibilities:

- authentication;
- authorization;
- GitHub integration;
- database access;
- analysis orchestration;
- LLM calls;
- sandbox execution;
- result validation.

Frontend responsibilities:

- navigation;
- displaying data;
- forms;
- loading/error states;
- charts/cards/tables;
- chat interface;
- user interaction.

---

# 18. Phase 17 — Ask Quorum Implementation (Days 59–63)

If the core dashboard works, implement the chatbot.

Backend:

```text
GET  /api/reviews/{review_id}/chat
POST /api/reviews/{review_id}/chat
```

Store:

```text
review_id
user_id
role
message
timestamp
```

Use bounded context.

Prevent:

- cross-repository context leakage;
- cross-review context leakage;
- prompt injection from repository content;
- automatic chatbot self-replies;
- unsupported claims.

If time is limited, reduce chatbot complexity before reducing the core review pipeline or evaluation harness.

---

# 19. Phase 18 — Evaluation Harness (Days 64–67)

Evaluation remains mandatory.

Use:

```text
15–20 manually labeled Pull Requests
```

Measure:

```text
Security Precision
Security Recall
F1
Generated Test Pass Rate
Coverage Delta
Overall Review Quality
```

Store scripts/results under:

```text
evaluation/
```

The results must be reproducible.

---

# 20. Phase 19 — Hardening + Final Demo (Days 68–70)

Demonstrate:

- invalid webhook signature;
- repository prompt injection;
- chatbot prompt injection;
- sandbox escape attempt;
- chatbot self-reply prevention;
- unauthorized repository access;
- oversized Pull Request/context handling.

Prepare:

```text
clean demo repository
known-bad PR
known-good PR
security finding example
generated test example
coverage example
chatbot example
evaluation results
backup demo video
```

---

# 21. Final Architecture

```text
                           GitHub
                              │
                         Pull Request
                              │
                              ▼
                       GitHub App Webhook
                              │
                              ▼
                       FastAPI Backend
                              │
                    Signature Verification
                              │
                              ▼
                         Orchestrator
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              Diff + AST          Semgrep
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       Context Builder
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Security Agent            Test Writer Agent
                 │                         │
               Ollama                   Ollama
                 │                         │
                 │                  Generated Tests
                 │                         │
                 │                   Docker Sandbox
                 │                         │
                 │                       pytest
                 │                         │
                 │                      Coverage
                 └────────────┬────────────┘
                              ▼
                       Result Synthesis
                              │
                              ▼
                    Merge Readiness Score
                              │
                  ┌───────────┴───────────┐
                  ▼                       ▼
             PostgreSQL             GitHub Comment
                  │
                  ▼
             FastAPI REST API
                  │
                  ▼
        ┌─────────────────────────┐
        │    Quorum Web Dashboard │
        ├─────────────────────────┤
        │ Main Dashboard          │
        │ Repositories            │
        │ PR Review Details       │
        │ Security Findings       │
        │ Test Generation         │
        │ Review History          │
        │ Ask Quorum              │
        │ Settings                │
        └─────────────────────────┘
                  │
                  ▼
              React/Vite
                  │
              TypeScript
                  │
          Tailwind + shadcn/ui
```

---

# 22. Security Principles

1. Never trust repository content.
2. Never trust PR comments.
3. Never execute generated code directly on the host.
4. Verify every GitHub webhook signature.
5. Use minimum GitHub permissions.
6. Keep secrets outside Git.
7. Use short-lived GitHub App installation tokens where appropriate.
8. Never expose database credentials to the frontend.
9. Enforce repository authorization on the backend.
10. Keep chatbot context scoped to the selected review.
11. Keep LLM context bounded.
12. Treat LLM output as untrusted until validated.
13. Do not let LLM output determine security severity or final score without deterministic validation/evidence.

---

# 23. Definition of Done

## Core backend

- [ ] GitHub App works.
- [ ] GitHub login/authorization works.
- [ ] Webhook signature verification works.
- [ ] PR diff extraction works.
- [ ] AST extraction works.
- [ ] Context Builder works.
- [ ] Semgrep works.
- [ ] Ollama works.
- [ ] Security Agent works.
- [ ] Docker sandbox works.
- [ ] Test Writer works.
- [ ] pytest execution works.
- [ ] Coverage delta works.
- [ ] Merge Readiness Score works.
- [ ] GitHub PR comment works.
- [ ] PostgreSQL stores review data.

## Web dashboard

- [ ] Login page.
- [ ] Main Dashboard.
- [ ] Repository Page.
- [ ] PR Review Details.
- [ ] Security Findings Page.
- [ ] Test Generation Page.
- [ ] Review History Page.
- [ ] Settings Page.
- [ ] Ask Quorum page.
- [ ] Frontend consumes FastAPI APIs only.
- [ ] Loading/error/empty states work.
- [ ] No fake final data in the completed demo.

## Evaluation and security

- [ ] 15–20 PR evaluation set exists.
- [ ] Precision/recall/F1 measured.
- [ ] Test pass rate measured.
- [ ] Coverage delta measured.
- [ ] Oversized PR/context handling tested.
- [ ] Prompt-injection defenses demonstrated.
- [ ] Sandbox security demonstrated.
- [ ] Unauthorized repository access prevented.
- [ ] Demo is reproducible.

---

# 24. Milestones

| Milestone | Day | Result |
|---|---:|---|
| M1 | 3 | FastAPI skeleton |
| M2 | 11 | GitHub App + GitHub API |
| M3 | 17 | Database + Orchestrator |
| M4 | 22 | Diff + AST |
| M5 | 30 | Context + LLM |
| M6 | 34 | Security Agent |
| M7 | 43 | Test Writer + Sandbox |
| M8 | 49 | Core MVP + GitHub comment |
| M9 | 52 | Frontend API |
| M10 | 58 | Quorum Web Dashboard |
| M11 | 63 | Ask Quorum |
| M12 | 67 | Evaluation |
| M13 | 70 | Hardening + Final Demo |

---

# 25. First Working Goal

Do not build the entire system immediately.

The first target is:

```text
GitHub PR
   ↓
Webhook
   ↓
FastAPI
   ↓
Read PR
   ↓
Save PR
   ↓
Post "Quorum received this PR"
```

Then build one phase at a time.

The frontend should not be a disconnected CRUD application. It must become the visual control center for the same PR-review pipeline that runs in the backend.
