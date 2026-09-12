# Quorum — Getting Started (Demo Note)

Date: 2026-09-12. From `README.md`; no credentials included.

Backend (repo root, Python 3.13):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn --app-dir src quorum.main:app --reload
pytest
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
npm run build
```

Verify:

- Backend root: `http://localhost:8000/`
- Health: `http://localhost:8000/health` → `{"status":"ok"}`
- Frontend: `http://localhost:5173/`
- Sign in: `http://localhost:5173/login`

PostgreSQL runs locally on port `5432`; never commit the real `.env`.
