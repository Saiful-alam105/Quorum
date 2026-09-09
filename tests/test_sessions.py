from quorum.auth.sessions import clear_all_sessions, create_session, delete_session, get_session


def setup_function() -> None:
    clear_all_sessions()


def test_create_session_returns_token() -> None:
    token = create_session({"username": "alice"})
    assert isinstance(token, str)
    assert len(token) == 64


def test_get_session_returns_data() -> None:
    token = create_session({"username": "alice", "github_id": 123})
    data = get_session(token)
    assert data is not None
    assert data["username"] == "alice"
    assert data["github_id"] == 123


def test_get_session_returns_copy() -> None:
    token = create_session({"username": "alice"})
    data1 = get_session(token)
    data2 = get_session(token)
    assert data1 is not data2


def test_get_session_unknown_token() -> None:
    assert get_session("nonexistent") is None


def test_delete_session() -> None:
    token = create_session({"username": "alice"})
    delete_session(token)
    assert get_session(token) is None


def test_delete_session_unknown_is_safe() -> None:
    delete_session("nonexistent")


def test_clear_all_sessions() -> None:
    create_session({"username": "alice"})
    create_session({"username": "bob"})
    clear_all_sessions()
    assert get_session("any") is None
