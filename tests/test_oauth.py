from quorum.auth.github_oauth import build_authorize_url


def test_build_authorize_url() -> None:
    url = build_authorize_url(
        client_id="test-client-id",
        redirect_uri="http://localhost:8000/auth/callback",
        state="test-state-123",
    )
    assert "github.com/login/oauth/authorize" in url
    assert "client_id=test-client-id" in url
    assert "redirect_uri=http" in url
    assert "state=test-state-123" in url
