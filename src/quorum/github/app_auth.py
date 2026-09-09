import time
from pathlib import Path

import httpx
import jwt


GITHUB_API_BASE = "https://api.github.com"


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

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        return response.json()
