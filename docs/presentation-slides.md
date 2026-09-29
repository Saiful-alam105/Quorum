---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: "Segoe UI", Arial, sans-serif;
  }
  h1 {
    color: #0f766e;
  }
  h2 {
    color: #0f766e;
    border-bottom: 3px solid #0f766e;
    padding-bottom: 6px;
  }
  table {
    font-size: 20px;
  }
  blockquote {
    color: #134e4a;
    font-style: italic;
  }
---

<!-- Slide 1: Title / Team -->
# Quorum

![Quorum logo](../frontend/public/favicon.svg)

### AI-Powered GitHub Pull Request Reviewer

**Faculty:** Zobaer Ibn Razzaque  
**Course:** CSE 3422 Software Engineering Laboratory — Section C

**Team Members**

| Member | ID | Role |
|--------|----|------|
| **Saiful Alam** | 0112320105 | Backend, AI Analysis Pipeline, Web Dashboard |
| **Sabbir Ahmed** | 011222279 | Documentation & Project Support |

---

<!-- Slide 2: Introduction -->
# Introduction

**The problem**
- Merging code is risky — hidden bugs, security vulnerabilities, broken tests
- *"Looks fine to me"* is not evidence

**Quorum's answer**
- Scans every Pull Request for **security issues** (Semgrep)
- **Writes real tests** and runs them in a **secure Docker sandbox**
- **Measures test coverage** automatically
- Gives one clear, evidence-based answer: **Merge Readiness Score 0–100**

> Turn "trust me" into "prove it."

---

<!-- Slide 3: Feature Breakdown (show the app while presenting) -->
# Feature Breakdown

- **GitHub App + OAuth login** — sign in with GitHub
- **Repository discovery** — see all your repos, one-click **Connect / Disconnect**
- **Create Pull Requests from Quorum** — Base + Compare, suggested titles
- **Merge / Close PRs** — no need to leave the app
- **AI Analysis Pipeline**
  - Extract diff → **Semgrep** security scan → Security Agent (LLM)
  - Generate tests → run in **Docker sandbox** → measure coverage
- **Merge Readiness Score 0–100** with an explainable breakdown
- **Auto review comment** posted on the PR
- **Ask Quorum** — evidence-grounded chatbot for each review

---

<!-- Slide 4: What's different from other PR review apps -->
# What's Different from Other PR Review Apps

| Other AI reviewers | Quorum |
|--------------------|--------|
| Just post an AI comment | **Generates & runs real tests**, measures **coverage** |
| LLM decides a score | **Deterministic 0–100 score** with exact breakdown |
| Findings can be hallucinated | Every finding maps to **real Semgrep evidence** |
| Only comments on GitHub | **Full workflow app** — connect, create, merge, close |
| Run code on your machine | Runs in a **hardened, sandboxed Docker container** |
| Generic chatbot | Chatbot grounded **only in that review's evidence** |

---

<!-- Slide 5: Git / Timeline (show live git while presenting) -->
# Git — Timeline & Contribution

**Project timeline:** Aug 8 → Sep 29, 2026 (~7 weeks) · **196 commits**

| Member | Commits | Main contribution |
|--------|---------|-------------------|
| **Saiful Alam** | 165 | Backend architecture, GitHub App/OAuth, AI pipeline (Semgrep, sandbox, scoring), dashboard, webhooks |
| **Sabbir Ahmed** | 11 | Documentation, demo checklists, architecture & project-update docs |

*Live demo: `git log`, GitHub Insights → Contributors*

---

<!-- Slide 6: Testing (run in terminal while presenting) -->
# Testing

- **Backend** — `pytest`
  - **679 tests passing** (webhooks, auth, API, pipeline stages, security, scoring, chat)
- **Frontend** — `npm test`
  - **119 tests passing** (Vitest + Testing Library)
- **Per-PR coverage** — measured live inside the sandbox for every review

*Live demo: run the suites in the terminal*

---

<!-- Slide 7: Thank You -->
# Thank You!

**Quorum** — evidence-based Pull Request reviews, from 0 to 100.

<!--
CSE 3422 Software Engineering Laboratory — Section C
Faculty: Zobaer Ibn Razzaque
Team: Saiful Alam (0112320105), Sabbir Ahmed (011222279)
-->