from sqlalchemy.orm import Session

from quorum.config import settings
from quorum.database.models import User
from quorum.database.repository import (
    detach_repositories_not_in,
    upsert_repository,
)
from quorum.github.api import get_installation_repositories
from quorum.github.app_auth import get_installation_token


async def sync_user_repositories(db: Session, user: User) -> bool:
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
        install_token = install_auth.get("token")
        if not install_token:
            return False

        authorized = await get_installation_repositories(install_token)
        for repo_data in authorized:
            upsert_repository(db, repo_data, user_id=user.id)
        detach_repositories_not_in(
            db,
            user.id,
            {r.get("full_name") for r in authorized},
        )
        return True
    except Exception:
        return False