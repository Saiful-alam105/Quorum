import httpx
from sqlalchemy.orm import Session

from quorum.config import settings
from quorum.database.models import User, utcnow
from quorum.database.repository import (
    detach_repositories_not_in,
    upsert_repository,
)
from quorum.github.api import get_installation_repositories
from quorum.github.app_auth import get_installation_token


def _age_seconds(last) -> float:
    if last.tzinfo is None:
        last = last.replace(tzinfo=utcnow().tzinfo)
    return (utcnow() - last).total_seconds()


async def maybe_sync_user_repositories(
    db: Session, user: User, max_age_seconds: int = 60
) -> bool:
    """Sync only when the last sync is older than ``max_age_seconds``.

    Keeps cheap page loads fast: the GitHub App installation round-trip is
    avoided on every request, while GitHub-side changes still show up within
    the staleness window.
    """
    last = user.repos_synced_at
    if last is not None and _age_seconds(last) < max_age_seconds:
        return True
    return await sync_user_repositories(db, user)


async def sync_user_repositories(
    db: Session, user: User, clear_exclusions: bool = False
) -> bool:
    """Reconcile a user's repositories with the GitHub App installation.

    Attaches repositories the installation authorizes (unless the user has
    explicitly disconnected them) and detaches everything else. When
    ``clear_exclusions`` is set (e.g. after the user goes through the GitHub
    App install flow) all intentional disconnects are forgotten first.
    """
    if (
        user.github_installation_id is None
        or not settings.github_app_id
        or not settings.github_app_private_key_path
    ):
        return False

    try:
        install_auth = await get_installation_token(
            settings.github_app_id,
            settings.github_app_private_key_path,
            user.github_installation_id,
        )
    except httpx.HTTPStatusError as exc:
        # The installation no longer exists (app uninstalled): detach all
        # repositories and forget the installation so we stop trying.
        if exc.response.status_code in (401, 403, 404):
            detach_repositories_not_in(db, user.id, set())
            user.github_installation_id = None
            user.excluded_repositories = []
            user.repos_synced_at = utcnow()
            db.commit()
        return False
    except Exception:
        return False

    install_token = install_auth.get("token")
    if not install_token:
        return False

    if clear_exclusions:
        user.excluded_repositories = []

    try:
        authorized = await get_installation_repositories(install_token)
    except Exception:
        return False

    excluded = set(user.excluded_repositories or [])
    attachable = [r for r in authorized if r.get("full_name") not in excluded]
    for repo_data in attachable:
        upsert_repository(db, repo_data, user_id=user.id)
    detach_repositories_not_in(
        db,
        user.id,
        {r.get("full_name") for r in attachable},
    )
    user.repos_synced_at = utcnow()
    db.commit()
    return True