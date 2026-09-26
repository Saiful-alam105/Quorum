"""Point the GitHub App webhook at the current Cloudflare tunnel URL.

Why this exists: a *quick* tunnel (``cloudflared tunnel --url ...``) gets a new
random ``*.trycloudflare.com`` URL on every restart. GitHub keeps delivering
webhooks to the old URL, so Pull Requests silently never reach the backend.

Run this after starting the tunnel (or after any cloudflared restart):

    python scripts/sync_github_webhook.py --url https://xxxx.trycloudflare.com

It sets the GitHub App webhook to ``<url>/webhooks/github`` using the app's
JWT. Requires GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY_PATH, and
GITHUB_WEBHOOK_SECRET (already in ``.env``).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import httpx

from quorum.config import settings
from quorum.github.app_auth import create_app_jwt

GITHUB_API = "https://api.github.com/app/hook/config"


def sync_webhook(url: str, dry_run: bool = False) -> dict:
    """Update the GitHub App webhook URL to the current tunnel URL."""
    base = url.rstrip("/")
    target = f"{base}/webhooks/github"
    body = {
        "url": target,
        "content_type": "json",
        "secret": settings.github_webhook_secret,
    }
    if dry_run:
        print(f"[dry-run] would set the app webhook url -> {target}")
        return {"url": target}

    jwt = create_app_jwt(settings.github_app_id, settings.github_app_private_key_path)
    response = httpx.patch(
        GITHUB_API,
        headers={
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github+json",
        },
        json=body,
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"GitHub API {response.status_code}: {response.text[:300]}")
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Point the GitHub App webhook at the current tunnel URL."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="current tunnel URL, e.g. https://xxxx.trycloudflare.com",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the target URL without calling GitHub",
    )
    args = parser.parse_args()

    try:
        result = sync_webhook(args.url, dry_run=args.dry_run)
        print("OK  webhook url ->", result.get("url"))
        print("    active:", result.get("active"), "| content_type:", result.get("content_type"))
    except Exception as exc:  # noqa: BLE001 - report the failure clearly
        print("ERROR:", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())