import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import quorum.api.routes as routes_module
import quorum.config as config_module
import quorum.github.repo_sync as repo_sync_module
from quorum.auth.sessions import create_session
from quorum.database.base import Base, get_db
from quorum.database.models import PullRequest, Repository, User
from quorum.database.repository import get_repository_by_full_name
from quorum.github.repo_sync import sync_user_repositories
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


# --- branches ---


def _install(user: User, db_session: Session) -> None:
    user.github_installation_id = 555
    db_session.commit()


def _mock_install_token(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_token(app_id, key_path, installation_id):
        return {"token": "install-token"}

    monkeypatch.setattr(routes_module, "get_installation_token", mock_token)


def test_branches_requires_auth(client: TestClient) -> None:
    assert client.get("/api/repositories/1/branches").status_code == 401


def test_branches_not_owned(client: TestClient, session_token: str) -> None:
    response = client.get("/api/repositories/999999/branches", **_auth(session_token))
    assert response.status_code == 404


def test_branches_requires_installation(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    response = client.get(
        f"/api/repositories/{repo.id}/branches", **_auth(session_token)
    )
    assert response.status_code == 400


def test_branches_returns_sorted(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(user, db_session)
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _mock_install_token(monkeypatch)

    async def mock_list_branches(token, owner, name):
        return ["main", "feature/auth", "dev"]

    monkeypatch.setattr(routes_module, "list_branches", mock_list_branches)

    response = client.get(
        f"/api/repositories/{repo.id}/branches", **_auth(session_token)
    )
    assert response.status_code == 200
    assert response.json() == ["dev", "feature/auth", "main"]


def test_branches_github_error_returns_502(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(user, db_session)
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _mock_install_token(monkeypatch)

    async def mock_list_branches(token, owner, name):
        raise RuntimeError("GitHub down")

    monkeypatch.setattr(routes_module, "list_branches", mock_list_branches)

    response = client.get(
        f"/api/repositories/{repo.id}/branches", **_auth(session_token)
    )
    assert response.status_code == 502


# --- create pull request ---


def _github_pr(number: int = 42) -> dict:
    return {
        "id": 900042,
        "number": number,
        "title": "Add authentication",
        "state": "open",
        "head": {"ref": "feature/auth"},
        "base": {"ref": "main"},
        "user": {"login": "octocat"},
    }


def test_create_pr_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/repositories/1/pull-requests",
        json={"title": "t", "head": "h", "base": "b"},
    )
    assert response.status_code == 401


def test_create_pr_not_owned(
    client: TestClient, session_token: str
) -> None:
    response = client.post(
        "/api/repositories/999999/pull-requests",
        json={"title": "t", "head": "h", "base": "b"},
        **_auth(session_token),
    )
    assert response.status_code == 404


def test_create_pr_requires_fields(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    response = client.post(
        f"/api/repositories/{repo.id}/pull-requests",
        json={"title": "  ", "head": "feature/auth", "base": "main"},
        **_auth(session_token),
    )
    assert response.status_code == 400


def test_create_pr_requires_installation(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    response = client.post(
        f"/api/repositories/{repo.id}/pull-requests",
        json={"title": "t", "head": "feature/auth", "base": "main"},
        **_auth(session_token),
    )
    assert response.status_code == 400


def test_create_pr_success_persists_and_triggers_analysis(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(user, db_session)
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _mock_install_token(monkeypatch)

    async def mock_create_pr(token, owner, name, title, head, base, body=None):
        return _github_pr()

    monkeypatch.setattr(routes_module, "create_pull_request", mock_create_pr)
    called = []

    async def mock_run(pull_request_id):
        called.append(pull_request_id)

    monkeypatch.setattr(routes_module, "run_analysis_for_pull_request", mock_run)

    response = client.post(
        f"/api/repositories/{repo.id}/pull-requests",
        json={"title": "Add authentication", "head": "feature/auth", "base": "main"},
        **_auth(session_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["number"] == 42
    assert data["head_ref"] == "feature/auth"
    assert data["base_ref"] == "main"

    from quorum.database.models import PullRequest

    pr = db_session.query(PullRequest).filter_by(github_id=900042).first()
    assert pr is not None
    assert pr.head_ref == "feature/auth"
    assert pr.base_ref == "main"
    assert called == [pr.id]


def test_create_pr_github_error_returns_502(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(user, db_session)
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _mock_install_token(monkeypatch)

    async def mock_create_pr(token, owner, name, title, head, base, body=None):
        raise RuntimeError("GitHub rejected the PR")

    monkeypatch.setattr(routes_module, "create_pull_request", mock_create_pr)

    response = client.post(
        f"/api/repositories/{repo.id}/pull-requests",
        json={"title": "t", "head": "feature/auth", "base": "main"},
        **_auth(session_token),
    )
    assert response.status_code == 502


# --- unconnect ---


def test_unconnect_requires_auth(
    client: TestClient, db_session: Session, user: User
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    response = client.post(f"/api/repositories/{repo.id}/unconnect")
    assert response.status_code == 401


def test_unconnect_not_owned_returns_404(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _, other_token = _other_user(user, db_session)
    response = client.post(
        f"/api/repositories/{repo.id}/unconnect", **_auth(other_token)
    )
    assert response.status_code == 404


def test_unconnect_detaches_repository(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")

    response = client.post(
        f"/api/repositories/{repo.id}/unconnect", **_auth(session_token)
    )
    assert response.status_code == 200
    db_session.refresh(repo)
    assert repo.user_id is None

    async def mock_get_repositories(token: str) -> list:
        return [_github_repo(201, "octocat/alpha")]

    monkeypatch.setattr(routes_module, "get_repositories", mock_get_repositories)
    discovered = client.get(
        "/api/repositories/discover", **_auth(session_token)
    ).json()
    assert discovered[0]["connected"] is False


def test_unconnect_is_remembered_as_exclusion(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    client.post(f"/api/repositories/{repo.id}/unconnect", **_auth(session_token))
    db_session.refresh(user)
    assert user.excluded_repositories == ["octocat/alpha"]


def test_auto_sync_does_not_reattach_disconnected_repo(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user.github_installation_id = 555
    user.excluded_repositories = ["quorum-dev/kept-repo"]
    kept = _add_connected_repo(db_session, user, 1001, "quorum-dev/kept-repo")
    other = _add_connected_repo(db_session, user, 1002, "quorum-dev/other-repo")
    db_session.commit()

    monkeypatch.setattr(config_module.settings, "github_app_id", "test-app-id")
    monkeypatch.setattr(
        config_module.settings, "github_app_private_key_path", "test-key.pem"
    )

    async def mock_installation_token(app_id: str, key_path: str, installation_id: int) -> dict:
        return {"token": "install-token"}

    async def mock_installation_repos(token: str) -> list:
        return [
            _github_repo(1001, "quorum-dev/kept-repo"),
            _github_repo(1002, "quorum-dev/other-repo"),
        ]

    monkeypatch.setattr(repo_sync_module, "get_installation_token", mock_installation_token)
    monkeypatch.setattr(
        repo_sync_module, "get_installation_repositories", mock_installation_repos
    )

    response = client.get("/api/repositories", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert [item["full_name"] for item in data] == ["quorum-dev/other-repo"]
    db_session.refresh(kept)
    assert kept.user_id is None
    db_session.refresh(other)
    assert other.user_id == user.id


def test_sync_clears_exclusions_on_explicit_connect(
    db_session: Session,
    user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user.github_installation_id = 555
    user.excluded_repositories = ["quorum-dev/kept-repo"]
    _add_connected_repo(db_session, user, 1001, "quorum-dev/kept-repo")
    db_session.commit()

    monkeypatch.setattr(config_module.settings, "github_app_id", "test-app-id")
    monkeypatch.setattr(
        config_module.settings, "github_app_private_key_path", "test-key.pem"
    )

    async def mock_installation_token(app_id: str, key_path: str, installation_id: int) -> dict:
        return {"token": "install-token"}

    async def mock_installation_repos(token: str) -> list:
        return [_github_repo(1001, "quorum-dev/kept-repo")]

    monkeypatch.setattr(repo_sync_module, "get_installation_token", mock_installation_token)
    monkeypatch.setattr(
        repo_sync_module, "get_installation_repositories", mock_installation_repos
    )

    import asyncio

    asyncio.run(sync_user_repositories(db_session, user, clear_exclusions=True))

    assert user.excluded_repositories == []
    assert get_repository_by_full_name(db_session, "quorum-dev/kept-repo").user_id == user.id


# --- cross-user authorization hardening ---


def _other_user(client_ctx: User, db_session: Session) -> tuple[User, str]:
    other = User(github_id=2, username="other")
    db_session.add(other)
    db_session.commit()
    token = create_session(
        {"github_id": 2, "username": "other", "access_token": "other-token"}
    )
    return other, token


def test_user_cannot_access_another_users_repository_data(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _, other_token = _other_user(user, db_session)

    for path in (
        f"/api/repositories/{repo.id}/branches",
        f"/api/repositories/{repo.id}",
    ):
        response = client.get(path, **_auth(other_token))
        assert response.status_code == 404


def test_user_cannot_create_pr_on_another_users_repository(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _, other_token = _other_user(user, db_session)

    response = client.post(
        f"/api/repositories/{repo.id}/pull-requests",
        json={"title": "t", "head": "feature/auth", "base": "main"},
        **_auth(other_token),
    )
    assert response.status_code == 404


def test_discovery_marks_only_own_repos_connected(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _add_connected_repo(db_session, user, 201, "octocat/alpha")
    _, other_token = _other_user(user, db_session)

    async def mock_get_repositories(token: str) -> list:
        # Both users share the same GitHub repos; only `user` has them connected.
        return [
            _github_repo(201, "octocat/alpha"),
            _github_repo(202, "octocat/beta"),
        ]

    monkeypatch.setattr(routes_module, "get_repositories", mock_get_repositories)

    response = client.get(
        "/api/repositories/discover", **_auth(other_token)
    )
    data = response.json()
    assert {item["full_name"]: item["connected"] for item in data} == {
        "octocat/alpha": False,
        "octocat/beta": False,
    }
