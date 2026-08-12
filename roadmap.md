# Quorum — AI-Powered Pull Request Reviewer

> This file is the implementation roadmap and project context for human developers and AI coding agents.
> AI coding agents MUST read this file before modifying the project.

## 1. Project Identity

**Quorum** is a GitHub App for AI-assisted Pull Request review.

Core principle:

> **Measure, don't merely claim.**

Quorum combines GitHub PR data, diff/AST analysis, Semgrep evidence, LLM reasoning, generated tests, sandboxed execution, coverage measurement, and deterministic synthesis.

```text
GitHub PR
  ↓
Webhook → FastAPI → Orchestrator
  ↓
Diff + AST + Semgrep
  ↓
┌───────────────────────┬──────────────────────┐
│ Security Review Agent │ Test Writer Agent     │
│ Semgrep + LLM         │ AST + LLM + pytest   │
└───────────────────────┴──────────────────────┘
  ↓
Docker sandbox + coverage
  ↓
Deterministic Merge Readiness Score
  ↓
PostgreSQL + GitHub PR Comment
```

## 2. MVP Scope

### MUST BUILD

- GitHub App installation and authentication
- Pull Request webhook ingestion
- `X-Hub-Signature-256` verification
- PR metadata, changed files, diff, and checkout
- Python AST extraction of modified functions/classes
- Bounded LLM context builder
- Semgrep security analysis
- Security Review Agent
- Test Writer Agent
- Docker sandbox for generated tests
- pytest execution
- pytest-cov coverage measurement
- Deterministic 0–100 merge-readiness score
- PostgreSQL persistence
- GitHub PR review comment
- 15–20 PR evaluation harness with Precision, Recall, F1, coverage delta, and test pass rate

### POST-MVP

Ask Quorum chatbot using `@quorum`.

If time is limited, remove the chatbot first. Do not remove evaluation.

## 3. Out of Scope

Do not add unless explicitly requested:

- React dashboard
- Redis
- Celery
- Kafka/RabbitMQ
- Kubernetes
- Microservices
- Paid LLM APIs
- Paid hosting for initial development
- Multi-language AST support
- Vector databases/RAG
- Enterprise authentication

Keep the MVP simple.

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.12/3.13 | Main language |
| Backend | FastAPI | API + webhook handling |
| Server | Uvicorn | Run FastAPI |
| LLM runtime | Ollama | Local inference |
| Coding model | Qwen2.5-Coder 7B | Code reasoning/generation |
| GitHub | GitHub App + REST API | PR integration |
| Security | Semgrep | Static security evidence |
| Parsing | Python AST | Code structure/function extraction |
| Testing | pytest | Execute generated tests |
| Coverage | pytest-cov | Coverage measurement |
| Sandbox | Docker | Isolate untrusted test execution |
| Database | PostgreSQL | Persistent analysis data |
| ORM | SQLAlchemy | Database access |
| Migration | Alembic | Schema migrations |
| HTTP | httpx | HTTP requests |
| Validation | Pydantic | Structured validation |
| CI | GitHub Actions | Automated tests |
| Tunnel | Cloudflare Quick Tunnel | Local webhook development |

All core development technologies should be free/open-source or locally runnable.

## 5. LLM Architecture

Agents MUST depend on an abstraction, not directly on Ollama:

```text
LLMProvider
    ↓
OllamaProvider
    ↓
Qwen2.5-Coder
```

Example interface:

```python
class LLMProvider:
    async def generate(self, prompt: str) -> str:
        ...
```

Configuration should include:

```text
OLLAMA_BASE_URL
OLLAMA_MODEL
LLM_CONTEXT_LIMIT
LLM_OUTPUT_LIMIT
```

## 6. Context Window Management — CRITICAL

### Problem

Users can submit tiny or huge PRs. Quorum MUST NOT send the whole repository, entire PR history, all comments, or unlimited tool output to one LLM call.

A PR does not permanently increase Quorum's context window. Every analysis gets its own bounded context budget.

```text
PR #101 → Context Budget A
PR #102 → Context Budget B
```

### Hard Rules

1. Every LLM call has an explicit context budget.
2. Reserve output space inside that budget.
3. Never send the entire repository by default.
4. Never send unlimited Semgrep output.
5. Never let one user's repository context leak into another analysis.
6. Large PRs MUST be split into semantic chunks.
7. The final synthesis should consume structured results instead of the whole source again.

### Context pipeline

```text
Repository
  ↓
PR diff
  ↓
Changed files
  ↓
Changed functions/classes
  ↓
AST context
  ↓
Semgrep findings
  ↓
Relevant surrounding code/tests
  ↓
Rank + filter
  ↓
Token budget
  ↓
LLM
```

### Priority when context is too large

1. Changed code
2. Changed functions/classes
3. Relevant Semgrep findings
4. Required surrounding code
5. Relevant existing tests
6. PR metadata
7. Unrelated repository context — exclude

### Large PR strategy

Do not solve large PRs by increasing the prompt indefinitely.

```text
Large PR
  ↓
Semantic grouping by function/class/module
  ↓
Chunk 1 → LLM
Chunk 2 → LLM
Chunk 3 → LLM
  ↓
Structured results
  ↓
Final synthesis
```

Prefer semantic boundaries rather than arbitrary character boundaries.

### Tool-output bounding

```text
Semgrep JSON
  ↓
Parse
  ↓
Filter relevant findings
  ↓
Deduplicate
  ↓
Rank severity/relevance
  ↓
Context budget
  ↓
LLM
```

### Agent-specific contexts

Do NOT give every agent the same prompt.

**Security Agent:** changed code + AST context + relevant Semgrep findings + required imports/config.

**Test Writer:** modified function + AST context + dependencies + relevant existing tests.

**Synthesis:** structured security result + test result + coverage result. It normally does not need the entire source again.

### Context Builder

Create:

```text
analysis/context_builder.py
```

Responsibilities:

- Select relevant files/functions
- Select AST context
- Select relevant Semgrep findings
- Select relevant tests
- Rank context
- Estimate token usage
- Enforce context limits
- Chunk oversized analysis
- Produce final bounded LLM input

No agent should independently create unlimited prompts.

### Persistent data vs prompt context

PostgreSQL may store useful analysis data, but stored data is NOT automatically sent to the LLM.

```text
PostgreSQL
  ↓
Analysis repository
  ↓
Context Builder
  ↓
Bounded prompt
  ↓
LLM
```

### Chatbot context

For Ask Quorum, do not resend the complete conversation or PR every time.
Use:

```text
Current question
+ relevant previous messages
+ stored PR analysis summary
+ requested evidence
```

Older irrelevant messages should be summarized or omitted.

### Evidence preservation

If context must be compressed, preserve factual evidence such as:

- file path
- line number
- Semgrep rule
- severity
- test result
- coverage measurement
- error message

Compression must not invent facts.

## 7. Repository Structure

```text
Quorum/
├── README.md
├── roadmap.md
├── proposal.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
│
├── src/quorum/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── health.py
│   │   └── webhooks.py
│   ├── github/
│   │   ├── auth.py
│   │   ├── client.py
│   │   └── webhook.py
│   ├── orchestrator/
│   │   └── runner.py
│   ├── agents/
│   │   ├── security/
│   │   │   ├── agent.py
│   │   │   └── schemas.py
│   │   ├── test_writer/
│   │   │   ├── agent.py
│   │   │   └── schemas.py
│   │   └── synthesis/
│   │       ├── scorer.py
│   │       └── schemas.py
│   ├── analysis/
│   │   ├── diff.py
│   │   ├── ast_parser.py
│   │   ├── context_builder.py
│   │   ├── semgrep.py
│   │   └── coverage.py
│   ├── llm/
│   │   ├── base.py
│   │   └── ollama_provider.py
│   ├── sandbox/
│   │   ├── docker_runner.py
│   │   └── limits.py
│   ├── database/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── repositories.py
│   └── schemas/
│       ├── github.py
│       ├── analysis.py
│       └── common.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── evaluation/
│   ├── dataset/
│   ├── scripts/
│   └── results/
├── prompts/
│   ├── security/
│   ├── test_writer/
│   └── chatbot/
├── docker/sandbox/
└── .github/workflows/ci.yml
```

## 8. API

Initial endpoints only:

```text
GET /
GET /health
POST /webhooks/github
```

`POST /webhooks/github` must:

1. Read the raw request body.
2. Verify `X-Hub-Signature-256`.
3. Read `X-GitHub-Event`.
4. Parse the payload.
5. Ignore unsupported events.
6. Process `pull_request` actions: `opened`, `reopened`, `synchronize`.
7. Start background analysis.
8. Return quickly.

Do not create public endpoints for internal agents.

## 9. Orchestrator

```text
Webhook
  ↓
Orchestrator
  ├── PR metadata
  ├── diff
  ├── changed files
  ├── checkout
  ├── AST
  ├── bounded contexts
  ├── Semgrep
  ├── Security Agent
  ├── Test Writer Agent
  ├── sandbox
  ├── coverage
  ├── synthesis
  ├── database
  └── GitHub comment
```

The orchestrator coordinates components; it should not contain their internal implementation.

## 10. Security Agent

```text
PR code
  ↓
Semgrep
  ↓
Structured findings
  ↓
Relevant diff + AST
  ↓
Bounded LLM context
  ↓
Security result
```

Semgrep provides evidence. The LLM explains and reasons over the evidence.

Structured result example:

```json
{
  "findings": [
    {
      "severity": "high",
      "title": "Potential SQL Injection",
      "file": "app/users.py",
      "line": 42,
      "evidence": "Semgrep rule ...",
      "explanation": "...",
      "confidence": 0.91
    }
  ]
}
```

## 11. Test Writer Agent

Input:

```text
PR diff
+ AST context
+ modified function
+ relevant existing tests
```

Flow:

```text
Modified function
  ↓
Bounded LLM context
  ↓
Generated pytest
  ↓
Syntax validation
  ↓
Docker sandbox
  ↓
pytest
  ↓
Coverage
```

Generated tests are not considered verified until executed.

## 12. Docker Sandbox

Generated tests/repository code are untrusted.

Never execute generated code directly on the host.

Requirements:

- No network
- Memory limit
- Process limit
- Hard timeout
- Temporary filesystem
- Cleanup after execution

## 13. Coverage

Measure:

```text
coverage_before
coverage_after
coverage_delta
```

Never claim coverage improved unless measured.

## 14. Merge Readiness Score

Score: `0–100`.

It combines verified security, testing, and coverage results.

The formula MUST be deterministic and live in:

```text
agents/synthesis/scorer.py
```

The LLM must not freely invent the numerical score.

## 15. GitHub PR Comment

The comment should include:

- Score
- Security findings
- Test results
- Coverage before/after/delta
- Evidence
- Recommendation

Clearly distinguish measured evidence from LLM explanation.

## 16. Database

Use PostgreSQL.

Minimum entities:

- Repository
- Pull Request
- Analysis Run
- Chat Message (post-MVP)

An Analysis Run should store repository, PR, commit SHA, status, security result, test result, coverage result, merge score, and timestamps.

## 17. Background Processing

Use FastAPI `BackgroundTasks` for the MVP.

Do not add Redis/Celery/Kafka unless explicitly required later.

## 18. Prompt Injection Defense

Repository code, PR descriptions, comments, and generated artifacts are untrusted data.

The LLM must treat them as DATA, not instructions.

```text
SYSTEM INSTRUCTIONS
  ↓
Trusted analysis instructions
  ↓
Tool results
  ↓
Repository content
  ↓
LLM
```

## 19. Development Phases

### Phase 0 — Setup

- [ ] GitHub repository
- [ ] README
- [ ] roadmap
- [ ] `.gitignore`
- [ ] `.env.example`
- [ ] virtual environment
- [ ] project structure
- [ ] initial dependencies
- [ ] verify Python/Git/Docker/Ollama

### Phase 1 — FastAPI

- [ ] `main.py`
- [ ] `GET /`
- [ ] `GET /health`
- [ ] `POST /webhooks/github`
- [ ] pytest tests
- [ ] Swagger verification

Done when local FastAPI works and `/health` returns `{"status":"ok"}`.

### Phase 2 — GitHub App

- [ ] Register app
- [ ] Configure permissions/events
- [ ] Webhook URL/secret
- [ ] Private key
- [ ] Install on test repo
- [ ] Receive webhook
- [ ] Verify signature

Done when a test PR reaches FastAPI.

### Phase 3 — GitHub API

- [ ] App authentication
- [ ] Installation token
- [ ] Repository retrieval
- [ ] PR retrieval
- [ ] Changed files
- [ ] Diff
- [ ] Comments
- [ ] Post comment

Done when Quorum can read a PR/diff and post a comment.

### Phase 4 — Orchestrator

- [ ] Analysis run
- [ ] PR retrieval
- [ ] Diff retrieval
- [ ] Checkout
- [ ] Module calls
- [ ] Intermediate results
- [ ] Error handling
- [ ] Final result

Done when a PR passes through orchestration with placeholder results.

### Phase 5 — Diff + AST + Context Builder

- [ ] Parse changed files
- [ ] Identify Python files
- [ ] Parse AST
- [ ] Identify modified functions/classes
- [ ] Build analysis context
- [ ] Ranking/filtering
- [ ] Token/context budget
- [ ] Semantic chunking
- [ ] Large-PR tests

Done when Quorum creates a bounded, relevant context for an LLM call.

### Phase 6 — Sandbox

- [ ] Docker environment
- [ ] Network disabled
- [ ] Resource limits
- [ ] Timeout
- [ ] pytest execution
- [ ] stdout/stderr/exit code
- [ ] cleanup

Done when generated tests execute safely in Docker.

### Phase 7 — Security Agent

- [ ] Semgrep
- [ ] Parse JSON
- [ ] Filter findings
- [ ] Bounded security prompt
- [ ] Ollama
- [ ] Structured response
- [ ] Validation
- [ ] Tests

Done when a known-vulnerable PR produces an evidence-grounded finding.

### Phase 8 — Test Writer

- [ ] Test-generation prompt
- [ ] Bounded test context
- [ ] pytest generation
- [ ] Syntax validation
- [ ] Docker execution
- [ ] Results
- [ ] Coverage
- [ ] Coverage delta
- [ ] Persistence

Done when tests are generated, executed, and measured.

### Phase 9 — Synthesis

- [ ] Scoring formula
- [ ] Deterministic scorer
- [ ] Security result
- [ ] Test result
- [ ] Coverage
- [ ] 0–100 score
- [ ] Recommendation

Done when identical inputs always produce the same score.

### Phase 10 — PR Comment

- [ ] Formatter
- [ ] Score
- [ ] Security
- [ ] Tests
- [ ] Coverage
- [ ] Evidence
- [ ] Recommendation
- [ ] GitHub API posting

Done when a real PR receives a complete Quorum review.

### Phase 11 — MVP Freeze

Before freezing:

- [ ] GitHub App
- [ ] Webhook verification
- [ ] PR extraction
- [ ] AST
- [ ] Context management
- [ ] Semgrep
- [ ] Security Agent
- [ ] Test Writer
- [ ] Docker
- [ ] pytest
- [ ] Coverage
- [ ] Merge score
- [ ] PR comment
- [ ] PostgreSQL

Then freeze major features.

### Phase 12 — Evaluation

- [ ] 15–20 real PRs
- [ ] Manual labels
- [ ] Run Quorum
- [ ] Predictions
- [ ] Precision
- [ ] Recall
- [ ] F1
- [ ] Coverage delta
- [ ] Test pass rate
- [ ] Save reproducible results

### Phase 13 — Ask Quorum

Only after MVP + evaluation.

- [ ] Detect `@quorum`
- [ ] Retrieve PR analysis
- [ ] Retrieve relevant chat
- [ ] Bounded chatbot context
- [ ] Generate response
- [ ] Post reply
- [ ] Prevent self-trigger loops
- [ ] Prompt-injection defenses

### Phase 14 — Hardening

- [ ] Invalid webhook signature
- [ ] Forged webhook
- [ ] Repository prompt injection
- [ ] PR comment injection
- [ ] Chatbot prompt injection
- [ ] Oversized PR
- [ ] Context overflow
- [ ] Sandbox timeout
- [ ] Sandbox network access
- [ ] Resource exhaustion
- [ ] Unauthorized repository access
- [ ] Chatbot self-reply loop

## 20. Current Development Status

AI agents MUST update this section only when a milestone is actually complete.

```text
Phase: Project Initialization

Completed:
- [x] Project concept defined
- [x] Tech stack selected
- [x] GitHub repository planned
- [x] Roadmap created
- [x] .gitignore created
- [x] requirements.txt initialized
- [ ] FastAPI implementation
- [ ] GitHub App
- [ ] Webhook
- [ ] PostgreSQL
- [ ] Orchestrator
- [ ] Diff/AST
- [ ] Context Builder
- [ ] Semgrep
- [ ] Security Agent
- [ ] Docker sandbox
- [ ] Test Writer
- [ ] Coverage
- [ ] Merge score
- [ ] Evaluation
- [ ] Chatbot
```

## 21. Git Workflow

Main branch:

```text
main
```

Feature branches:

```text
feature/github-app
feature/orchestrator
feature/security-agent
feature/test-writer
feature/context-management
feature/evaluation
feature/chatbot
```

Rules:

1. Do not work directly on `main` for major features.
2. Make small commits.
3. Run tests before committing.
4. Never commit secrets.
5. Never commit `.env` or private keys.
6. Never commit local model files.
7. Never commit generated temporary repositories.

## 22. AI Coding Agent Rules

Before editing:

1. Read `roadmap.md` completely.
2. Inspect the repository.
3. Determine the current phase.
4. Identify the smallest next incomplete task.
5. Inspect relevant existing code.

Then:

1. Explain files to change.
2. Explain why.
3. Implement only the current task.
4. Add/update tests.
5. Run relevant tests.
6. Report results.
7. Update status only if actually complete.

Additional hard rules:

- Do not implement future phases early.
- Do not overengineer.
- Do not add unnecessary dependencies.
- Do not use paid services.
- Do not commit secrets.
- Do not execute untrusted code outside Docker.
- Do not invent tool/test/coverage/security results.
- Do not put an entire repository into an LLM prompt.
- Respect every configured context budget.
- Preserve existing behavior.

## 23. Definition of Done

Final project completion requires:

- [ ] GitHub App
- [ ] Webhook verification
- [ ] PR ingestion
- [ ] Diff extraction
- [ ] AST extraction
- [ ] Small- and large-PR context management
- [ ] Semgrep
- [ ] Security Agent
- [ ] Ollama integration
- [ ] Test Writer
- [ ] Docker sandbox
- [ ] pytest
- [ ] Coverage delta
- [ ] Deterministic merge-readiness score
- [ ] PostgreSQL persistence
- [ ] GitHub PR comments
- [ ] 15–20 PR evaluation dataset
- [ ] Precision
- [ ] Recall
- [ ] F1
- [ ] Coverage delta
- [ ] Test pass rate
- [ ] Prompt-injection tests
- [ ] Sandbox security tests
- [ ] Large-PR context tests
- [ ] Documentation
- [ ] Demo repository
- [ ] Final demonstration

Optional:

- [ ] Ask Quorum chatbot

## 24. Final Architecture

```text
                         GitHub
                            │
                     Pull Request Event
                            │
                            ▼
                  GitHub App Webhook
                            │
                            ▼
                  Signature Verification
                            │
                            ▼
                         FastAPI
                            │
                            ▼
                    Background Task
                            │
                            ▼
                      Orchestrator
                            │
                            ▼
                  Diff + AST Extraction
                            │
                            ▼
                     Context Builder
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Security Context             Test Context
              │                           │
              ▼                           ▼
       Security Agent              Test Writer Agent
              │                           │
           Semgrep                     Ollama
              │                           │
           Ollama                 Generated pytest
              │                           │
              │                     Docker Sandbox
              │                           │
              │                         pytest
              │                           │
              │                       Coverage
              │                           │
              └─────────────┬─────────────┘
                            │
                            ▼
                    Result Synthesis
                            │
                            ▼
                 Merge Readiness Score
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
             PostgreSQL          GitHub PR Comment
                 │
                 ▼
          Ask Quorum Chatbot
             (post-MVP)
```

## 25. AI Agent Starting Instruction

```text
Read roadmap.md completely.

Inspect the current repository.

Determine the current development phase from
Current Development Status.

Do not implement future phases.

Identify the smallest next incomplete task.

Before changing code:
1. Explain what files need to change.
2. Explain why.
3. Implement only that task.
4. Add/update tests.
5. Run relevant tests.
6. Report what was completed.
7. Update Current Development Status only if the milestone is actually complete.

Do not add unnecessary dependencies.
Do not introduce architecture unless required.
Do not use paid services.
Do not commit secrets.
Do not execute untrusted repository code outside Docker.
Do not invent tool results, test results, coverage, or security findings.
Do not put an entire repository into an LLM prompt.
Respect every configured context budget.
```

## 26. First Implementation Task

At the current project stage, implement only:

```text
Create the initial FastAPI application.

GET /
GET /health
POST /webhooks/github
```

Do NOT implement yet:

- GitHub App authentication
- Semgrep
- LLM
- Docker sandbox
- PostgreSQL
- Security Agent
- Test Writer

The first success condition is:

```text
GitHub PR
    ↓
POST /webhooks/github
    ↓
FastAPI receives the event
```

Then continue one roadmap phase at a time.
