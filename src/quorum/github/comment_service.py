"""GitHub review-comment posting (Phase 14).

Obtains an installation token and posts a review comment to a pull request,
converting configuration and HTTP failures into a typed
:class:`CommentPostError` so pipeline stages can react consistently.
"""

from quorum.config import settings
from quorum.github.api import create_pr_comment
from quorum.github.app_auth import get_installation_token


class CommentPostError(Exception):
    """Raised when a review comment cannot be posted."""


async def _get_installation_token(installation_id: int) -> str:
    if (
        not installation_id
        or not settings.github_app_id
        or not settings.github_app_private_key_path
    ):
        raise CommentPostError(
            "GitHub App credentials or installation id are not configured"
        )

    try:
        install_auth = await get_installation_token(
            settings.github_app_id,
            settings.github_app_private_key_path,
            installation_id,
        )
    except Exception as exc:
        raise CommentPostError("failed to obtain GitHub installation token") from exc

    token = install_auth.get("token") if isinstance(install_auth, dict) else None
    if not token:
        raise CommentPostError("GitHub installation token could not be obtained")
    return token


async def post_review_comment(
    installation_id: int,
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
) -> dict:
    """Post ``body`` as a comment on the pull request."""
    token = await _get_installation_token(installation_id)
    try:
        return await create_pr_comment(token, owner, repo, pr_number, body)
    except Exception as exc:
        raise CommentPostError(
            f"failed to post review comment to {owner}/{repo}#{pr_number}"
        ) from exc