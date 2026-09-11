from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from quorum.api.schemas import RepositoryOut, UserOut
from quorum.auth.sessions import get_session
from quorum.database.base import get_db
from quorum.database.repository import list_repositories

router = APIRouter(prefix="/api", tags=["api"])


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
def read_repositories(db: Session = Depends(get_db)) -> list[RepositoryOut]:
    return [RepositoryOut.model_validate(repo) for repo in list_repositories(db)]
