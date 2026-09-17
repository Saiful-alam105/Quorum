"""GitHub PR diff retrieval: obtain an installation token and fetch the raw diff.

Wraps installation-token acquisition and the GitHub diff endpoint, converting
configuration and HTTP failures into a typed :class:`DiffFetchError` so pipeline
stages can react consistently.
"""

from quorum.config import settings
from quorum.github.api import get_pr_diff
from quorum.github.app_auth import get_installation_token


class DiffFetchError(Exception):
    """Raised when a PR diff cannot be retrieved from GitHub."""


async def fetch_pr_diff(
    installation_id: int,
    owner: str,
    repo: str,
    pr_number: int,
) -> str:
    """Fetch the raw unified diff for a pull request as an installation."""
    if (
        not installation_id
        or not settings.github_app_id
        or not settings.github_app_private_key_path
    ):
        raise DiffFetchError(
            "GitHub App credentials or installation id are not configured"
        )

    try:
        install_auth = await get_installation_token(
            settings.github_app_id,
            settings.github_app_private_key_path,
            installation_id,
        )
    except Exception as exc:
        raise DiffFetchError("failed to obtain GitHub installation token") from exc

    token = install_auth.get("token") if isinstance(install_auth, dict) else None
    if not token:
        raise DiffFetchError("GitHub installation token could not be obtained")

    try:
        return await get_pr_diff(token, owner, repo, pr_number)
    except Exception as exc:
        raise DiffFetchError(
            f"failed to fetch diff for {owner}/{repo}#{pr_number}"
        ) from exc