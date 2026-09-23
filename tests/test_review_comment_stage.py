import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.security_agent import SecurityAgentFinding
from quorum.agents.synthesis import MergeReadinessResult
from quorum.agents.test_runner import STATUS_PASSED, TestOutcome
from quorum.database.base import Base
from quorum.database.models import CoverageResult, PullRequest, Repository, User
from quorum.database.repository import create_analysis_run
from quorum.github.comment_service import CommentPostError
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext
from quorum.orchestrator.stages import post_review_comment_stage


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


def _create_pr_with_user(db: Session) -> PullRequest:
    user = User(github_id=777, username="octocat", github_installation_id=555)
    db.add(user)
    db.commit()
    repo = Repository(
        github_id=101,
        owner="octocat",
        name="hello-world",
        full_name="octocat/hello-world",
        is_private=False,
        user_id=user.id,
    )
    db.add(repo)
    db.commit()
    pr = PullRequest(
        github_id=301,
        repository_id=repo.id,
        number=7,
        title="Add authentication",
        author="octocat",
        state="open",
    )
    db.add(pr)
    db.commit()
    return pr


def _context(analysis_run_id: int) -> AnalysisContext:
    return AnalysisContext(
        pull_request_id=1,
        repository_id=1,
        owner="octocat",
        repo="hello-world",
        pr_number=7,
        installation_id=555,
        analysis_run_id=analysis_run_id,
        merge_readiness=MergeReadinessResult(score=82, recommendation="Approve with minor concerns"),
        security_findings=[
            SecurityAgentFinding(
                severity="high", title="t", file="f.py", evidence="e", confidence=0.9
            )
        ],
        test_results=[TestOutcome(name="t::x", status=STATUS_PASSED)],
        coverage=CoverageResult(coverage_before=0.0, coverage_after=80.0, coverage_delta=80.0),
    )


class TestPostReviewCommentStage:
    @pytest.mark.asyncio
    async def test_builds_and_posts_comment(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        posted: list[tuple] = []

        async def fake_post(installation_id, owner, repo, pr_number, body):
            posted.append((owner, repo, pr_number, body))

        monkeypatch.setattr(
            "quorum.orchestrator.stages.post_review_comment", fake_post
        )

        await post_review_comment_stage(db_session, context)

        assert len(posted) == 1
        owner, repo, pr_number, body = posted[0]
        assert (owner, repo, pr_number) == ("octocat", "hello-world", 7)
        assert "## Quorum Review" in body
        assert "82/100" in body

    @pytest.mark.asyncio
    async def test_missing_run_id_raises(self, db_session: Session) -> None:
        context = _context(analysis_run_id=None)
        with pytest.raises(CommentPostError, match="no analysis run id"):
            await post_review_comment_stage(db_session, context)

    @pytest.mark.asyncio
    async def test_missing_installation_raises(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        context.installation_id = None
        with pytest.raises(CommentPostError, match="no GitHub installation id"):
            await post_review_comment_stage(db_session, context)

    @pytest.mark.asyncio
    async def test_post_failure_propagates(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)

        async def failing_post(installation_id, owner, repo, pr_number, body):
            raise CommentPostError("github down")

        monkeypatch.setattr(
            "quorum.orchestrator.stages.post_review_comment", failing_post
        )

        with pytest.raises(CommentPostError, match="github down"):
            await post_review_comment_stage(db_session, context)


class TestRegistration:
    def test_post_review_comment_stage_is_registered(self) -> None:
        assert post_review_comment_stage in runner.STAGES