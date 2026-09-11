import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.auth.sessions import clear_all_sessions, create_session
from quorum.database.base import Base, get_db
from quorum.database.models import PullRequest, Repository
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
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def setup_function() -> None:
    clear_all_sessions()


def test_api_me_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/me")
    assert response.status_code == 401


def test_api_me_invalid_session(client: TestClient) -> None:
    response = client.get("/api/me", cookies={"session": "invalid-token"})
    assert response.status_code == 401


def test_api_me_authenticated(client: TestClient) -> None:
    token = create_session({"github_id": 12345, "username": "testuser"})
    response = client.get("/api/me", cookies={"session": token})
    assert response.status_code == 200
    assert response.json() == {"github_id": 12345, "username": "testuser"}


def test_api_repositories_empty(client: TestClient) -> None:
    response = client.get("/api/repositories")
    assert response.status_code == 200
    assert response.json() == []


def test_api_repositories_returns_stored(client: TestClient, db_session: Session) -> None:
    db_session.add(
        Repository(
            github_id=201,
            owner="octocat",
            name="hello-world",
            full_name="octocat/hello-world",
            is_private=False,
        )
    )
    db_session.commit()

    response = client.get("/api/repositories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["full_name"] == "octocat/hello-world"
    assert data[0]["owner"] == "octocat"
    assert data[0]["is_private"] is False


def test_api_repositories_sorted_by_full_name(client: TestClient, db_session: Session) -> None:
    for github_id, full_name in [(2, "octocat/zeta"), (1, "octocat/alpha")]:
        db_session.add(
            Repository(
                github_id=github_id,
                owner="octocat",
                name=full_name.split("/")[1],
                full_name=full_name,
                is_private=False,
            )
        )
    db_session.commit()

    response = client.get("/api/repositories")
    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()]
    assert names == ["octocat/alpha", "octocat/zeta"]


def _add_repository(db_session: Session) -> Repository:
    repo = Repository(
        github_id=201,
        owner="octocat",
        name="hello-world",
        full_name="octocat/hello-world",
        is_private=False,
    )
    db_session.add(repo)
    db_session.commit()
    return repo


def test_api_repository_by_id(client: TestClient, db_session: Session) -> None:
    repo = _add_repository(db_session)

    response = client.get(f"/api/repositories/{repo.id}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "octocat/hello-world"


def test_api_repository_by_id_not_found(client: TestClient) -> None:
    response = client.get("/api/repositories/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_api_repository_pull_requests_empty(client: TestClient, db_session: Session) -> None:
    repo = _add_repository(db_session)

    response = client.get(f"/api/repositories/{repo.id}/pull-requests")
    assert response.status_code == 200
    assert response.json() == []


def test_api_repository_pull_requests_returns(
    client: TestClient, db_session: Session
) -> None:
    repo = _add_repository(db_session)
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

    response = client.get(f"/api/repositories/{repo.id}/pull-requests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["number"] == 7
    assert data[0]["title"] == "Add authentication"
    assert data[0]["state"] == "open"


def test_api_repository_pull_requests_sorted_by_number_desc(
    client: TestClient, db_session: Session
) -> None:
    repo = _add_repository(db_session)
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

    response = client.get(f"/api/repositories/{repo.id}/pull-requests")
    numbers = [item["number"] for item in response.json()]
    assert numbers == [3, 2, 1]


def test_api_repository_pull_requests_not_found(client: TestClient) -> None:
    response = client.get("/api/repositories/999999/pull-requests")
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"
