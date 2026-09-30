import asyncio
import time
from pathlib import Path

import httpx
import jwt

from quorum.config import settings

GITHUB_API_BASE = "https://api.github.com"


class GitHubTransientError(Exception):
    """Raised for transient network errors so callers can retry or surface."""


async def retry_github(call, attempts: int | None = None):
    """Run ``call`` with backoff, retrying transient network failures.

    GitHub API calls are the pipeline's most failure-prone step (slow or
    flaky connections, quick tunnel overhead). A short retry loop with a
    generous timeout keeps one slow request from failing a whole analysis.
    """
    attempts = attempts or settings.github_retries
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return await call()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.TransportError) as exc:
            last_exc = exc
            await asyncio.sleep(0.5 * (i + 1))
    raise GitHubTransientError(f"GitHub request failed after {attempts} attempts") from last_exc


def github_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=httpx.Timeout(settings.github_timeout_seconds))


def _read_private_key(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def create_app_jwt(app_id: str, private_key_path: str) -> str:
    if not app_id or not private_key_path:
        raise ValueError("GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY_PATH must be set")

    private_key = _read_private_key(private_key_path)
    now = int(time.time())

    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": app_id,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


async def get_installation_token(app_id: str, private_key_path: str, installation_id: int) -> dict:
    app_jwt = create_app_jwt(app_id, private_key_path)

    async def post():
        async with github_client() as client:
            response = await client.post(
                f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            return response.json()

    return await retry_github(post)
