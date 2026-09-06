import json

from fastapi.testclient import TestClient

from conftest import sign_body
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
    body = json.dumps({"zen": "Keep it logically awesome.", "hook_id": 1}).encode()
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": sign_body(body)},
        content=body,
    )
    assert response.status_code == 200
    assert response.json()["event"] == "ping"


def test_webhook_supported_pull_request_action() -> None:
    body = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": sign_body(body)},
        content=body,
    )
    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "event": "pull_request", "action": "opened"}


def test_webhook_ignored_event() -> None:
    body = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": sign_body(body)},
        content=body,
    )
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"


def test_webhook_ignored_pull_request_action() -> None:
    body = json.dumps({"action": "closed"}).encode()
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": sign_body(body)},
        content=body,
    )
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"


def test_webhook_invalid_signature() -> None:
    body = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=deadbeef"},
        content=body,
    )
    assert response.status_code == 401
    assert response.json() == {"status": "invalid signature"}


def test_webhook_missing_signature() -> None:
    body = json.dumps({"action": "opened"}).encode()
    response = client.post(
        "/webhooks/github",
        headers={"X-GitHub-Event": "pull_request"},
        content=body,
    )
    assert response.status_code == 401