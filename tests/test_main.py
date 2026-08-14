from fastapi.testclient import TestClient

from quorum.main import app

client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Quorum"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_ping() -> None:
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "ping"},
        json={"zen": "Keep it logically awesome.", "hook_id": 1},
    )
    assert response.status_code == 200
    assert response.json()["event"] == "ping"


def test_webhook_supported_pull_request_action() -> None:
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "pull_request"},
        json={"action": "opened"},
    )
    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "event": "pull_request", "action": "opened"}


def test_webhook_ignored_event() -> None:
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "issues"},
        json={"action": "opened"},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"


def test_webhook_ignored_pull_request_action() -> None:
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "pull_request"},
        json={"action": "closed"},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"
