from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from quorum.api.schemas import (
    PullRequestOut,
    PullRequestSummaryOut,
    RepositoryOut,
    UserOut,
)
from quorum.auth.sessions import get_session
from quorum.database.base import get_db
from quorum.database.models import PullRequest
from quorum.database.repository import (
    get_pull_request_for_user,
    get_repository_for_user,
    get_user_by_github_id,
    list_pull_requests_for_user,
    list_repositories_for_user,
    list_repository_pull_requests_for_user,
)

router = APIRouter(prefix="/api", tags=["api"])


def _current_user_id(db: Session, session: str | None) -> int:
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = get_user_by_github_id(db, session_data.get("github_id"))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user.id


@router.get("/me", response_model=UserOut)
def read_current_user(session: str | None = Cookie(default=None)) -> UserOut:
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return UserOut(
        github_id=session_data.get("github_id"),
        username=session_data.get("username"),
    )


@router.get("/repositories", response_model=list[RepositoryOut])
def read_repositories(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[RepositoryOut]:
    user_id = _current_user_id(db, session)
    return [
        RepositoryOut.model_validate(repo)
        for repo in list_repositories_for_user(db, user_id)
    ]


def _pull_request_summary(pull_request: PullRequest) -> PullRequestSummaryOut:
    return PullRequestSummaryOut(
        id=pull_request.id,
        github_id=pull_request.github_id,
        number=pull_request.number,
        title=pull_request.title,
        author=pull_request.author,
        state=pull_request.state,
        repository_id=pull_request.repository_id,
        repository_full_name=(
            pull_request.repository.full_name
            if pull_request.repository is not None
            else None
        ),
    )


@router.get("/pull-requests", response_model=list[PullRequestSummaryOut])
def read_pull_requests(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[PullRequestSummaryOut]:
    user_id = _current_user_id(db, session)
    return [_pull_request_summary(pr) for pr in list_pull_requests_for_user(db, user_id)]


@router.get("/pull-requests/{pull_request_id}", response_model=PullRequestSummaryOut)
def read_pull_request(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> PullRequestSummaryOut:
    user_id = _current_user_id(db, session)
    pull_request = get_pull_request_for_user(db, pull_request_id, user_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return _pull_request_summary(pull_request)


@router.get("/repositories/{repository_id}", response_model=RepositoryOut)
def read_repository(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> RepositoryOut:
    user_id = _current_user_id(db, session)
    repository = get_repository_for_user(db, repository_id, user_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryOut.model_validate(repository)


@router.get(
    "/repositories/{repository_id}/pull-requests",
    response_model=list[PullRequestOut],
)
def read_repository_pull_requests(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[PullRequestOut]:
    user_id = _current_user_id(db, session)
    if get_repository_for_user(db, repository_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return [
        PullRequestOut.model_validate(pr)
        for pr in list_repository_pull_requests_for_user(db, repository_id, user_id)
    ]
