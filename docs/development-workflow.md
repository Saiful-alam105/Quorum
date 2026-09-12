# Quorum — Development Workflow (Demo Note)

Date: 2026-09-12. From `AGENTS.md`.

Incremental loop used for remaining work:

```text
ONE SMALL CHUNK
    ↓
IMPLEMENT
    ↓
AUTOMATED TEST
    ↓
MANUAL TEST
    ↓
USER CONFIRMATION
    ↓
COMMIT + PUSH
    ↓
NEXT CHUNK
```

Rules followed:

- One roadmap phase at a time; large phases split into small chunks.
- Only the smallest incomplete task of the current phase.
- No future phases early; no fake data; no unrelated refactoring.
- Work on `feature/*` / `docs/*` branches, never directly on `main`.
- Never commit `.env`, `*.pem`/`*.key`, or local model files.

Commands (Windows / PowerShell, from repo root):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn --app-dir src quorum.main:app --reload
pytest
```
