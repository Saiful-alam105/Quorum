import secrets

from fastapi import APIRouter, Cookie, HTTPException, Request, Response

from quorum.auth.github_oauth import build_authorize_url, exchange_code, get_github_user
from quorum.auth.sessions import create_session, delete_session, get_session
from quorum.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(response: Response) -> dict:
    if not settings.github_client_id:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        max_age=300,
    )

    authorize_url = build_authorize_url(
        client_id=settings.github_client_id,
        redirect_uri=settings.github_redirect_uri,
        state=state,
    )

    return {"authorize_url": authorize_url}


@router.get("/callback")
async def callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    oauth_state: str | None = Cookie(default=None),
) -> dict:
    if not oauth_state or oauth_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    response.delete_cookie("oauth_state")

    try:
        access_token = await exchange_code(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            code=code,
        )
        user = await get_github_user(access_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {e}")

    session_token = create_session({
        "github_id": user.get("id"),
        "username": user.get("login"),
        "access_token": access_token,
    })

    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )

    return {"username": user.get("login"), "github_id": user.get("id")}


@router.get("/me")
async def me(session: str | None = Cookie(default=None)) -> dict:
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return {
        "github_id": session_data.get("github_id"),
        "username": session_data.get("username"),
    }


@router.post("/logout")
async def logout(
    response: Response,
    session: str | None = Cookie(default=None),
) -> dict:
    if session:
        delete_session(session)

    response.delete_cookie("session")
    return {"status": "logged_out"}
