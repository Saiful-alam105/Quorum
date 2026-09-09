import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database import models as db_models
from quorum.database.models import (
    AnalysisRun,
    ChatMessage,
    CoverageResult,
    PullRequest,
    Repository,
    SecurityFinding,
    User,
)


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


def _create_repository(session: Session) -> Repository:
    repo = Repository(
        github_id=101,
        owner="octocat",
        name="hello-world",
        full_name="octocat/hello-world",
        is_private=False,
    )
    session.add(repo)
    return repo


class TestRepositoryStoreRetrieve:
    def test_store_and_retrieve_repository(self, db_session: Session) -> None:
        repo = _create_repository(db_session)
        db_session.commit()

        stored = db_session.get(Repository, repo.id)
        assert stored is not None
        assert stored.full_name == "octocat/hello-world"
        assert stored.owner == "octocat"
        assert stored.name == "hello-world"
        assert stored.is_private is False

    def test_repository_full_name_is_unique(self, db_session: Session) -> None:
        _create_repository(db_session)
        db_session.commit()

        duplicate = Repository(
            github_id=102,
            owner="octocat",
            name="hello-world",
            full_name="octocat/hello-world",
        )
        db_session.add(duplicate)
        with pytest.raises(Exception):
            db_session.commit()


class TestPullRequestStoreRetrieve:
    def test_store_and_retrieve_pull_request(self, db_session: Session) -> None:
        repo = _create_repository(db_session)
        db_session.commit()

        pr = PullRequest(
            github_id=42,
            repository_id=repo.id,
            number=42,
            title="Add authentication",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()

        stored = db_session.get(PullRequest, pr.id)
        assert stored is not None
        assert stored.title == "Add authentication"
        assert stored.number == 42
        assert stored.state == "open"

    def test_pull_request_belongs_to_repository(self, db_session: Session) -> None:
        repo = _create_repository(db_session)
        db_session.commit()

        pr = PullRequest(
            github_id=43,
            repository_id=repo.id,
            number=43,
            title="Fix bug",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()

        stored = db_session.get(PullRequest, pr.id)
        assert stored is not None
        assert stored.repository is not None
        assert stored.repository.full_name == "octocat/hello-world"


class TestAnalysisRunStoreRetrieve:
    def test_store_and_retrieve_analysis_run(self, db_session: Session) -> None:
        repo = _create_repository(db_session)
        db_session.commit()

        pr = PullRequest(
            github_id=44,
            repository_id=repo.id,
            number=44,
            title="Add API endpoint",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()

        analysis = AnalysisRun(
            pull_request_id=pr.id,
            status="completed",
            merge_readiness_score=85,
        )
        db_session.add(analysis)
        db_session.commit()

        stored = db_session.get(AnalysisRun, analysis.id)
        assert stored is not None
        assert stored.status == "completed"
        assert stored.merge_readiness_score == 85

    def test_analysis_run_belongs_to_pull_request(self, db_session: Session) -> None:
        repo = _create_repository(db_session)
        db_session.commit()

        pr = PullRequest(
            github_id=45,
            repository_id=repo.id,
            number=45,
            title="Another PR",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()

        analysis = AnalysisRun(pull_request_id=pr.id, status="pending")
        db_session.add(analysis)
        db_session.commit()

        stored = db_session.get(AnalysisRun, analysis.id)
        assert stored is not None
        assert stored.pull_request is not None
        assert stored.pull_request.number == 45


class TestRelatedModels:
    def test_security_finding_belongs_to_analysis_run(self, db_session: Session) -> None:
        repo = _create_repository(db_session)
        db_session.commit()
        pr = PullRequest(
            github_id=46,
            repository_id=repo.id,
            number=46,
            title="SQL injection",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()
        analysis = AnalysisRun(pull_request_id=pr.id, status="completed")
        db_session.add(analysis)
        db_session.commit()

        finding = SecurityFinding(
            analysis_run_id=analysis.id,
            severity="high",
            title="SQL Injection",
            file="db.py",
            line=42,
            evidence="User input passed to execute()",
            explanation="Use parameterized queries",
            confidence=0.9,
        )
        db_session.add(finding)
        db_session.commit()

        stored = db_session.get(SecurityFinding, finding.id)
        assert stored is not None
        assert stored.severity == "high"
        assert stored.analysis_run is not None
        assert stored.analysis_run.status == "completed"

    def test_test_run_and_coverage_belong_to_analysis_run(
        self, db_session: Session
    ) -> None:
        repo = _create_repository(db_session)
        db_session.commit()
        pr = PullRequest(
            github_id=47,
            repository_id=repo.id,
            number=47,
            title="Tests",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()
        analysis = AnalysisRun(pull_request_id=pr.id, status="completed")
        db_session.add(analysis)
        db_session.commit()

        test_run = db_models.TestRun(
            analysis_run_id=analysis.id,
            test_name="test_login",
            status="passed",
            duration=0.5,
        )
        coverage = CoverageResult(
            analysis_run_id=analysis.id,
            coverage_before=72.0,
            coverage_after=81.0,
            coverage_delta=9.0,
        )
        db_session.add(test_run)
        db_session.add(coverage)
        db_session.commit()

        stored_analysis = db_session.get(AnalysisRun, analysis.id)
        assert stored_analysis is not None
        assert len(stored_analysis.test_runs) == 1
        assert stored_analysis.test_runs[0].test_name == "test_login"
        assert len(stored_analysis.coverage_results) == 1
        assert stored_analysis.coverage_results[0].coverage_delta == 9.0

    def test_chat_message_belongs_to_analysis_run_and_user(
        self, db_session: Session
    ) -> None:
        user = User(github_id=555, username="octocat")
        db_session.add(user)
        db_session.commit()

        repo = _create_repository(db_session)
        db_session.commit()
        pr = PullRequest(
            github_id=48,
            repository_id=repo.id,
            number=48,
            title="Chat",
            author="octocat",
            state="open",
        )
        db_session.add(pr)
        db_session.commit()
        analysis = AnalysisRun(pull_request_id=pr.id, status="completed")
        db_session.add(analysis)
        db_session.commit()

        message = ChatMessage(
            user_id=user.id,
            analysis_run_id=analysis.id,
            role="user",
            message="Why did this PR get 82?",
        )
        db_session.add(message)
        db_session.commit()

        stored = db_session.get(ChatMessage, message.id)
        assert stored is not None
        assert stored.role == "user"
        assert stored.message == "Why did this PR get 82?"
        assert stored.user is not None
        assert stored.user.username == "octocat"
        assert stored.analysis_run is not None