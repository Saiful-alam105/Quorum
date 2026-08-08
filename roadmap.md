# Quorum --- Detailed Implementation Roadmap

## Goal

Build and freeze a defensible 70-day MVP of Quorum, a GitHub App that
reviews Pull Requests using evidence-grounded AI agents, verifies
generated tests in a sandbox, produces a merge-readiness score, and
evaluates itself on 15--20 manually labeled real Pull Requests.

## Core Development Rule

Build the smallest complete working path first:

GitHub PR → Webhook → FastAPI → Orchestrator → Security/Test Agents →
Verification → Merge Score → PR Comment → PostgreSQL

Do not begin the chatbot, dashboard, or optional features before the
core pipeline and evaluation harness work.

## 1. Tech Stack

| Layer | Technology | Cost | Why |
|---|---|---|---|
| **Language** | Python 3.12/3.13 | Free | One language for backend, AST parsing, orchestration, GitHub integration, and tests |
| **Backend** | FastAPI | Free / Open Source | Receives GitHub webhooks and provides the backend API |
| **Server** | Uvicorn | Free / Open Source | Runs the FastAPI application |
| **LLM** | Ollama + Qwen2.5-Coder 7B | Free / Local | Runs the coding model locally without API charges |
| **LLM API** | Ollama Local API | Free / Local | Allows Python to communicate with the local model over HTTP |
| **GitHub** | GitHub App + Webhooks + REST API | Free | Receives PR events, retrieves PR data, and posts review comments |
| **Security Analysis** | Semgrep Community CLI | Free | Produces deterministic security findings used as evidence |
| **Code Parsing** | Python `ast` | Free | Extracts modified functions and structural code context |
| **Testing** | pytest | Free / Open Source | Runs generated tests |
| **Coverage** | pytest-cov | Free / Open Source | Measures test coverage changes |
| **Sandbox** | Docker | Free for intended personal/student use | Isolates generated test execution |
| **Database** | PostgreSQL | Free / Open Source | Stores repositories, PRs, analysis runs, and chat history |
| **ORM** | SQLAlchemy | Free / Open Source | Provides database access from Python |
| **Migrations** | Alembic | Free / Open Source | Manages database schema migrations |
| **HTTP** | httpx | Free / Open Source | Handles GitHub and local API communication |
| **Validation** | Pydantic | Free / Open Source | Validates application data and API schemas |
| **Version Control** | Git + GitHub | Free | Source control and team collaboration |
| **CI** | GitHub Actions | Free within limits | Automated testing and quality checks |
| **Webhook Development** | Cloudflare Quick Tunnel | Free | Exposes local FastAPI server to GitHub during development |
| **UI** | GitHub PR Comments | Free | No separate frontend is required |


### LLM choice

The proposal originally names Anthropic Claude, but Claude API is not a
zero-cost solution.

For a strictly free implementation, use:

``` text
Ollama
   ↓
Qwen2.5-Coder 7B
   ↓
localhost:11434
   ↓
FastAPI
```

Keep the LLM behind an interface such as `LLMProvider`, so the model can
be replaced later without changing the agents.

------------------------------------------------------------------------

## 2. Repository

Yes. Maintain one main GitHub repository:

``` text
Quorum/
├── README.md
├── roadmap.md
├── proposal.md
├── .gitignore
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── src/
│   └── quorum/
│       ├── main.py
│       ├── config.py
│       ├── api/
│       ├── github/
│       ├── orchestrator/
│       ├── agents/
│       │   ├── security/
│       │   ├── test_writer/
│       │   └── synthesis/
│       ├── analysis/
│       │   ├── semgrep.py
│       │   ├── ast_parser.py
│       │   └── coverage.py
│       ├── llm/
│       │   ├── base.py
│       │   └── ollama_provider.py
│       ├── sandbox/
│       ├── database/
│       └── schemas/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── evaluation/
│   ├── dataset/
│   ├── scripts/
│   └── results/
├── prompts/
├── docker/
├── docs/
└── .github/
    └── workflows/
        └── ci.yml
```

Do not commit `.env`, GitHub private keys, API keys, model files, or
unnecessary large datasets.

------------------------------------------------------------------------

## 3. Branch Strategy

Use:

``` text
main
├── feature/github-app
├── feature/orchestrator
├── feature/security-agent
├── feature/test-writer
├── feature/evaluation
└── feature/chatbot
```

Merge a feature only after its tests pass.

------------------------------------------------------------------------

# 4. 70-Day Roadmap

## Phase 0 --- Setup (Day 1)

-   Create GitHub repository
-   Clone repository
-   Create Python virtual environment
-   Create folder structure
-   Create README
-   Create roadmap
-   Create `.env.example`
-   Add `.gitignore`
-   Install core dependencies
-   Install Docker
-   Install Ollama

Definition of done:

``` text
Python
Git
Docker
Ollama
```

all work locally.

------------------------------------------------------------------------

## Phase 1 --- FastAPI Skeleton (Days 2--3)

Create:

``` text
GET /
GET /health
POST /webhooks/github
```

Add pytest tests.

Definition of done:

``` bash
uvicorn quorum.main:app --reload
```

works and `/health` returns HTTP 200.

------------------------------------------------------------------------

## Phase 2 --- GitHub App (Days 4--7)

-   Register GitHub App
-   Configure webhook
-   Generate webhook secret
-   Generate App private key
-   Configure minimum repository permissions
-   Subscribe to Pull Request events
-   Subscribe to issue-comment events
-   Install App on a test repository
-   Verify `X-Hub-Signature-256`

Day 7 milestone:

``` text
Open PR
 ↓
GitHub webhook
 ↓
FastAPI
 ↓
Read PR information
 ↓
Post test comment
```

AI is not required yet.

------------------------------------------------------------------------

## Phase 3 --- GitHub API Layer (Days 8--10)

Implement:

``` text
get_installation_token()
get_repository()
get_pull_request()
get_pr_files()
get_pr_diff()
get_pr_comments()
create_pr_comment()
```

Keep these inside the GitHub service layer.

Definition of done:

The application can receive a PR, authenticate, read it, and post a
comment.

------------------------------------------------------------------------

## Phase 4 --- PostgreSQL (Days 11--13)

Create:

``` text
repositories
pull_requests
analysis_runs
chat_messages
```

Use SQLAlchemy + Alembic.

Definition of done:

A PR creates repository, PR and analysis-run records.

------------------------------------------------------------------------

## Phase 5 --- Orchestrator (Days 14--16)

Build:

``` text
Orchestrator
├── clone PR
├── extract diff
├── extract AST
├── Security Agent
├── Test Writer Agent
└── Synthesis
```

Use FastAPI `BackgroundTasks`.

Do not introduce Redis/Celery.

------------------------------------------------------------------------

## Phase 6 --- Diff + AST (Days 17--21)

Extract:

-   changed files
-   added/removed lines
-   modified functions
-   classes
-   arguments
-   decorators
-   source ranges
-   surrounding function context

Definition of done:

The system can identify the modified Python functions in a PR.

------------------------------------------------------------------------

## Phase 7 --- Semgrep (Days 22--25)

Pipeline:

``` text
PR code
 ↓
Semgrep
 ↓
JSON findings
```

Store:

``` text
rule ID
severity
file
line
message
code location
```

The LLM must reason over these findings rather than inventing security
issues from nothing.

------------------------------------------------------------------------

## Phase 8 --- LLM Layer (Days 26--27)

Create:

``` text
llm/base.py
llm/ollama_provider.py
```

Interface:

``` python
class LLMProvider:
    async def generate(self, prompt: str) -> str:
        ...
```

Run Qwen2.5-Coder locally through Ollama.

Definition of done:

Python can send a prompt and receive a model response.

------------------------------------------------------------------------

## Phase 9 --- Security Agent (Days 28--31)

Input:

``` text
PR diff
AST context
Semgrep findings
```

Output:

``` json
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

The agent must explain findings using the supplied evidence.

------------------------------------------------------------------------

## Phase 10 --- Docker Sandbox (Days 32--34)

Run generated tests inside a temporary Docker container.

Requirements:

-   no network
-   memory limit
-   process limit
-   hard timeout
-   temporary filesystem
-   container cleanup

Definition of done:

A valid test passes and an intentionally unsafe/infinite test is
terminated.

------------------------------------------------------------------------

## Phase 11 --- Test Writer (Days 35--42)

Input:

``` text
PR diff
AST context
modified function
existing test structure
```

Pipeline:

``` text
LLM
 ↓
Generated pytest
 ↓
Syntax validation
 ↓
Docker
 ↓
pytest
 ↓
coverage
```

Measure:

``` text
coverage_before
coverage_after
coverage_delta
```

------------------------------------------------------------------------

## Phase 12 --- Synthesis (Days 43--45)

Combine:

``` text
Security result
+
Test result
```

into:

``` text
Merge Readiness Score: 0–100
```

The numerical scoring formula must be deterministic and documented. Do
not allow the LLM to freely invent the final score.

------------------------------------------------------------------------

## Phase 13 --- PR Comment + MVP Freeze (Days 46--49)

Post:

``` text
## Quorum Review

### Merge Readiness
82/100

### Security
1 High
1 Medium

### Tests
Generated tests passed
Coverage increased

### Evidence
...

### Recommendation
...
```

Day 49:

``` text
MVP FEATURE FREEZE
```

Do not add new core features after this point.

------------------------------------------------------------------------

## Phase 14 --- Evaluation Harness (Days 50--56)

This phase is mandatory.

Use:

``` text
15–20 real Pull Requests
```

Manually label expected security findings.

Measure:

``` text
Precision
Recall
F1
Coverage delta
Test pass rate
```

Store evaluation data and results in:

``` text
evaluation/
```

Definition of done:

The results can be reproduced from the documented dataset and scripts.

------------------------------------------------------------------------

## Phase 15 --- Ask Quorum Chatbot (Days 57--63)

Only start after MVP freeze and evaluation are complete.

Example:

``` text
@quorum why was this marked as a security risk?
```

Ground the response in:

``` text
question
+
PR diff
+
Semgrep findings
+
Security Agent result
+
Test Writer result
```

Repository code and PR comments remain untrusted input.

If time is limited, remove this feature first. Never remove the
evaluation harness.

------------------------------------------------------------------------

## Phase 16 --- Hardening + Demo (Days 64--70)

Demonstrate:

-   invalid webhook signature
-   repository prompt injection
-   chatbot prompt injection
-   sandbox escape attempt
-   chatbot self-reply prevention
-   unauthorized repository access

Prepare:

``` text
clean demo repository
known-bad PR
known-good PR
prompt injection example
generated test example
evaluation results
backup demo video
```

------------------------------------------------------------------------

# 5. Final Architecture

``` text
                    GitHub
                       |
                 Pull Request
                       |
                       v
              GitHub App Webhook
                       |
                       v
                FastAPI Endpoint
                       |
              Signature Verification
                       |
                       v
             BackgroundTasks
                       |
                       v
                 Orchestrator
                       |
          +------------+------------+
          |                         |
          v                         v
    Security Agent           Test Writer Agent
          |                         |
       Semgrep                   AST
          |                         |
          v                         v
       Ollama                    Ollama
          |                         |
          v                         v
   Security Result          Generated Tests
                                    |
                                    v
                              Docker Sandbox
                                    |
                                    v
                                  pytest
                                    |
                                    v
                               Coverage
          |                         |
          +------------+------------+
                       |
                       v
               Result Synthesis
                       |
                       v
             Merge Readiness Score
                       |
             +---------+---------+
             |                   |
             v                   v
        PostgreSQL          GitHub Comment
```

------------------------------------------------------------------------

# 6. Security Principles

1.  Never trust repository content.
2.  Never trust PR comments.
3.  Never execute generated code directly.
4.  Verify every GitHub webhook signature.
5.  Use minimum GitHub permissions.
6.  Keep secrets outside Git.
7.  Use short-lived GitHub App installation tokens.
8.  Do not expose the PostgreSQL database publicly.

------------------------------------------------------------------------

# 7. Definition of Done

-   [ ] GitHub App works
-   [ ] Webhook signature verification works
-   [ ] PR diff extraction works
-   [ ] AST extraction works
-   [ ] Semgrep works
-   [ ] Ollama works
-   [ ] Security Agent works
-   [ ] Docker sandbox works
-   [ ] Test Writer works
-   [ ] pytest execution works
-   [ ] Coverage delta works
-   [ ] Merge-readiness score works
-   [ ] PR comment works
-   [ ] PostgreSQL stores analysis
-   [ ] 15--20 PR evaluation set exists
-   [ ] Precision/recall are measured
-   [ ] Coverage delta is measured
-   [ ] Prompt-injection defenses are demonstrated
-   [ ] Sandbox security is demonstrated
-   [ ] Chatbot works if time permits
-   [ ] Demo is reproducible
-   [ ] README is complete

------------------------------------------------------------------------

# 8. Milestones

  Milestone     Day Result
  ----------- ----- -------------------------
  M1              3 FastAPI
  M2             10 GitHub App + GitHub API
  M3             16 Database + Orchestrator
  M4             21 Diff + AST
  M5             31 Security Agent
  M6             42 Test Writer + Sandbox
  M7             49 MVP
  M8             56 Evaluation
  M9             63 Optional Chatbot
  M10            70 Final Demo

------------------------------------------------------------------------

# 9. First Working Goal

Do not try to build the complete Quorum immediately.

Your first target is only:

``` text
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

After this works, add one component at a time.

That is the correct way to get out of the "middle of the ocean" feeling.
