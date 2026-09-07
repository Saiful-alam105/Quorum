import secrets

_sessions: dict[str, dict] = {}


def create_session(user_data: dict) -> str:
    token = secrets.token_hex(32)
    _sessions[token] = {**user_data}
    return token


def get_session(token: str) -> dict | None:
    data = _sessions.get(token)
    if data is None:
        return None
    return {**data}


def delete_session(token: str) -> None:
    _sessions.pop(token, None)


def clear_all_sessions() -> None:
    _sessions.clear()
