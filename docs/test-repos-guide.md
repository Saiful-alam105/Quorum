# Quorum — Test Repository Guide

A guide to set up test repositories that exercise Quorum's full pipeline
(Semgrep security analysis → Security Agent → Test Writer → Docker sandbox →
coverage → Merge Readiness → Ask Quorum), organized so you can create many
repositories / many code types and push Pull Requests without merge conflicts.

## Setup notes (apply to all repos)

- **Use Python-heavy code.** Quorum's AST extraction, Test Writer, and coverage
  measurement target Python (`.py`). Semgrep also scans other files, but the
  full pipeline needs Python.
- **One concern per file, one file per PR** — the main rule that avoids merge
  conflicts (see the workflow below).
- To trigger analysis: open a PR (or push to the PR's branch to re-trigger
  `synchronize`); Quorum analyzes automatically.
- Requirements: backend running, `OPENAI_API_KEY` set, Docker + `quorum-sandbox`
  image built (for tests/coverage).

---

## Repo 1 — `quorum-vuln-demo` (known-BAD PRs → security findings)

Purpose: trigger real Semgrep findings at known files/lines. Create one module
per vulnerability (each its own file), then one PR per file.

| File | Code (add to a branch) | Expected finding |
| --- | --- | --- |
| `vulns/shell_injection.py` | `import subprocess` / `def run(cmd):` / `    subprocess.call(cmd, shell=True)` | HIGH — `subprocess.call(... shell=True)` |
| `vulns/eval_injection.py` | `def evaluate(data):` / `    return eval(data)` | MEDIUM — `eval` on dynamic data |
| `vulns/sql_injection.py` | `cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")` | HIGH — SQL string concatenation |
| `vulns/os_command.py` | `import os` / `def go(u):` / `    os.system(u)` | HIGH — `os.system` with untrusted input |
| `vulns/pickle_load.py` | `import pickle` / `def load(b):` / `    return pickle.loads(b)` | MEDIUM — unsafe `pickle.loads` |
| `vulns/weak_hash.py` | `import hashlib` / `def h(p):` / `    return hashlib.md5(p.encode())` | LOW — weak hash (MD5) |
| `vulns/template_injection.py` | `from flask import render_template_string` / `def page(t):` / `    return render_template_string(t)` | MEDIUM — SSTI via `render_template_string` |
| `vulns/unsafe_yaml.py` | `import yaml` / `def load(c):` / `    return yaml.load(c)` | MEDIUM/HIGH — unsafe `yaml.load` |

Push **one** such file per PR; each PR should produce the matching finding(s)
in Review History / PR detail.

## Repo 2 — `quorum-good-demo` (known-GOOD PRs → no/low findings, high score)

Purpose: safe versions of the same features → no findings, a high Merge
Readiness score. One PR per safe feature.

| File | Code idea | Expected result |
| --- | --- | --- |
| `safe/shell_injection.py` | `subprocess.run(["ls", path])` — list args, no `shell=True` | No finding |
| `safe/sql_injection.py` | parameterized query: `execute("... WHERE name = ?", (name,))` | No finding |
| `safe/crypto.py` | `secrets.token_hex(16)`, `hashlib.sha256` | No finding |
| `safe/validation.py` | input length/type checks before use | No finding |

Good PRs should get scores in the 80–100 band (no findings, tests generated,
coverage measured).

## Repo 3 — `quorum-testwriter-demo` (test generation + coverage focus)

Purpose: pure functions that the Test Writer can test and coverage can measure
a real delta (0% → higher). Create modules of pure, well-defined functions with
branches (coverage gets interesting):

- `math_utils.py` — `calculate_discount(price, rate)` with `if rate < 0 / > 1`
  branches, `tax_add(price)`
- `string_utils.py` — `to_slug(text)`, `truncate(text, limit)` with edge cases
- `validation.py` — `is_valid_email(email)`, `validate_password(password)`
  (length + complexity branches)
- `parsers.py` — `parse_csv_row(line)` handling empty/extra fields

Expected: each PR shows generated tests (status pass/fail), coverage
`before → after` and a delta, and a score influenced by how many tests pass.
Keep functions importable so the sandbox can run the generated tests.

## Repo 4 — `quorum-edge-demo` (edge cases / honest limits)

Purpose: see how Quorum behaves on non-ideal inputs.

- `edge/docs_only.md` (or a PR that only changes `.md`) — no Python changes →
  no findings/tests, low score (honest).
- `edge/big_pr/` — one PR touching many files (30–50 small modules) → triggers
  context truncation handling (bounded prompt) rather than unbounded.
- `edge/non_python.js` (a JS file) — Semgrep may scan it, but no AST/test
  coverage.
- `edge/renames/` — a PR that renames a module → `renamed` status path.
- An intentionally infinite/unsafe generated-test scenario is hard to force;
  rely on the sandbox's live DoD tests instead.

## Repo 5 — `quorum-chat-demo` (Ask Quorum)

Purpose: a repo with findings + tests + coverage so you can ask chat questions.

- Include 1–2 vulnerable files (from Repo 1), 1 pure-function module (from
  Repo 3), and a couple of safe files, in **separate PRs**.
- Then in Ask Quorum ask: *"What security issues were found?"*, *"Why did this
  PR get this score?"*, *"What were the test results?"*, *"How did coverage
  change?"* — expect structured Markdown answers grounded in that review only.

---

## How to push all this WITHOUT merge conflicts

The core rule: **each PR touches unique files; never modify the same file in
two open PRs.**

Recommended workflow (per PR):

```bash
# from a clean main
git fetch origin
git checkout main
git pull origin main

# new branch for ONE test
git checkout -b pr-shell-injection
# add ONE new file only (e.g. vulns/shell_injection.py)
git add vulns/shell_injection.py
git commit -m "test: shell injection vulnerability"
git push -u origin pr-shell-injection
# open the PR on GitHub -> Quorum analyzes it
```

Rules that keep conflicts away:

1. **Additive only** — create new files; don't edit existing ones. This
   eliminates almost all conflicts.
2. **One file per branch/PR.** If a PR must touch an existing file, merge that
   PR first and pull before opening the next one that touches the same file.
3. **Sync before branching** — always `git pull origin main` before creating a
   branch.
4. **If a conflict appears anyway:** since branches are additive, resolve by
   keeping both files (they are different) or rebase:
   `git fetch origin && git rebase origin/main`.
5. Keep each branch short-lived; merge the PR, then start the next.

This lets you build up many repositories / many code types for testing Quorum
(security findings, good PRs, test generation, coverage, edge cases, chatbot
grounding) while keeping the test repos conflict-free.