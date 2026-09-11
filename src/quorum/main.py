import json
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from quorum.api.routes import router as api_router
from quorum.auth.routes import router as auth_router
from quorum.config import settings
from quorum.database.base import get_db
from quorum.database.repository import (
    get_user_by_installation,
    revoke_installation,
    upsert_pull_request,
    upsert_repository,
)
from quorum.github.webhook import verify_signature

app = FastAPI(
    title="Quorum",
    description="AI-powered Pull Request reviewer",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(api_router)

SUPPORTED_EVENTS = {
    "ping",
    "pull_request",
    "installation",
    "installation_repositories",
}
SUPPORTED_ACTIONS = {"opened", "reopened", "synchronize"}


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": "Quorum",
        "description": "AI-powered Pull Request reviewer",
        "version": app.version,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request, db: Session = Depends(get_db)
) -> JSONResponse:
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(settings.github_webhook_secret, raw_body, signature):
        return JSONResponse(status_code=401, content={"status": "invalid signature"})

    event = request.headers.get("X-GitHub-Event", "")
    if event not in SUPPORTED_EVENTS:
        return JSONResponse(status_code=202, content={"status": "ignored", "event": event})

    if event == "ping":
        return JSONResponse(status_code=200, content={"status": "ok", "event": "ping"})

    if event in ("installation", "installation_repositories"):
        payload = json.loads(raw_body)
        if event == "installation":
            action = payload.get("action") if isinstance(payload, dict) else None
            if action == "deleted":
                installation = payload.get("installation") or {}
                account = installation.get("account") or {}
                revoke_installation(
                    db,
                    installation_id=installation.get("id"),
                    account_id=account.get("id"),
                )
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "event": event},
        )

    payload: Any = json.loads(raw_body)
    action = payload.get("action") if isinstance(payload, dict) else None
    if action not in SUPPORTED_ACTIONS:
        return JSONResponse(
            status_code=202,
            content={"status": "ignored", "event": event, "action": action},
        )

    if isinstance(payload, dict):
        installation = payload.get("installation") or {}
        owner = get_user_by_installation(
            db, installation.get("id") if isinstance(installation, dict) else None
        )
        repository = upsert_repository(
            db,
            payload.get("repository") or {},
            user_id=owner.id if owner is not None else None,
        )
        if repository is not None:
            upsert_pull_request(db, payload.get("pull_request") or {}, repository)

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "event": event, "action": action},
    )