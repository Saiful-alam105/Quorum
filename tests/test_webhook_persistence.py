import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from conftest import sign_body
from quorum.database.base import Base, get_db
from quorum.database.models import PullRequest, User
from quorum.database.repository import get_pull_request, get_repository_by_full_name
from quorum.main import app


def _webhook_payload(action: str = "opened", title: str = "Add authentication") -> bytes:
    payload = {
        "action": action,
        "repository": {
            "id": 201,
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "private": False,
            "owner": {"login": "octocat"},
        },
        "pull_request": {
            "id": 301,
            "number": 7,
            "title": title,
            "state": "open",
            "user": {"login": "octocat"},
        },
    }
    return json.dumps(payload).encode()


def _webhook_headers(raw_body: bytes) -> dict:
    return {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": sign_body(raw_body),
    }


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


class TestWebhookPersistence:
    def test_webhook_stores_repository_and_pull_request(
        self, client: TestClient, db_session: Session
    ) -> None:
        body = _webhook_payload()
        response = client.post(
            "/webhooks/github", headers=_webhook_headers(body), content=body
        )

        assert response.status_code == 202
        assert response.json() == {
            "status": "accepted",
            "event": "pull_request",
            "action": "opened",
        }

        repository = get_repository_by_full_name(db_session, "octocat/hello-world")
        assert repository is not None
        assert repository.owner == "octocat"
        assert repository.name == "hello-world"
        assert repository.is_private is False

        pull_request = get_pull_request(db_session, 301)
        assert pull_request is not None
        assert pull_request.title == "Add authentication"
        assert pull_request.number == 7
        assert pull_request.author == "octocat"
        assert pull_request.state == "open"
        assert pull_request.repository is not None
        assert pull_request.repository.full_name == "octocat/hello-world"

    def test_webhook_synchronize_updates_existing_pull_request(
        self, client: TestClient, db_session: Session
    ) -> None:
        first = _webhook_payload(action="opened")
        client.post("/webhooks/github", headers=_webhook_headers(first), content=first)

        second = _webhook_payload(action="synchronize", title="Add authentication v2")
        response = client.post(
            "/webhooks/github", headers=_webhook_headers(second), content=second
        )
        assert response.status_code == 202

        pull_requests = db_session.scalars(
            select(PullRequest).where(PullRequest.github_id == 301)
        ).all()
        assert len(pull_requests) == 1
        assert pull_requests[0].title == "Add authentication v2"

    def test_invalid_signature_does_not_store(
        self, client: TestClient, db_session: Session
    ) -> None:
        body = _webhook_payload()
        response = client.post(
            "/webhooks/github",
            headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=deadbeef"},
            content=body,
        )

        assert response.status_code == 401
        assert get_repository_by_full_name(db_session, "octocat/hello-world") is None
        assert get_pull_request(db_session, 301) is None


class TestRepositoryGetters:
    def test_getters_return_none_when_missing(self, db_session: Session) -> None:
        assert get_repository_by_full_name(db_session, "missing/foo") is None
        assert get_pull_request(db_session, 999) is None


class TestInstallationRevocation:
    def test_installation_deleted_revokes_user(
        self, client: TestClient, db_session: Session
    ) -> None:
        db_session.add(
            User(github_id=555, username="octocat", github_installation_id=777)
        )
        db_session.commit()

        body = json.dumps(
            {"action": "deleted", "installation": {"id": 777, "account": {"id": 555}}}
        ).encode()
        response = client.post(
            "/webhooks/github",
            headers={"X-GitHub-Event": "installation", "X-Hub-Signature-256": sign_body(body)},
            content=body,
        )
        assert response.status_code == 200

        user = db_session.scalar(select(User).where(User.github_id == 555))
        assert user is not None
        assert user.github_installation_id is None

    def test_installation_created_does_not_revoke(
        self, client: TestClient, db_session: Session
    ) -> None:
        db_session.add(
            User(github_id=555, username="octocat", github_installation_id=777)
        )
        db_session.commit()

        body = json.dumps(
            {"action": "created", "installation": {"id": 777, "account": {"id": 555}}}
        ).encode()
        response = client.post(
            "/webhooks/github",
            headers={"X-GitHub-Event": "installation", "X-Hub-Signature-256": sign_body(body)},
            content=body,
        )
        assert response.status_code == 200

        user = db_session.scalar(select(User).where(User.github_id == 555))
        assert user is not None
        assert user.github_installation_id == 777

    def test_installation_deleted_invalid_signature_does_not_revoke(
        self, client: TestClient, db_session: Session
    ) -> None:
        db_session.add(
            User(github_id=555, username="octocat", github_installation_id=777)
        )
        db_session.commit()

        body = json.dumps(
            {"action": "deleted", "installation": {"id": 777, "account": {"id": 555}}}
        ).encode()
        response = client.post(
            "/webhooks/github",
            headers={
                "X-GitHub-Event": "installation",
                "X-Hub-Signature-256": "sha256=deadbeef",
            },
            content=body,
        )
        assert response.status_code == 401

        user = db_session.scalar(select(User).where(User.github_id == 555))
        assert user is not None
        assert user.github_installation_id == 777