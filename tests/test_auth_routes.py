import pytest
from fastapi.testclient import TestClient

from quorum.auth.sessions import clear_all_sessions
from quorum.main import app
import quorum.auth.routes as routes_module
import quorum.config as config_module


client = TestClient(app)


def setup_function() -> None:
    clear_all_sessions()


@pytest.fixture
def mock_github_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "github_client_id", "test-client-id")
    monkeypatch.setattr(config_module.settings, "github_client_secret", "test-client-secret")
    monkeypatch.setattr(config_module.settings, "github_redirect_uri", "http://localhost:8000/auth/callback")
    monkeypatch.setattr(config_module.settings, "frontend_url", "")


def test_login_returns_authorize_url(mock_github_config: None) -> None:
    response = client.get("/auth/login")
    assert response.status_code == 200
    data = response.json()
    assert "authorize_url" in data
    assert "github.com/login/oauth/authorize" in data["authorize_url"]
    assert "client_id=test-client-id" in data["authorize_url"]


def test_login_sets_state_cookie(mock_github_config: None) -> None:
    response = client.get("/auth/login")
    assert response.status_code == 200
    cookies = response.cookies
    assert "oauth_state" in cookies


def test_login_missing_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "github_client_id", "")
    response = client.get("/auth/login")
    assert response.status_code == 500
    assert "not configured" in response.json()["detail"]


def test_callback_invalid_state(mock_github_config: None) -> None:
    response = client.get("/auth/callback?code=test-code&state=wrong-state")
    assert response.status_code == 400
    assert "Invalid OAuth state" in response.json()["detail"]


def test_callback_missing_state_cookie(mock_github_config: None) -> None:
    response = client.get("/auth/callback?code=test-code&state=some-state")
    assert response.status_code == 400


def test_callback_success(mock_github_config: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_exchange(client_id: str, client_secret: str, code: str) -> str:
        return "mock-access-token"

    async def mock_get_user(access_token: str) -> dict:
        return {"id": 12345, "login": "testuser"}

    monkeypatch.setattr(routes_module, "exchange_code", mock_exchange)
    monkeypatch.setattr(routes_module, "get_github_user", mock_get_user)

    login_response = client.get("/auth/login")
    state = login_response.cookies.get("oauth_state")

    callback_response = client.get(f"/auth/callback?code=test-code&state={state}")
    assert callback_response.status_code == 200
    data = callback_response.json()
    assert data["username"] == "testuser"
    assert data["github_id"] == 12345
    assert "session" in callback_response.cookies


def test_callback_redirects_to_frontend_when_configured(
    mock_github_config: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config_module.settings, "frontend_url", "http://localhost:5173")

    async def mock_exchange(client_id: str, client_secret: str, code: str) -> str:
        return "mock-access-token"

    async def mock_get_user(access_token: str) -> dict:
        return {"id": 12345, "login": "testuser"}

    monkeypatch.setattr(routes_module, "exchange_code", mock_exchange)
    monkeypatch.setattr(routes_module, "get_github_user", mock_get_user)

    login_response = client.get("/auth/login")
    state = login_response.cookies.get("oauth_state")

    callback_response = client.get(
        f"/auth/callback?code=test-code&state={state}", follow_redirects=False
    )
    assert callback_response.status_code == 302
    assert callback_response.headers["location"] == "http://localhost:5173/"
    assert "session" in callback_response.cookies


def test_me_unauthenticated() -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_invalid_session() -> None:
    response = client.get("/auth/me", cookies={"session": "invalid-token"})
    assert response.status_code == 401


def test_me_authenticated(mock_github_config: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_exchange(client_id: str, client_secret: str, code: str) -> str:
        return "mock-access-token"

    async def mock_get_user(access_token: str) -> dict:
        return {"id": 12345, "login": "testuser"}

    monkeypatch.setattr(routes_module, "exchange_code", mock_exchange)
    monkeypatch.setattr(routes_module, "get_github_user", mock_get_user)

    login_response = client.get("/auth/login")
    state = login_response.cookies.get("oauth_state")

    callback_response = client.get(f"/auth/callback?code=test-code&state={state}")
    session_token = callback_response.cookies.get("session")

    me_response = client.get("/auth/me", cookies={"session": session_token})
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == "testuser"
    assert data["github_id"] == 12345


def test_logout(mock_github_config: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_exchange(client_id: str, client_secret: str, code: str) -> str:
        return "mock-access-token"

    async def mock_get_user(access_token: str) -> dict:
        return {"id": 12345, "login": "testuser"}

    monkeypatch.setattr(routes_module, "exchange_code", mock_exchange)
    monkeypatch.setattr(routes_module, "get_github_user", mock_get_user)

    login_response = client.get("/auth/login")
    state = login_response.cookies.get("oauth_state")

    callback_response = client.get(f"/auth/callback?code=test-code&state={state}")
    session_token = callback_response.cookies.get("session")

    logout_response = client.post("/auth/logout", cookies={"session": session_token})
    assert logout_response.status_code == 200
    assert logout_response.json()["status"] == "logged_out"

    me_response = client.get("/auth/me", cookies={"session": session_token})
    assert me_response.status_code == 401


def test_logout_without_session() -> None:
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["status"] == "logged_out"
