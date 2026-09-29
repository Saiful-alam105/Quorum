---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    background:
      radial-gradient(1100px 500px at 100% 0%, rgba(139, 124, 240, 0.20), transparent 60%),
      radial-gradient(900px 450px at 0% 100%, rgba(62, 207, 110, 0.10), transparent 55%),
      linear-gradient(160deg, #0b0d12 0%, #12141c 100%);
    color: #e8ecf3;
  }
  section::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: linear-gradient(90deg, #8b7cf0 0%, #3ecf6e 100%);
  }
  section::after {
    color: #5b6474;
    font-size: 14px;
  }
  h1 {
    color: #a594f9;
    text-shadow: 0 0 28px rgba(139, 124, 240, 0.35);
  }
  h2 {
    color: #a594f9;
    border-bottom: 2px solid #262b38;
    padding-bottom: 0.25em;
  }
  strong {
    color: #ffffff;
  }
  em {
    color: #cfd7e3;
  }
  blockquote {
    background: #151823;
    border-left: 4px solid #3ecf6e;
    border-radius: 6px;
    padding: 0.6em 1em;
    color: #cfd7e3;
  }
  table {
    border-collapse: collapse;
    background: #12151c;
  }
  th {
    background: #1b1f2a;
    color: #a594f9;
    border: 1px solid #2a3040;
    padding: 0.35em 0.7em;
  }
  td {
    background: #12151c;
    color: #e8ecf3;
    border: 1px solid #2a3040;
    padding: 0.35em 0.7em;
  }
  section.benchmark table {
    font-size: 13px;
    width: auto;
    margin-left: auto;
    margin-right: auto;
  }
  a {
    color: #a594f9;
  }
  code {
    background: #1b1f2a;
    color: #7ee2a8;
    padding: 0 0.25em;
    border-radius: 4px;
  }
  section.lead {
    justify-content: center;
    text-align: center;
  }
  section.lead h1 {
    font-size: 2.6em;
  }
  section.lead table {
    margin: 0 auto;
    text-align: left;
  }
---

<!-- Slide 1: Title / Team -->
<!-- _class: lead -->
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

<!-- Slide 2: Problem & Solution -->
# Problem & Solution

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

<!-- Slide 4: Benchmark vs other PR review apps -->
<!-- _class: benchmark -->
# Quorum vs Other PR Review Apps

| Capability | Quorum | GitHub Copilot | CodeRabbit | Codacy | Qodo (PR-Agent) |
|---|---|---|---|---|---|
| AI review comments | ✅ | ✅ | ✅ | ❌ | ✅ |
| Security scanning (Semgrep rules) | ✅ | ❌ | ✅ | ✅ | ✅ |
| Generates tests | ✅ | ❌ | ❌ | ❌ | ❌ |
| Runs tests in a secure sandbox | ✅ | ❌ | ❌ | ❌ | ❌ |
| Measures test coverage | ✅ | ❌ | ❌ | ❌ | ❌ |
| Deterministic 0–100 Merge Readiness score | ✅ | ❌ | ❌ | ❌ | ❌ |
| Merge / close PRs from the app | ✅ | ❌ | ❌ | ❌ | ❌ |
| Evidence-grounded review chatbot | ✅ | ❌ | ❌ | ❌ | ❌ |

---

<!-- Slide 5: Git / Timeline (show live git while presenting) -->
# Git — Timeline

**Project timeline:** Aug 8 → Sep 29, 2026 (~7 weeks) · **203 commits**

**Repo:** [github.com/Saiful-alam105/Quorum](https://github.com/Saiful-alam105/Quorum)

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
<!-- _class: lead -->
# Thank You!

**Quorum** — evidence-based Pull Request reviews, from 0 to 100.

<!--
CSE 3422 Software Engineering Laboratory — Section C
Faculty: Zobaer Ibn Razzaque
Team: Saiful Alam (0112320105), Sabbir Ahmed (011222279)
-->