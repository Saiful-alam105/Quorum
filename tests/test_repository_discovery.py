import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import quorum.api.routes as routes_module
import quorum.config as config_module
from quorum.auth.sessions import create_session
from quorum.database.base import Base, get_db
from quorum.database.models import PullRequest, Repository, User
from quorum.main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def user(db_session: Session) -> User:
    test_user = User(github_id=1, username="testuser")
    db_session.add(test_user)
    db_session.commit()
    return test_user


@pytest.fixture
def session_token(user: User) -> str:
    return create_session(
        {
            "github_id": 1,
            "username": "testuser",
            "access_token": "user-oauth-token",
        }
    )


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth(token: str) -> dict:
    return {"cookies": {"session": token}}


def _github_repo(
    github_id: int,
    full_name: str,
    language: str | None = "Python",
    default_branch: str = "main",
    private: bool = False,
) -> dict:
    owner, name = full_name.split("/")
    return {
        "id": github_id,
        "name": name,
        "full_name": full_name,
        "private": private,
        "language": language,
        "default_branch": default_branch,
        "owner": {"login": owner},
    }


def _add_connected_repo(
    db_session: Session,
    user: User,
    github_id: int,
    full_name: str,
    pr_count: int = 0,
) -> Repository:
    owner, name = full_name.split("/")
    repo = Repository(
        github_id=github_id,
        owner=owner,
        name=name,
        full_name=full_name,
        is_private=False,
        user_id=user.id,
    )
    db_session.add(repo)
    db_session.commit()
    for number in range(1, pr_count + 1):
        db_session.add(
            PullRequest(
                github_id=1000 + number,
                repository_id=repo.id,
                number=number,
                title=f"PR {number}",
                author="octocat",
                state="open",
            )
        )
    db_session.commit()
    return repo


def test_discover_requires_auth(client: TestClient) -> None:
    assert client.get("/api/repositories/discover").status_code == 401


def test_discover_requires_access_token(client: TestClient, user: User) -> None:
    token = create_session({"github_id": 1, "username": "testuser"})
    response = client.get(
        "/api/repositories/discover", **_auth(token)
    )
    assert response.status_code == 401


def test_discover_returns_github_repos_with_connected_status(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _add_connected_repo(db_session, user, github_id=201, full_name="octocat/alpha", pr_count=3)
    github_repos = [
        _github_repo(201, "octocat/alpha"),
        _github_repo(202, "octocat/beta", language="TypeScript"),
    ]

    async def mock_get_repositories(token: str) -> list:
        return github_repos

    monkeypatch.setattr(routes_module, "get_repositories", mock_get_repositories)

    response = client.get(
        "/api/repositories/discover", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert [item["full_name"] for item in data] == ["octocat/alpha", "octocat/beta"]
    assert data[0]["connected"] is True
    assert data[0]["id"] is not None
    assert data[0]["pull_request_count"] == 3
    assert data[0]["language"] == "Python"
    assert data[1]["connected"] is False
    assert data[1]["id"] is None
    assert data[1]["pull_request_count"] == 0
    assert data[1]["language"] == "TypeScript"
    assert data[1]["default_branch"] == "main"


def test_discover_empty(client: TestClient, session_token: str, monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get_repositories(token: str) -> list:
        return []

    monkeypatch.setattr(routes_module, "get_repositories", mock_get_repositories)
    response = client.get(
        "/api/repositories/discover", **_auth(session_token)
    )
    assert response.status_code == 200
    assert response.json() == []


def test_discover_github_error_returns_502(
    client: TestClient, session_token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_get_repositories(token: str) -> list:
        raise RuntimeError("GitHub down")

    monkeypatch.setattr(routes_module, "get_repositories", mock_get_repositories)
    response = client.get(
        "/api/repositories/discover", **_auth(session_token)
    )
    assert response.status_code == 502


def test_connect_url_requires_auth(client: TestClient) -> None:
    assert client.get("/api/repositories/connect-url").status_code == 401


def test_connect_url_returns_install_url(
    client: TestClient, session_token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config_module.settings, "github_app_slug", "quorum-app")
    response = client.get(
        "/api/repositories/connect-url", **_auth(session_token)
    )
    assert response.status_code == 200
    assert (
        response.json()["install_url"]
        == "https://github.com/apps/quorum-app/installations/new"
    )


def test_connect_url_requires_slug(
    client: TestClient, session_token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config_module.settings, "github_app_slug", "")
    response = client.get(
        "/api/repositories/connect-url", **_auth(session_token)
    )
    assert response.status_code == 500
