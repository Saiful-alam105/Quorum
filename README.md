# Quorum

## AI-Powered Pull Request Reviewer

Quorum is an AI-powered GitHub Pull Request review system with a web dashboard and an evidence-grounded chatbot.

Quorum analyzes Pull Requests using code-analysis tools and specialized AI agents, verifies generated tests in a Docker sandbox, measures coverage, and produces a deterministic Merge Readiness Score.

The system has two user-facing interfaces:

```text
GitHub
  │
  └── PR events + review comments

Quorum Web Dashboard
  │
  ├── Dashboard
  ├── Repositories
  ├── PR Reviews
  ├── Security Findings
  ├── Test Results
  ├── Review History
  └── Ask Quorum
```

### Core principle

> **Measure, don't merely claim.**

If Quorum says a test passed, the test must actually pass.

If Quorum says coverage improved, coverage must actually be measured.

If Quorum reports a security issue, it should be supported by analysis evidence.

---

# How Quorum Works

```text
GitHub Pull Request
        │
        ▼
GitHub Webhook
        │
        ▼
FastAPI
        │
        ▼
Orchestrator
        │
        ├── PR Diff
        ├── AST Analysis
        ├── Context Builder
        └── Semgrep
                │
        ┌───────┴────────┐
        ▼                ▼
Security Agent    Test Writer Agent
        │                │
     Ollama           Ollama
        │                │
        │          Generated Tests
        │                │
        │          Docker Sandbox
        │                │
        │              pytest
        │                │
        │             Coverage
        └───────┬────────┘
                ▼
        Result Synthesis
                │
                ▼
      Merge Readiness Score
              0–100
                │
        ┌───────┴────────┐
        ▼                ▼
   PostgreSQL       GitHub PR Comment
        │
        ▼
    FastAPI REST API
        │
        ▼
  Quorum Web Dashboard
        │
        ├── Reviews
        ├── Findings
        ├── Tests
        ├── History
        └── Ask Quorum
```

---

# Main Features

## 1. GitHub Integration

Quorum runs as a GitHub App.

It receives Pull Request events such as:

- `opened`
- `reopened`
- `synchronize`

It verifies the webhook signature before processing.

Quorum can read Pull Request information and post a review summary back to GitHub.

---

## 2. GitHub Login and Authorization

The Quorum Web Dashboard uses GitHub as the user's identity provider.

Conceptual flow:

```text
Continue with GitHub
        ↓
GitHub authentication
        ↓
GitHub App authorization
        ↓
Repository access
        ↓
Quorum Dashboard
```

Login and repository authorization are separate concepts:

- **Login** identifies the user.
- **GitHub App authorization** determines which repositories Quorum can access.

Quorum should use minimum required GitHub permissions.

---

# 3. Pull Request Analysis

Quorum extracts:

- Pull Request metadata
- changed files
- diff
- modified functions
- relevant code context
- relevant existing tests

The initial MVP focuses on Python code and uses Python's built-in `ast` module for structural analysis.

---

# 4. Security Review Agent

The Security Review Agent combines static-analysis evidence with LLM reasoning.

```text
Changed Code
     +
AST Context
     +
Semgrep Findings
     ↓
Security Agent
     ↓
Structured Security Result
```

Semgrep provides deterministic security-analysis evidence.

The LLM explains and prioritizes findings using the supplied evidence.

The agent must not invent security findings.

---

# 5. AI Test Writer Agent

The Test Writer Agent generates `pytest` tests for modified code.

Generated tests are not automatically trusted.

They go through:

```text
LLM
 ↓
Generated Test
 ↓
Syntax Validation
 ↓
Docker Sandbox
 ↓
pytest
 ↓
Coverage
```

The frontend can show whether each test was:

- generated;
- executed;
- passed;
- failed.

---

# 6. Sandboxed Test Execution

Repository code and AI-generated tests are untrusted.

They are executed inside Docker with restrictions such as:

- no network;
- execution timeout;
- memory limits;
- process limits;
- temporary filesystem;
- non-privileged execution;
- cleanup after execution.

Quorum must never execute generated tests directly on the host.

---

# 7. Coverage Measurement

Quorum measures coverage before and after generated tests.

```text
Coverage Before
       ↓
Run Generated Tests
       ↓
Coverage After
       ↓
Coverage Delta
```

Example:

```text
Before: 72%
After:  81%
Delta:  +9%
```

The dashboard displays the actual stored measurement.

---

# 8. Merge Readiness Score

Quorum produces a deterministic score from:

```text
0–100
```

The score is based on structured evidence such as:

- security results;
- test results;
- coverage.

The LLM must not freely invent the final numerical score.

The same evidence should produce the same score.

---

# 9. Context Window Management

A Pull Request may contain a small or very large amount of code.

Quorum must **not send the entire repository to the LLM by default**.

Instead:

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
Relevant Evidence
    ↓
Filter + Rank + Chunk
    ↓
Fixed Context Budget
    ↓
LLM
```

Different agents receive only the context they need.

### Security Agent

```text
Changed Code
+
AST Context
+
Semgrep Findings
```

### Test Writer

```text
Modified Functions
+
AST Context
+
Relevant Tests
+
Required Dependencies
```

### Synthesis

```text
Security Result
+
Test Result
+
Coverage Result
```

For large Pull Requests, Quorum should use semantic chunks such as functions, classes, or related files.

The context budget is bounded per LLM call.

A large PR causes more filtering/chunking/aggregation, not an unbounded prompt.

---

# 10. Quorum Web Dashboard

The web dashboard is a required part of the MVP.

It is not a generic admin dashboard. It is the visual control center for Quorum's Pull Request review pipeline.

```text
GitHub
   ↓
FastAPI
   ↓
Analysis
   ↓
PostgreSQL
   ↓
FastAPI REST API
   ↓
React Web Dashboard
```

The frontend should never directly access PostgreSQL, Docker, Ollama, or GitHub server secrets.

---

## 10.1 Main Dashboard

Purpose:

Give the user a quick overview of Quorum activity.

Suggested navigation:

```text
Dashboard
Repositories
Pull Requests
Reviews
Ask Quorum
Settings
```

Suggested dashboard content:

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

The final dashboard must use real backend data rather than hardcoded demo statistics.

---

## 10.2 Repository Page

Purpose:

Show a connected GitHub repository and its Pull Requests.

Example:

```text
Repository: user/my-project

Pull Requests

#42  Add authentication          Score 82
#41  Fix payment validation      Score 94
#40  Update documentation        Score 98
```

Show:

- repository name;
- GitHub link;
- Pull Requests;
- review status;
- Merge Readiness Score;
- last review time;
- link to the review details.

---

## 10.3 PR Review Details — MOST IMPORTANT PAGE

This is the primary Quorum showcase page.

Example:

```text
PR #42 — Add authentication

Merge Readiness
82 / 100

Security       Tests       Coverage
⚠              ✓           ✓
```

The page should contain:

### Review summary

- Merge Readiness Score;
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
- generation status;
- execution status;
- pass/fail status.

### Coverage

Show:

```text
Before: 72%
After:  81%
Delta:  +9%
```

### Changed files

Show the files analyzed by Quorum.

### GitHub link

Provide a link back to the original Pull Request.

This page should make the central Quorum idea visible:

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

## 10.4 Security Findings Page

Purpose:

Give detailed information about security findings.

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

The frontend only displays stored backend findings.

It must not invent:

- severity;
- file;
- line;
- evidence;
- recommendations.

---

## 10.5 Test Generation Page

Purpose:

Show what Quorum generated and what actually happened.

Example:

```text
Generated Tests

Function:
authenticate_user()

Generated:
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
- execution duration;
- stdout/stderr where appropriate;
- coverage;
- failure reason.

Clearly distinguish:

```text
Generated
Executed
Passed
Failed
```

---

## 10.6 Ask Quorum — Chatbot 🤖

Ask Quorum is the conversational interface for a specific Quorum review.

Example:

```text
User:
Why did PR #42 receive a score of 82?

Quorum:
The PR received 82 because the security analysis
identified a high-severity issue, while generated
tests passed for most modified functions and
coverage increased from 72% to 81%.
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

# 11. Ask Quorum Must NOT Be Generic ChatGPT

This is an important architectural rule.

Do not implement:

```text
User Question
      ↓
Generic LLM
```

Instead:

```text
User Question
      ↓
Selected Repository
      ↓
Selected Pull Request
      ↓
Analysis Run
      ↓
Security Findings
      ↓
Test Results
      ↓
Coverage
      ↓
Relevant PR Evidence
      ↓
Bounded Context
      ↓
Ollama
      ↓
Grounded Answer
```

The chatbot should answer questions about actual Quorum analysis.

It must not pretend to know facts that are not in the review context.

It must not use unrelated repository or review data.

It must use the same context-window management principles as the review agents.

---

# 12. Review History

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
- view analysis details;
- continue the Ask Quorum conversation for a review.

PostgreSQL provides the persistent data.

---

# 13. Settings Page

The initial Settings page should contain only implemented functionality.

Possible sections:

- GitHub account information;
- connected repositories;
- GitHub App authorization status;
- implemented Quorum preferences;
- logout.

Do not build settings that have no backend behavior.

---

# 14. Frontend Technology

The recommended frontend stack is:

| Technology | Purpose |
|---|---|
| React | UI framework |
| TypeScript | Type safety |
| Vite | Frontend build/development |
| Tailwind CSS | Styling |
| shadcn/ui | Reusable UI components |

This keeps the frontend modern, manageable, and suitable for a university software project.

All are free/open-source.

---

# 15. Frontend Must Consume the Backend

The frontend should communicate with the FastAPI backend through REST APIs.

Correct:

```text
React
  │
  │ HTTP/REST
  ▼
FastAPI
  │
  ├── PostgreSQL
  ├── GitHub
  ├── Ollama
  ├── Semgrep
  └── Docker
```

Incorrect:

```text
React → PostgreSQL
React → Docker
React → Ollama
React → GitHub using private server secrets
```

### Backend responsibilities

- authentication;
- authorization;
- GitHub integration;
- database access;
- PR analysis;
- LLM calls;
- sandbox execution;
- result validation.

### Frontend responsibilities

- navigation;
- displaying review data;
- cards/tables/charts;
- loading/error/empty states;
- chat interface;
- user interaction.

---

# 16. Frontend API

The initial API surface should remain small.

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

The backend must enforce user/repository authorization.

---

# 17. Project Structure

```text
Quorum/
│
├── README.md
├── roadmap.md
├── AGENTS.md
├── requirements.txt
├── package.json
├── .env.example
├── .gitignore
│
├── backend/
│   └── src/
│       └── quorum/
│           ├── main.py
│           ├── config.py
│           ├── api/
│           ├── auth/
│           ├── github/
│           ├── orchestrator/
│           ├── agents/
│           ├── analysis/
│           ├── llm/
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
├── evaluation/
├── prompts/
├── docker/
└── .github/
    └── workflows/
```

---

# 18. Development Workflow for AI Coding Agents

Before changing code:

```text
1. Read README.md
2. Read roadmap.md
3. Read AGENTS.md
4. Inspect the current repository
5. Identify the current phase
6. Plan the smallest change
7. Implement
8. Run tests
9. Check for regressions
10. Report what changed
```

Implement the project incrementally.

Do not ask an AI coding agent to build the entire system in one request.

---

# 19. Important Development Rules

### Do not overengineer the MVP

Do not introduce:

- Kubernetes;
- Kafka;
- Redis;
- Celery;
- microservices;
- vector databases;
- paid LLM APIs;

unless a later requirement explicitly justifies them.

### Never execute untrusted code directly

Repository code and generated tests must run through Docker.

### Do not invent evidence

Never report:

```text
Test passed
```

unless the test actually passed.

Never report:

```text
Coverage increased
```

unless coverage was measured.

Never report a Semgrep finding that does not exist.

### Keep LLM context bounded

Use:

```text
Filter → Rank → Chunk → Analyze → Aggregate
```

### Keep components separated

```text
GitHub
   ↓
FastAPI
   ↓
Orchestrator
   ↓
Analysis
   ↓
Agents
   ↓
Sandbox
   ↓
Synthesis
   ↓
PostgreSQL / GitHub
   ↓
REST API
   ↓
React Dashboard
```

### Test new features

Every important backend component should have unit or integration tests.

Frontend pages should have appropriate component/integration tests as the project grows.

---

# 20. Evaluation

Evaluation is mandatory.

Use a manually labeled Pull Request dataset containing approximately 15–20 Pull Requests.

Measure:

- security precision;
- security recall;
- F1 score;
- generated-test pass rate;
- coverage delta;
- overall review quality.

Evaluation must be reproducible.

---

# 21. MVP Scope

The MVP must contain:

### Core review system

- GitHub App;
- GitHub login/authorization;
- webhook verification;
- Pull Request extraction;
- diff extraction;
- Python AST analysis;
- bounded context management;
- Semgrep;
- Security Review Agent;
- Test Writer Agent;
- Ollama;
- Docker sandbox;
- pytest;
- pytest-cov;
- PostgreSQL;
- deterministic Merge Readiness Score;
- GitHub PR comment;
- evaluation harness.

### Web dashboard

- Login;
- Main Dashboard;
- Repository Page;
- PR Review Details;
- Security Findings Page;
- Test Generation Page;
- Review History;
- Settings;
- Ask Quorum chatbot.

### Post-MVP

Additional advanced features can be considered after the core MVP and evaluation are stable.

---

# 22. Demo Flow

A strong final demonstration should be:

```text
1. Open Quorum
        ↓
2. Continue with GitHub
        ↓
3. Open repository
        ↓
4. Select PR
        ↓
5. Show Merge Readiness
        ↓
6. Show Security Finding
        ↓
7. Show Generated Tests
        ↓
8. Show Coverage Change
        ↓
9. Open Ask Quorum
        ↓
10. Ask:
    "Why did this PR receive 82?"
        ↓
11. Quorum explains using actual review evidence
```

The demo should show that Quorum is not simply a chatbot.

It is:

```text
Code
 ↓
Static Analysis
 ↓
AI Reasoning
 ↓
Generated Tests
 ↓
Real Execution
 ↓
Coverage
 ↓
Measured Evidence
 ↓
Merge Readiness
 ↓
Human-friendly Dashboard
 ↓
Grounded Chatbot
```

---

# 23. Project Status

The project is developed incrementally according to `roadmap.md`.

The implementation order is:

```text
Project Setup
      ↓
FastAPI
      ↓
GitHub App + Login
      ↓
GitHub API
      ↓
PostgreSQL
      ↓
Orchestrator
      ↓
Diff + AST
      ↓
Context Builder
      ↓
Semgrep
      ↓
LLM
      ↓
Security Agent
      ↓
Docker Sandbox
      ↓
Test Writer
      ↓
Coverage
      ↓
Synthesis
      ↓
GitHub Comment
      ↓
Frontend API
      ↓
Quorum Dashboard
      ↓
Ask Quorum
      ↓
Evaluation
      ↓
Hardening
```

---

# 24. Getting Started

## Backend

Create a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run FastAPI:

```bash
uvicorn quorum.main:app --reload
```

Run backend tests:

```bash
pytest
```

## Frontend

From the frontend directory:

```bash
npm install
npm run dev
```

The exact frontend commands may change with the final project structure.

---

# 25. Free/Local Development Principle

The student MVP should avoid paid APIs.

Preferred local stack:

```text
Ollama
   ↓
Local coding model
   ↓
FastAPI
   ↓
React Dashboard
```

GitHub App, GitHub Actions within applicable free limits, PostgreSQL, Docker, Semgrep Community, React, Vite, Tailwind CSS, shadcn/ui, FastAPI, pytest, and the other listed open-source components should be used without introducing paid infrastructure into the MVP.

---

# Core Philosophy

Quorum is not simply an LLM that comments on code.

It is an **evidence-driven Pull Request review system with a human-friendly web interface and a grounded review chatbot**.

> **Quorum: Don't just ask AI if the code is ready. Measure it.**
