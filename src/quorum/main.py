from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Quorum",
    description="AI-powered Pull Request reviewer",
    version="0.1.0",
)

SUPPORTED_EVENTS = {"ping", "pull_request"}
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
async def github_webhook(request: Request) -> JSONResponse:
    event = request.headers.get("X-GitHub-Event", "")
    if event not in SUPPORTED_EVENTS:
        return JSONResponse(status_code=202, content={"status": "ignored", "event": event})

    if event == "ping":
        return JSONResponse(status_code=200, content={"status": "ok", "event": "ping"})

    payload: Any = await request.json()
    action = payload.get("action") if isinstance(payload, dict) else None
    if action not in SUPPORTED_ACTIONS:
        return JSONResponse(
            status_code=202,
            content={"status": "ignored", "event": event, "action": action},
        )

    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "event": event, "action": action},
    )