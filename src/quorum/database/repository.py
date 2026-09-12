from sqlalchemy import select
from sqlalchemy.orm import Session

from quorum.database.models import PullRequest, Repository, User


def upsert_user(
    db: Session,
    github_id: int | None,
    username: str | None,
    avatar_url: str | None = None,
    github_installation_id: int | None = None,
) -> User | None:
    if github_id is None:
        return None

    user = db.scalar(select(User).where(User.github_id == github_id))
    if user is None:
        user = User(github_id=github_id)
        db.add(user)

    if username is not None:
        user.username = username
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if github_installation_id is not None:
        user.github_installation_id = github_installation_id
    db.commit()
    return user


def revoke_installation(
    db: Session,
    installation_id: int | None,
    account_id: int | None = None,
) -> int:
    revoked = 0
    if installation_id is not None:
        for user in db.scalars(
            select(User).where(User.github_installation_id == installation_id)
        ):
            user.github_installation_id = None
            revoked += 1
    if account_id is not None:
        for user in db.scalars(select(User).where(User.github_id == account_id)):
            if user.github_installation_id is not None:
                user.github_installation_id = None
                revoked += 1
    db.commit()
    return revoked


def upsert_repository(
    db: Session, data: dict, user_id: int | None = None
) -> Repository | None:
    github_id = data.get("id")
    if github_id is None:
        return None

    repository = db.scalar(
        select(Repository).where(Repository.github_id == github_id)
    )
    if repository is None:
        repository = Repository(github_id=github_id)
        db.add(repository)

    owner = data.get("owner") or {}
    repository.owner = owner.get("login", "")
    repository.name = data.get("name", "")
    repository.full_name = data.get("full_name", "")
    repository.is_private = bool(data.get("private", False))
    if user_id is not None:
        repository.user_id = user_id
    db.commit()
    return repository


def upsert_pull_request(
    db: Session, data: dict, repository: Repository
) -> PullRequest | None:
    github_id = data.get("id")
    if github_id is None:
        return None

    pull_request = db.scalar(
        select(PullRequest).where(PullRequest.github_id == github_id)
    )
    if pull_request is None:
        pull_request = PullRequest(github_id=github_id, repository_id=repository.id)
        db.add(pull_request)

    author = data.get("user") or {}
    pull_request.repository_id = repository.id
    pull_request.number = data.get("number", 0)
    pull_request.title = data.get("title", "")
    pull_request.author = author.get("login", "")
    pull_request.state = data.get("state", "")
    db.commit()
    return pull_request


def list_repositories(db: Session) -> list[Repository]:
    return list(db.scalars(select(Repository).order_by(Repository.full_name)))


def get_repository_by_id(db: Session, repository_id: int) -> Repository | None:
    return db.get(Repository, repository_id)


def list_pull_requests_by_repository(
    db: Session, repository_id: int
) -> list[PullRequest]:
    return list(
        db.scalars(
            select(PullRequest)
            .where(PullRequest.repository_id == repository_id)
            .order_by(PullRequest.number.desc())
        )
    )


def list_pull_requests(db: Session) -> list[PullRequest]:
    return list(db.scalars(select(PullRequest).order_by(PullRequest.id.desc())))


def get_repository_by_full_name(db: Session, full_name: str) -> Repository | None:
    return db.scalar(
        select(Repository).where(Repository.full_name == full_name)
    )


def get_pull_request(db: Session, github_id: int) -> PullRequest | None:
    return db.scalar(
        select(PullRequest).where(PullRequest.github_id == github_id)
    )


def get_pull_request_by_id(db: Session, pull_request_id: int) -> PullRequest | None:
    return db.get(PullRequest, pull_request_id)


def get_user_by_github_id(db: Session, github_id: int | None) -> User | None:
    if github_id is None:
        return None
    return db.scalar(select(User).where(User.github_id == github_id))


def get_user_by_installation(db: Session, installation_id: int | None) -> User | None:
    if installation_id is None:
        return None
    return db.scalar(
        select(User).where(User.github_installation_id == installation_id)
    )


def list_repositories_for_user(db: Session, user_id: int) -> list[Repository]:
    return list(
        db.scalars(
            select(Repository)
            .where(Repository.user_id == user_id)
            .order_by(Repository.full_name)
        )
    )


def detach_repositories_not_in(
    db: Session, user_id: int, authorized_full_names: set[str]
) -> int:
    detached = 0
    for repository in db.scalars(
        select(Repository).where(Repository.user_id == user_id)
    ):
        if repository.full_name not in authorized_full_names:
            repository.user_id = None
            detached += 1
    db.commit()
    return detached


def get_repository_for_user(
    db: Session, repository_id: int, user_id: int
) -> Repository | None:
    return db.scalar(
        select(Repository).where(
            Repository.id == repository_id, Repository.user_id == user_id
        )
    )


def list_pull_requests_for_user(db: Session, user_id: int) -> list[PullRequest]:
    return list(
        db.scalars(
            select(PullRequest)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.user_id == user_id)
            .order_by(PullRequest.id.desc())
        )
    )


def list_repository_pull_requests_for_user(
    db: Session, repository_id: int, user_id: int
) -> list[PullRequest]:
    return list(
        db.scalars(
            select(PullRequest)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(
                PullRequest.repository_id == repository_id,
                Repository.user_id == user_id,
            )
            .order_by(PullRequest.number.desc())
        )
    )


def get_pull_request_for_user(
    db: Session, pull_request_id: int, user_id: int
) -> PullRequest | None:
    return db.scalar(
        select(PullRequest)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .where(PullRequest.id == pull_request_id, Repository.user_id == user_id)
    )