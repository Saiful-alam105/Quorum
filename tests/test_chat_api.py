import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import quorum.chat.service as chat_service
from quorum.auth.sessions import create_session
from quorum.chat.context import build_review_context
from quorum.chat.service import build_chat_prompt
from quorum.database.base import Base, get_db
from quorum.database.models import (
    AnalysisRun,
    CoverageResult,
    PullRequest,
    Repository,
    SecurityFinding,
    TestRun,
    User,
)
from quorum.llm.base import LLMError
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
    return create_session({"github_id": 1, "username": "testuser"})


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


def _add_pull_request(
    db_session: Session, repo: Repository, number: int = 7
) -> PullRequest:
    pull_request = PullRequest(
        github_id=300 + number,
        repository_id=repo.id,
        number=number,
        title=f"PR {number}",
        author="octocat",
        state="open",
    )
    db_session.add(pull_request)
    db_session.commit()
    return pull_request


def _add_run(
    db_session: Session,
    pull_request: PullRequest,
    status: str = "completed",
    score: int | None = 82,
    findings: list[dict] | None = None,
    tests: list[dict] | None = None,
    coverage: tuple[float, float, float] | None = None,
) -> AnalysisRun:
    run = AnalysisRun(
        pull_request_id=pull_request.id,
        status=status,
        merge_readiness_score=score,
    )
    db_session.add(run)
    db_session.commit()
    for finding in findings or []:
        db_session.add(SecurityFinding(analysis_run_id=run.id, **finding))
    for test in tests or []:
        db_session.add(TestRun(analysis_run_id=run.id, **test))
    if coverage is not None:
        db_session.add(
            CoverageResult(
                analysis_run_id=run.id,
                coverage_before=coverage[0],
                coverage_after=coverage[1],
                coverage_delta=coverage[2],
            )
        )
    db_session.commit()
    return run


def _finding(severity: str = "high", **kwargs) -> dict:
    data = {
        "severity": severity,
        "title": f"{severity} issue",
        "file": "app.py",
        "line": 5,
        "evidence": "evidence",
        "explanation": "explanation",
        "confidence": 0.9,
        "rule_id": "python.security.example",
    }
    data.update(kwargs)
    return data


def _other_user_repo_pr(db_session: Session) -> tuple[User, Repository, PullRequest]:
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
    return other, other_repo, other_pr


class FakeProvider:
    def __init__(self, answer: str = "answer text", error: Exception | None = None):
        self.answer = answer
        self.error = error
        self.last_prompt = ""

    async def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        if self.error:
            raise self.error
        return self.answer


# --- context and prompt builders ---


def test_build_review_context_includes_evidence(
    db_session: Session, user: User
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(
        db_session,
        pull_request,
        score=82,
        findings=[
            _finding(severity="high", title="Shell injection", file="auth.py", line=5),
        ],
        tests=[{"test_name": "test_login", "status": "failed", "failure_reason": "boom"}],
        coverage=(72.0, 81.0, 9.0),
    )

    context = build_review_context(run)
    assert "octocat/hello-world #7" in context
    assert "PR 7" in context
    assert "82/100" in context
    assert "[HIGH] Shell injection (auth.py:5)" in context
    assert "test_login — failed" in context
    assert "coverage: 72.0% -> 81.0%" in context


def test_build_chat_prompt_is_grounded(
    db_session: Session, user: User
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(db_session, pull_request, findings=[_finding(severity="high")])

    prompt = build_chat_prompt(run, [], "What security issues were found?")
    assert "REVIEW CONTEXT:" in prompt
    assert "CONVERSATION HISTORY:" in prompt
    assert "USER QUESTION:" in prompt
    assert "What security issues were found?" in prompt
    assert "UNTRUSTED" in prompt


# --- GET /api/reviews/{id}/chat ---


def test_chat_history_requires_auth(client: TestClient) -> None:
    assert client.get("/api/reviews/1/chat").status_code == 401


def test_chat_history_not_found(client: TestClient, session_token: str) -> None:
    response = client.get("/api/reviews/999999/chat", **_auth(session_token))
    assert response.status_code == 404


def test_chat_history_not_owned(
    client: TestClient, db_session: Session, session_token: str
) -> None:
    _, _, other_pr = _other_user_repo_pr(db_session)
    other_run = _add_run(db_session, other_pr)
    response = client.get(f"/api/reviews/{other_run.id}/chat", **_auth(session_token))
    assert response.status_code == 404


def test_chat_history_empty(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(db_session, pull_request)

    response = client.get(f"/api/reviews/{run.id}/chat", **_auth(session_token))
    assert response.status_code == 200
    assert response.json() == []


# --- POST /api/reviews/{id}/chat ---


def test_chat_post_requires_auth(client: TestClient) -> None:
    assert client.post("/api/reviews/1/chat", json={"question": "hi"}).status_code == 401


def test_chat_post_not_owned(
    client: TestClient, db_session: Session, session_token: str
) -> None:
    _, _, other_pr = _other_user_repo_pr(db_session)
    other_run = _add_run(db_session, other_pr)
    response = client.post(
        f"/api/reviews/{other_run.id}/chat",
        json={"question": "hi"},
        **_auth(session_token),
    )
    assert response.status_code == 404


def test_chat_post_empty_question(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(db_session, pull_request)

    response = client.post(
        f"/api/reviews/{run.id}/chat",
        json={"question": "   "},
        **_auth(session_token),
    )
    assert response.status_code == 400


def test_chat_post_success_persists_messages(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(db_session, pull_request, findings=[_finding(severity="high")])

    provider = FakeProvider(answer="Two high-severity issues were found.")
    monkeypatch.setattr(chat_service, "create_llm_provider", lambda role=None: provider)

    response = client.post(
        f"/api/reviews/{run.id}/chat",
        json={"question": "What security issues were found?"},
        **_auth(session_token),
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Two high-severity issues were found."
    assert "USER QUESTION:" in provider.last_prompt

    history = client.get(f"/api/reviews/{run.id}/chat", **_auth(session_token))
    messages = history.json()
    assert len(messages) == 2
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["message"] == "What security issues were found?"
    assert messages[1]["message"] == "Two high-severity issues were found."


def test_chat_post_llm_failure_returns_503(
    client: TestClient,
    db_session: Session,
    user: User,
    session_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(db_session, pull_request)

    provider = FakeProvider(error=LLMError("model unavailable"))
    monkeypatch.setattr(chat_service, "create_llm_provider", lambda role=None: provider)

    response = client.post(
        f"/api/reviews/{run.id}/chat",
        json={"question": "hello"},
        **_auth(session_token),
    )
    assert response.status_code == 503

    history = client.get(f"/api/reviews/{run.id}/chat", **_auth(session_token))
    messages = history.json()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"