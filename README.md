# Quorum

## AI-Powered Pull Request Reviewer

Quorum is a GitHub App that automatically reviews Pull Requests using multiple specialized AI agents and real code-analysis evidence.

Instead of asking one LLM to review the entire repository, Quorum breaks the review into specialized tasks:

- **Security Review Agent** — analyzes security-related issues using Semgrep findings and LLM reasoning.
- **Test Writer Agent** — generates tests for modified code and verifies them in a Docker sandbox.
- **Synthesis Layer** — combines security, testing, and coverage results into a deterministic Merge Readiness Score.

### Core Principle

> **Measure, don't merely claim.**

If Quorum says a test passed, the test must actually pass.

If Quorum says coverage improved, coverage must actually be measured.

If Quorum reports a security issue, it should be supported by analysis evidence.

---

# How It Works

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
        └── Context Builder
                │
        ┌───────┴────────┐
        ▼                ▼
Security Agent    Test Writer Agent
        │                │
     Semgrep           Ollama
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
```

---

# Main Features

### 1. GitHub Integration

Quorum runs as a GitHub App and reacts to Pull Request events such as:

- `opened`
- `reopened`
- `synchronize`

The webhook signature must always be verified before processing.

### 2. Pull Request Analysis

Quorum extracts:

- Pull Request metadata
- changed files
- diff
- affected code
- relevant existing tests

### 3. Python AST Analysis

The initial MVP focuses on Python.

Python's built-in `ast` module is used to identify relevant:

- functions
- classes
- arguments
- source locations
- code structure

### 4. Security Review

The Security Review Agent uses:

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

Semgrep provides static-analysis evidence while the LLM interprets the findings.

### 5. AI Test Generation

The Test Writer Agent generates `pytest` tests for modified functions.

Generated tests are not trusted automatically.

They must be:

1. syntax validated
2. executed
3. checked for success/failure
4. measured for coverage

### 6. Sandboxed Execution

Repository code and generated tests are untrusted.

They must be executed inside Docker with restrictions such as:

- execution timeout
- memory limits
- process limits
- network restrictions
- temporary filesystem
- container cleanup

### 7. Coverage Measurement

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

### 8. Merge Readiness Score

The final score is deterministic and ranges from:

```text
0–100
```

It is based on structured evidence from:

- security analysis
- test results
- coverage

The LLM must not arbitrarily choose the final score.

---

# Context Window Management

A Pull Request can contain a small or very large amount of code.

Quorum must **never send the entire repository to the LLM by default**.

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

Each LLM call has a bounded context budget.

Different agents receive only the context they need.

### Security Agent

```text
Changed Code
+
AST Context
+
Semgrep Findings
```

### Test Writer Agent

```text
Modified Functions
+
AST Context
+
Relevant Tests
+
Dependencies
```

### Synthesis

```text
Security Result
+
Test Result
+
Coverage Result
```

For large Pull Requests, code should be split into meaningful semantic chunks such as functions, classes, or related files.

---

# Technology Stack

All core technologies are intended to be free, open-source, or locally runnable.

| Component | Technology | Purpose |
|---|---|---|
| Language | Python | Main development language |
| Backend | FastAPI | API and GitHub webhook server |
| Server | Uvicorn | Runs FastAPI |
| LLM Runtime | Ollama | Local LLM inference |
| Coding Model | Qwen2.5-Coder | Code reasoning and generation |
| GitHub | GitHub App | PR integration |
| Security | Semgrep | Static security analysis |
| Code Analysis | Python AST | Structural code analysis |
| Testing | pytest | Test execution |
| Coverage | pytest-cov | Coverage measurement |
| Sandbox | Docker | Safe execution of untrusted code |
| Database | PostgreSQL | Persistent analysis data |
| ORM | SQLAlchemy | Database access |
| Migration | Alembic | Database migrations |
| Validation | Pydantic | Data validation |
| HTTP | httpx | External API requests |
| CI | GitHub Actions | Automated testing |

---

# Project Structure

```text
Quorum/
│
├── README.md
├── roadmap.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── src/
│   └── quorum/
│       ├── main.py
│       ├── config.py
│       │
│       ├── api/
│       │   ├── health.py
│       │   └── webhooks.py
│       │
│       ├── github/
│       │   ├── auth.py
│       │   └── client.py
│       │
│       ├── orchestrator/
│       │   └── runner.py
│       │
│       ├── agents/
│       │   ├── security/
│       │   ├── test_writer/
│       │   └── synthesis/
│       │
│       ├── analysis/
│       │   ├── diff.py
│       │   ├── ast_parser.py
│       │   ├── context_builder.py
│       │   ├── semgrep.py
│       │   └── coverage.py
│       │
│       ├── llm/
│       │   ├── base.py
│       │   └── ollama_provider.py
│       │
│       ├── sandbox/
│       │   └── docker_runner.py
│       │
│       └── database/
│           ├── models.py
│           └── session.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── evaluation/
├── prompts/
├── docker/
└── .github/
    └── workflows/
```

---

# API

The initial API should remain small.

### `GET /`

Basic application information.

### `GET /health`

Health check.

### `POST /webhooks/github`

Receives GitHub webhook events.

The webhook endpoint should:

1. Verify `X-Hub-Signature-256`.
2. Identify the event.
3. Validate the payload.
4. Ignore unsupported events.
5. Start the review process.
6. Return quickly.

Long-running AI analysis should not block the webhook request.

---

# Development Workflow

Before implementing anything, an AI coding agent should:

```text
1. Read README.md
2. Read roadmap.md
3. Inspect the existing repository
4. Identify the current implementation phase
5. Implement only the required phase
6. Run tests
7. Update documentation when necessary
```

The detailed implementation plan is maintained in:

```text
roadmap.md
```

`README.md` explains **what Quorum is**.

`roadmap.md` explains **what needs to be built and in what order**.

---

# Important Development Rules

### 1. Do Not Overengineer the MVP

Do not introduce unnecessary infrastructure such as:

- Kubernetes
- Kafka
- Redis
- Celery
- microservices
- vector databases
- paid LLM APIs

unless the roadmap explicitly requires them.

### 2. Never Execute Untrusted Code Directly

Repository code and AI-generated tests must run through the Docker sandbox.

### 3. Do Not Invent Evidence

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

### 4. Keep LLM Context Bounded

Do not send the entire repository to the LLM.

Use:

```text
Filter → Rank → Chunk → Analyze → Aggregate
```

### 5. Keep Components Separated

The following responsibilities should remain separate:

```text
GitHub Integration
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
```

### 6. Test New Features

Every important component should have unit or integration tests.

---

# Evaluation

Evaluation is part of the MVP.

The system should be tested against a manually labeled Pull Request dataset.

The evaluation should measure:

- security precision
- security recall
- F1 score
- generated-test pass rate
- coverage delta
- overall review quality

The evaluation results should be reproducible.

---

# MVP Scope

The MVP must contain:

- GitHub App
- webhook verification
- Pull Request extraction
- diff extraction
- Python AST analysis
- context management
- Semgrep
- Security Review Agent
- Test Writer Agent
- Ollama
- Docker sandbox
- pytest
- pytest-cov
- PostgreSQL
- deterministic Merge Readiness Score
- GitHub PR comment
- evaluation harness

### Post-MVP

The planned post-MVP feature is:

**Ask Quorum**

Users will be able to ask questions about the review through GitHub comments.

This should not delay the MVP.

---

# Getting Started

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment configuration:

```text
.env
```

using:

```text
.env.example
```

Run the API:

```bash
uvicorn src.quorum.main:app --reload
```

Run tests:

```bash
pytest
```

---

# Project Status

The project is being developed incrementally according to `roadmap.md`.

The implementation order is:

```text
Project Setup
      ↓
FastAPI
      ↓
GitHub App
      ↓
Webhook
      ↓
GitHub API
      ↓
Orchestrator
      ↓
Diff + AST
      ↓
Context Builder
      ↓
Docker Sandbox
      ↓
Security Agent
      ↓
Test Writer Agent
      ↓
Coverage
      ↓
Synthesis
      ↓
GitHub Comment
      ↓
Evaluation
      ↓
Ask Quorum
```

---

# Core Philosophy

Quorum is not simply an LLM that comments on code.

It is an **evidence-driven Pull Request review system**.

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
```

> **Quorum: Don't just ask AI if the code is ready. Measure it.**
