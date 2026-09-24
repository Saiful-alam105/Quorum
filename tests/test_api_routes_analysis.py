import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.auth.sessions import create_session
from quorum.database.base import Base, get_db
from quorum.database.models import (
    AnalysisRun,
    CoverageResult,
    PullRequest,
    Repository,
    SecurityFinding,
    TestRun,
    User,
    utcnow,
)
from quorum.database.repository import upsert_pull_request
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


# --- analysis runs per pull request ---


def test_analysis_requires_auth(client: TestClient) -> None:
    assert client.get("/api/pull-requests/1/analysis").status_code == 401
    assert client.get("/api/pull-requests/1/security").status_code == 401
    assert client.get("/api/pull-requests/1/tests").status_code == 401
    assert client.get("/api/pull-requests/1/coverage").status_code == 401


def test_analysis_pull_request_not_found(
    client: TestClient, session_token: str
) -> None:
    response = client.get(
        "/api/pull-requests/999999/analysis", **_auth(session_token)
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Pull request not found"


def test_analysis_pull_request_not_owned(
    client: TestClient, db_session: Session, session_token: str
) -> None:
    _, _, other_pr = _other_user_repo_pr(db_session)
    response = client.get(
        f"/api/pull-requests/{other_pr.id}/analysis", **_auth(session_token)
    )
    assert response.status_code == 404


def test_analysis_empty_when_no_runs(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/analysis", **_auth(session_token)
    )
    assert response.status_code == 200
    assert response.json() == []


def test_analysis_returns_runs_newest_first(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    first = _add_run(db_session, pull_request, status="completed", score=70)
    second = _add_run(db_session, pull_request, status="in_progress", score=None)

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/analysis", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [second.id, first.id]
    assert data[0]["status"] == "in_progress"
    assert data[0]["merge_readiness_score"] is None
    assert data[0]["recommendation"] is None
    assert data[1]["merge_readiness_score"] == 70
    assert data[1]["recommendation"] == "Approve with minor concerns"
    assert data[1]["pull_request_id"] == pull_request.id


def test_analysis_recommendation_bands(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(db_session, pull_request, score=95)
    _add_run(db_session, pull_request, score=60)
    _add_run(db_session, pull_request, score=30)

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/analysis", **_auth(session_token)
    )
    data = response.json()
    recommendations = {
        item["merge_readiness_score"]: item["recommendation"]
        for item in data
    }
    assert recommendations[95] == "Ready to merge"
    assert recommendations[60] == "Needs review"
    assert recommendations[30] == "Do not merge"


# --- security / tests / coverage for the latest run ---


def test_security_empty_when_no_runs(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/security", **_auth(session_token)
    )
    assert response.status_code == 200
    assert response.json() == []


def test_security_returns_latest_run_findings(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        score=50,
        findings=[_finding(severity="high", title="old issue")],
    )
    _add_run(
        db_session,
        pull_request,
        score=95,
        findings=[_finding(severity="low", title="new issue")],
    )

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/security", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "new issue"
    assert data[0]["severity"] == "low"
    assert data[0]["file"] == "app.py"
    assert data[0]["line"] == 5
    assert data[0]["rule_id"] == "python.security.example"
    assert data[0]["confidence"] == 0.9


def test_security_not_owned(
    client: TestClient, db_session: Session, session_token: str
) -> None:
    _, _, other_pr = _other_user_repo_pr(db_session)
    response = client.get(
        f"/api/pull-requests/{other_pr.id}/security", **_auth(session_token)
    )
    assert response.status_code == 404


def test_tests_empty_when_no_runs(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/tests", **_auth(session_token)
    )
    assert response.status_code == 200
    assert response.json() == []


def test_tests_returns_latest_run_tests(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        tests=[
            {"test_name": "test_old", "status": "passed"},
        ],
    )
    _add_run(
        db_session,
        pull_request,
        tests=[
            {"test_name": "test_new", "status": "failed", "failure_reason": "boom"},
        ],
    )

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/tests", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["test_name"] == "test_new"
    assert data[0]["status"] == "failed"
    assert data[0]["failure_reason"] == "boom"


def test_coverage_null_when_no_runs(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/coverage", **_auth(session_token)
    )
    assert response.status_code == 200
    assert response.json() is None


def test_coverage_returns_latest_run_result(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(db_session, pull_request, coverage=(72.0, 74.0, 2.0))
    _add_run(db_session, pull_request, coverage=(70.0, 81.0, 11.0))

    response = client.get(
        f"/api/pull-requests/{pull_request.id}/coverage", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["coverage_before"] == 70.0
    assert data["coverage_after"] == 81.0
    assert data["coverage_delta"] == 11.0


# --- reviews ---


def test_reviews_requires_auth(client: TestClient) -> None:
    assert client.get("/api/reviews").status_code == 401


def test_reviews_empty(client: TestClient, session_token: str) -> None:
    response = client.get("/api/reviews", **_auth(session_token))
    assert response.status_code == 200
    assert response.json() == []


def test_reviews_returns_summaries_with_counts(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        score=82,
        findings=[_finding(severity="high"), _finding(severity="medium")],
        tests=[
            {"test_name": "t1", "status": "passed"},
            {"test_name": "t2", "status": "failed"},
        ],
    )

    response = client.get("/api/reviews", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["pr_number"] == 7
    assert item["pr_title"] == "PR 7"
    assert item["pr_author"] == "octocat"
    assert item["pr_state"] == "open"
    assert item["repository_full_name"] == "octocat/hello-world"
    assert item["repository_id"] == repo.id
    assert item["status"] == "completed"
    assert item["merge_readiness_score"] == 82
    assert item["recommendation"] == "Approve with minor concerns"
    assert item["finding_count"] == 2
    assert item["test_count"] == 2
    assert item["started_at"] is None
    assert item["completed_at"] is None


def test_reviews_sorted_newest_first(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    first = _add_run(db_session, pull_request, score=70)
    second = _add_run(db_session, pull_request, score=95)

    response = client.get("/api/reviews", **_auth(session_token))
    ids = [item["id"] for item in response.json()]
    assert ids == [second.id, first.id]


def test_reviews_only_returns_own(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(db_session, pull_request, score=90)

    _, _, other_pr = _other_user_repo_pr(db_session)
    _add_run(db_session, other_pr, score=10)

    response = client.get("/api/reviews", **_auth(session_token))
    data = response.json()
    assert len(data) == 1
    assert data[0]["pr_title"] == "PR 7"


def test_review_by_id(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(
        db_session,
        pull_request,
        score=82,
        findings=[_finding(severity="high", title="sql injection")],
        tests=[{"test_name": "test_login", "status": "passed"}],
        coverage=(72.0, 81.0, 9.0),
    )

    response = client.get(f"/api/reviews/{run.id}", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run.id
    assert data["merge_readiness_score"] == 82
    assert len(data["findings"]) == 1
    assert data["findings"][0]["title"] == "sql injection"
    assert data["findings"][0]["severity"] == "high"
    assert len(data["tests"]) == 1
    assert data["tests"][0]["test_name"] == "test_login"
    assert data["coverage"]["coverage_before"] == 72.0
    assert data["coverage"]["coverage_delta"] == 9.0


def test_review_by_id_coverage_null(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    run = _add_run(db_session, pull_request, score=60)

    response = client.get(f"/api/reviews/{run.id}", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert data["coverage"] is None
    assert data["findings"] == []
    assert data["tests"] == []


def test_review_by_id_not_found(
    client: TestClient, session_token: str
) -> None:
    response = client.get("/api/reviews/999999", **_auth(session_token))
    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


def test_review_by_id_not_owned(
    client: TestClient, db_session: Session, session_token: str
) -> None:
    _, _, other_pr = _other_user_repo_pr(db_session)
    other_run = _add_run(db_session, other_pr, score=10)

    response = client.get(
        f"/api/reviews/{other_run.id}", **_auth(session_token)
    )
    assert response.status_code == 404


# --- pull request summaries include latest analysis ---


def test_pull_requests_summary_includes_latest_analysis(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        score=50,
        findings=[
            _finding(severity="critical", title="old critical"),
            _finding(severity="high", title="old high"),
        ],
        tests=[{"test_name": "t1", "status": "passed"}],
    )
    _add_run(
        db_session,
        pull_request,
        score=95,
        findings=[_finding(severity="low", title="new low")],
    )

    response = client.get("/api/pull-requests", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["latest_analysis_status"] == "completed"
    assert item["merge_readiness_score"] == 95
    assert item["finding_count"] == 1
    assert item["critical_count"] == 0
    assert item["test_count"] == 0
    assert item["updated_at"] is not None


def test_pull_requests_summary_no_analysis_defaults(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    _add_pull_request(db_session, repo)

    response = client.get("/api/pull-requests", **_auth(session_token))
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["latest_analysis_status"] is None
    assert item["merge_readiness_score"] is None
    assert item["finding_count"] == 0
    assert item["critical_count"] == 0
    assert item["test_count"] == 0


def test_pull_requests_summary_counts_critical(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        score=40,
        findings=[
            _finding(severity="critical"),
            _finding(severity="critical"),
            _finding(severity="medium"),
        ],
    )

    response = client.get("/api/pull-requests", **_auth(session_token))
    data = response.json()
    assert data[0]["finding_count"] == 3
    assert data[0]["critical_count"] == 2


def test_upsert_pull_request_refreshes_updated_at(
    db_session: Session, user: User
) -> None:
    from datetime import datetime, timedelta, timezone

    repo = _add_repository(db_session, user)
    pull_request = PullRequest(
        github_id=301,
        repository_id=repo.id,
        number=7,
        title="Add authentication",
        author="octocat",
        state="open",
        updated_at=utcnow() - timedelta(days=1),
    )
    db_session.add(pull_request)
    db_session.commit()

    upsert_pull_request(
        db_session,
        {
            "id": 301,
            "number": 7,
            "title": "Add authentication",
            "state": "open",
            "user": {"login": "octocat"},
        },
        repo,
    )

    db_session.refresh(pull_request)
    naive_now = datetime.now(timezone.utc).replace(tzinfo=None)
    assert pull_request.updated_at is not None
    assert pull_request.updated_at > naive_now - timedelta(hours=1)


# --- recent findings feed ---


def test_findings_requires_auth(client: TestClient) -> None:
    assert client.get("/api/findings").status_code == 401


def test_findings_empty(client: TestClient, session_token: str) -> None:
    response = client.get("/api/findings", **_auth(session_token))
    assert response.status_code == 200
    assert response.json() == []


def test_findings_returns_findings_with_pr_context(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        score=50,
        findings=[
            _finding(severity="high", title="subprocess shell"),
            _finding(severity="medium", title="eval detected"),
        ],
    )

    response = client.get("/api/findings", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    item = data[0]
    assert item["severity"] == "medium"
    assert item["title"] == "eval detected"
    assert item["file"] == "app.py"
    assert item["line"] == 5
    assert item["pr_number"] == 7
    assert item["pr_title"] == "PR 7"
    assert item["repository_full_name"] == "octocat/hello-world"
    assert item["rule_id"] == "python.security.example"


def test_findings_sorted_newest_first(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        findings=[
            _finding(severity="low", title="one"),
            _finding(severity="low", title="two"),
        ],
    )

    response = client.get("/api/findings", **_auth(session_token))
    titles = [item["title"] for item in response.json()]
    assert titles == ["two", "one"]


def test_findings_only_include_latest_run(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        findings=[_finding(severity="high", title="old run finding")],
    )
    _add_run(
        db_session,
        pull_request,
        findings=[_finding(severity="medium", title="latest run finding")],
    )

    response = client.get("/api/findings", **_auth(session_token))
    titles = [item["title"] for item in response.json()]
    assert titles == ["latest run finding"]


def test_findings_respects_limit(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(
        db_session,
        pull_request,
        findings=[
            _finding(severity="low", title="one"),
            _finding(severity="low", title="two"),
            _finding(severity="low", title="three"),
        ],
    )

    response = client.get("/api/findings?limit=2", **_auth(session_token))
    data = response.json()
    assert len(data) == 2
    assert [item["title"] for item in data] == ["three", "two"]


def test_findings_only_returns_own(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(db_session, pull_request, findings=[_finding(severity="high")])

    _, _, other_pr = _other_user_repo_pr(db_session)
    _add_run(db_session, other_pr, findings=[_finding(severity="critical")])

    response = client.get("/api/findings", **_auth(session_token))
    data = response.json()
    assert len(data) == 1
    assert data[0]["severity"] == "high"


# --- repository summaries include counts and latest analysis status ---


def test_repositories_summary_counts(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    first = _add_pull_request(db_session, repo, number=1)
    second = _add_pull_request(db_session, repo, number=2)
    _add_run(db_session, first, status="completed", score=90)
    _add_run(db_session, second, status="failed", score=None)

    response = client.get("/api/repositories", **_auth(session_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["full_name"] == "octocat/hello-world"
    assert item["pull_request_count"] == 2
    assert item["open_pull_request_count"] == 2
    assert item["latest_analysis_status"] == "failed"


def test_repositories_summary_empty_defaults(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    _add_repository(db_session, user)

    response = client.get("/api/repositories", **_auth(session_token))
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["pull_request_count"] == 0
    assert item["open_pull_request_count"] == 0
    assert item["latest_analysis_status"] is None


def test_repository_by_id_summary(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo)
    _add_run(db_session, pull_request, status="completed", score=82)

    response = client.get(
        f"/api/repositories/{repo.id}", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pull_request_count"] == 1
    assert data["latest_analysis_status"] == "completed"


def test_repository_pull_requests_return_analysis_summaries(
    client: TestClient, db_session: Session, user: User, session_token: str
) -> None:
    repo = _add_repository(db_session, user)
    pull_request = _add_pull_request(db_session, repo, number=3)
    _add_run(
        db_session,
        pull_request,
        status="completed",
        score=82,
        findings=[_finding(severity="critical")],
    )

    response = client.get(
        f"/api/repositories/{repo.id}/pull-requests", **_auth(session_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["number"] == 3
    assert item["latest_analysis_status"] == "completed"
    assert item["merge_readiness_score"] == 82
    assert item["finding_count"] == 1
    assert item["critical_count"] == 1
    assert item["repository_full_name"] == "octocat/hello-world"