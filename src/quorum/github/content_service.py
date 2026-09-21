"""GitHub file-content and pull-request retrieval for Phase 8.

Wraps installation-token acquisition and the GitHub contents / pull-request
endpoints, converting configuration and HTTP failures into a typed
:class:`ContentFetchError` so pipeline stages can react consistently.
"""

from quorum.config import settings
from quorum.github.api import get_file_contents, get_pull_request
from quorum.github.app_auth import get_installation_token


class ContentFetchError(Exception):
    """Raised when a file's content cannot be retrieved from GitHub."""


async def _get_installation_token(installation_id: int) -> str:
    if (
        not installation_id
        or not settings.github_app_id
        or not settings.github_app_private_key_path
    ):
        raise ContentFetchError(
            "GitHub App credentials or installation id are not configured"
        )

    try:
        install_auth = await get_installation_token(
            settings.github_app_id,
            settings.github_app_private_key_path,
            installation_id,
        )
    except Exception as exc:
        raise ContentFetchError("failed to obtain GitHub installation token") from exc

    token = install_auth.get("token") if isinstance(install_auth, dict) else None
    if not token:
        raise ContentFetchError("GitHub installation token could not be obtained")
    return token


async def fetch_file_content(
    installation_id: int,
    owner: str,
    repo: str,
    path: str,
    ref: str,
) -> str:
    """Fetch the full content of ``path`` at ``ref`` as an installation."""
    token = await _get_installation_token(installation_id)
    try:
        return await get_file_contents(token, owner, repo, path, ref)
    except Exception as exc:
        raise ContentFetchError(
            f"failed to fetch content for {owner}/{repo} {path}@{ref}"
        ) from exc


async def fetch_pull_request(
    installation_id: int,
    owner: str,
    repo: str,
    pr_number: int,
) -> dict:
    """Fetch a pull request object (including ``head.sha``) as an installation."""
    token = await _get_installation_token(installation_id)
    try:
        return await get_pull_request(token, owner, repo, pr_number)
    except Exception as exc:
        raise ContentFetchError(
            f"failed to fetch pull request {owner}/{repo}#{pr_number}"
        ) from exc