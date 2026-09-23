import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.security_agent import SecurityAgentFinding
from quorum.agents.synthesis import SynthesisError
from quorum.agents.test_runner import STATUS_PASSED, TestOutcome
from quorum.database.base import Base
from quorum.database.models import CoverageResult, PullRequest, Repository, User
from quorum.database.repository import create_analysis_run
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext
from quorum.orchestrator.stages import synthesize_stage


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
    )


class TestSynthesizeStage:
    @pytest.mark.asyncio
    async def test_stores_score_from_evidence(
        self, db_session: Session
    ) -> None:
        pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        context.security_findings = [
            SecurityAgentFinding(
                severity="high", title="t", file="f.py", evidence="e", confidence=0.9
            )
        ]
        context.test_results = [TestOutcome(name="t::x", status=STATUS_PASSED)]
        context.coverage = CoverageResult(coverage_before=0.0, coverage_after=95.0, coverage_delta=95.0)

        await synthesize_stage(db_session, context)

        assert context.merge_readiness is not None
        assert context.merge_readiness.score == 80
        assert context.merge_readiness.security_deduction == 20
        assert context.merge_readiness.coverage_deduction == 0
        db_session.refresh(run)
        assert run.merge_readiness_score == 80

    @pytest.mark.asyncio
    async def test_empty_evidence_still_scores(self, db_session: Session) -> None:
        pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)

        await synthesize_stage(db_session, context)

        assert context.merge_readiness is not None
        assert context.merge_readiness.score == 80  # no tests (-10), no coverage (-10)
        db_session.refresh(run)
        assert run.merge_readiness_score == 80

    @pytest.mark.asyncio
    async def test_no_coverage_sets_none(self, db_session: Session) -> None:
        pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        context.test_results = [TestOutcome(name="t::x", status=STATUS_PASSED)]

        await synthesize_stage(db_session, context)

        assert context.merge_readiness is not None
        assert context.merge_readiness.coverage_deduction == 10

    @pytest.mark.asyncio
    async def test_missing_run_id_raises(self, db_session: Session) -> None:
        context = _context(analysis_run_id=None)
        with pytest.raises(SynthesisError, match="no analysis run id"):
            await synthesize_stage(db_session, context)


class TestRegistration:
    def test_synthesize_stage_is_registered(self) -> None:
        assert synthesize_stage in runner.STAGES