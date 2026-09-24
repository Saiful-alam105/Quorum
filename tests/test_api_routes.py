import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.auth.sessions import create_session
from quorum.database.base import Base, get_db
from quorum.database.models import PullRequest, Repository, User
from quorum.main import app
import quorum.config as config_module
import quorum.github.repo_sync as repo_sync_module


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
    return create_session({"github_id": 1, "username": "testuser"})


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth(client: TestClient, token: str) -> dict:
    return {"cookies": {"session": token}}


def _add_repository(db_session: Session, user: User) -> Repository:
    repo = Repository(
        github_id=201,
        owner="octocat",
        name="hello-world",
        full_name="octocat/hello-world",
        is_private=False,
        user_id=user.id,
    )
    db_session.add(repo)
    db_session.commit()
    return repo


def test_api_me_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/me")
    assert response.status_code == 401


def test_api_me_invalid_session(client: TestClient) -> None:
    response = client.get("/api/me", cookies={"session": "invalid-token"})
    assert response.status_code == 401


def test_api_me_authenticated(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(
        User(
            github_id=12345,
            username="testuser",
            avatar_url="https://example.com/avatar.png",
        )
    )
    db_session.commit()
    token = create_session({"github_id": 12345, "username": "testuser"})
    response = client.get("/api/me", cookies={"session": token})
    assert response.status_code == 200
    assert response.json() == {
        "github_id": 12345,
        "username": "testuser",
        "avatar_url": "https://example.com/avatar.png",
    }


def test_api_repositories_requires_auth(client: TestClient) -> None:
    response = client.get("/api/repositories")
    assert response.status_code == 401


def test_api_repositories_empty(
    client: TestClient, session_token: str
) -> None:
    response = client.get("/api/repositories", **_auth(client, session_token))
    assert response.status_code == 200
    assert response.json() == []


def test_api_repositories_returns_stored(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    _add_repository(db_session, user)

    response = client.get("/api/repositories", **_auth(client, session_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["full_name"] == "octocat/hello-world"
    assert data[0]["owner"] == "octocat"
    assert data[0]["is_private"] is False


def test_api_repositories_only_returns_own(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    _add_repository(db_session, user)
    other = User(github_id=2, username="other")
    db_session.add(other)
    db_session.commit()
    db_session.add(
        Repository(
            github_id=202,
            owner="other",
            name="private-repo",
            full_name="other/private-repo",
            is_private=True,
            user_id=other.id,
        )
    )
    db_session.commit()

    response = client.get("/api/repositories", **_auth(client, session_token))
    data = response.json()
    assert [item["full_name"] for item in data] == ["octocat/hello-world"]


def test_api_repositories_sorted_by_full_name(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    for github_id, full_name in [(2, "octocat/zeta"), (1, "octocat/alpha")]:
        db_session.add(
            Repository(
                github_id=github_id,
                owner="octocat",
                name=full_name.split("/")[1],
                full_name=full_name,
                is_private=False,
                user_id=user.id,
            )
        )
    db_session.commit()

    response = client.get("/api/repositories", **_auth(client, session_token))
    names = [item["full_name"] for item in response.json()]
    assert names == ["octocat/alpha", "octocat/zeta"]


def test_api_repository_by_id(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)

    response = client.get(f"/api/repositories/{repo.id}", **_auth(client, session_token))
    assert response.status_code == 200
    assert response.json()["full_name"] == "octocat/hello-world"


def test_api_repository_by_id_not_found(
    client: TestClient, session_token: str
) -> None:
    response = client.get("/api/repositories/999999", **_auth(client, session_token))
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_api_repository_by_id_not_owned(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    other = User(github_id=2, username="other")
    db_session.add(other)
    db_session.commit()
    other_repo = Repository(
        github_id=202,
        owner="other",
        name="private-repo",
        full_name="other/private-repo",
        is_private=True,
        user_id=other.id,
    )
    db_session.add(other_repo)
    db_session.commit()

    response = client.get(
        f"/api/repositories/{other_repo.id}", **_auth(client, session_token)
    )
    assert response.status_code == 404


def test_api_repository_pull_requests_empty(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)

    response = client.get(
        f"/api/repositories/{repo.id}/pull-requests", **_auth(client, session_token)
    )
    assert response.status_code == 200
    assert response.json() == []


def test_api_repository_pull_requests_returns(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    db_session.add(
        PullRequest(
            github_id=301,
            repository_id=repo.id,
            number=7,
            title="Add authentication",
            author="octocat",
            state="open",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/repositories/{repo.id}/pull-requests", **_auth(client, session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["number"] == 7
    assert data[0]["title"] == "Add authentication"
    assert data[0]["state"] == "open"


def test_api_repository_pull_requests_sorted_by_number_desc(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    for number in (1, 3, 2):
        db_session.add(
            PullRequest(
                github_id=300 + number,
                repository_id=repo.id,
                number=number,
                title=f"PR {number}",
                author="octocat",
                state="open",
            )
        )
    db_session.commit()

    response = client.get(
        f"/api/repositories/{repo.id}/pull-requests", **_auth(client, session_token)
    )
    numbers = [item["number"] for item in response.json()]
    assert numbers == [3, 2, 1]


def test_api_repository_pull_requests_not_found(
    client: TestClient, session_token: str
) -> None:
    response = client.get(
        "/api/repositories/999999/pull-requests", **_auth(client, session_token)
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_api_pull_requests_requires_auth(client: TestClient) -> None:
    response = client.get("/api/pull-requests")
    assert response.status_code == 401


def test_api_pull_requests_empty(
    client: TestClient, session_token: str
) -> None:
    response = client.get("/api/pull-requests", **_auth(client, session_token))
    assert response.status_code == 200
    assert response.json() == []


def test_api_pull_requests_returns_summaries(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    db_session.add(
        PullRequest(
            github_id=301,
            repository_id=repo.id,
            number=7,
            title="Add authentication",
            author="octocat",
            state="open",
        )
    )
    db_session.commit()

    response = client.get("/api/pull-requests", **_auth(client, session_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["number"] == 7
    assert data[0]["repository_full_name"] == "octocat/hello-world"


def test_api_pull_requests_sorted_by_id_desc(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    for i in (1, 2, 3):
        db_session.add(
            PullRequest(
                github_id=300 + i,
                repository_id=repo.id,
                number=i,
                title=f"PR {i}",
                author="octocat",
                state="open",
            )
        )
    db_session.commit()

    response = client.get("/api/pull-requests", **_auth(client, session_token))
    ids = [item["id"] for item in response.json()]
    assert ids == sorted(ids, reverse=True)


def test_api_pull_request_by_id(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = PullRequest(
        github_id=301,
        repository_id=repo.id,
        number=7,
        title="Add authentication",
        author="octocat",
        state="open",
    )
    db_session.add(pull_request)
    db_session.commit()

    response = client.get(
        f"/api/pull-requests/{pull_request.id}", **_auth(client, session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["number"] == 7
    assert data["title"] == "Add authentication"
    assert data["repository_id"] == repo.id
    assert data["repository_full_name"] == "octocat/hello-world"


def test_api_pull_request_by_id_not_found(
    client: TestClient, session_token: str
) -> None:
    response = client.get("/api/pull-requests/999999", **_auth(client, session_token))
    assert response.status_code == 404
    assert response.json()["detail"] == "Pull request not found"


def test_api_pull_request_not_owned(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    other = User(github_id=2, username="other")
    db_session.add(other)
    db_session.commit()
    other_repo = Repository(
        github_id=202,
        owner="other",
        name="private-repo",
        full_name="other/private-repo",
        is_private=True,
        user_id=other.id,
    )
    db_session.add(other_repo)
    db_session.commit()
    other_pr = PullRequest(
        github_id=302,
        repository_id=other_repo.id,
        number=9,
        title="Private PR",
        author="other",
        state="open",
    )
    db_session.add(other_pr)
    db_session.commit()

    response = client.get(
        f"/api/pull-requests/{other_pr.id}", **_auth(client, session_token)
    )
    assert response.status_code == 404


def test_api_repositories_syncs_from_github_on_refresh(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user.github_installation_id = 555
    db_session.commit()

    monkeypatch.setattr(config_module.settings, "github_app_id", "test-app-id")
    monkeypatch.setattr(
        config_module.settings, "github_app_private_key_path", "test-key.pem"
    )

    kept = Repository(
        github_id=1001,
        owner="quorum-dev",
        name="kept-repo",
        full_name="quorum-dev/kept-repo",
        is_private=False,
        user_id=user.id,
    )
    stale = Repository(
        github_id=1002,
        owner="quorum-dev",
        name="stale-repo",
        full_name="quorum-dev/stale-repo",
        is_private=False,
        user_id=user.id,
    )
    db_session.add(kept)
    db_session.add(stale)
    db_session.commit()

    async def mock_installation_token(app_id: str, key_path: str, installation_id: int) -> dict:
        return {"token": "install-token"}

    async def mock_installation_repos(token: str) -> list:
        return [
            {
                "id": 1001,
                "name": "kept-repo",
                "full_name": "quorum-dev/kept-repo",
                "private": False,
                "owner": {"login": "quorum-dev"},
            }
        ]

    monkeypatch.setattr(repo_sync_module, "get_installation_token", mock_installation_token)
    monkeypatch.setattr(
        repo_sync_module, "get_installation_repositories", mock_installation_repos
    )

    response = client.get("/api/repositories", **_auth(client, session_token))
    assert response.status_code == 200
    data = response.json()
    assert [item["full_name"] for item in data] == ["quorum-dev/kept-repo"]