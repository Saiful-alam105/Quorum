import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import (
    AnalysisRun,
    PullRequest,
    Repository,
    SecurityFinding,
    User,
)
from quorum.database.repository import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    get_analysis_run,
)
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request


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


def _create_pr_with_user(db: Session) -> tuple[User, Repository, PullRequest]:
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
    return user, repo, pr


class TestEmptyPipeline:
    @pytest.mark.asyncio
    async def test_run_completes_with_no_results(
        self, db_session: Session
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        assert run_id is not None
        run = get_analysis_run(db_session, run_id)
        assert run is not None
        assert run.status == STATUS_COMPLETED
        assert run.started_at is not None
        assert run.completed_at is not None
        assert db_session.query(SecurityFinding).count() == 0
        assert db_session.query(AnalysisRun).count() == 1

    @pytest.mark.asyncio
    async def test_missing_pull_request_returns_none(self, db_session: Session) -> None:
        result = await run_analysis_for_pull_request(999999, db=db_session)
        assert result is None
        assert db_session.query(AnalysisRun).count() == 0


class TestStageExecution:
    @pytest.mark.asyncio
    async def test_stage_receives_populated_context(
        self, db_session: Session
    ) -> None:
        user, repo, pr = _create_pr_with_user(db_session)
        seen: list[AnalysisContext] = []

        async def capture_stage(session: Session, context: AnalysisContext) -> None:
            seen.append(context)

        run_id = await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=[capture_stage]
        )
        assert run_id is not None
        assert len(seen) == 1
        assert seen[0].pull_request_id == pr.id
        assert seen[0].repository_id == repo.id
        assert seen[0].owner == "octocat"
        assert seen[0].repo == "hello-world"
        assert seen[0].pr_number == 7
        assert seen[0].installation_id == 555

    @pytest.mark.asyncio
    async def test_stage_sees_in_progress_run(self, db_session: Session) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        seen_statuses: list[str] = []

        async def check_stage(session: Session, context: AnalysisContext) -> None:
            run = session.query(AnalysisRun).order_by(AnalysisRun.id.desc()).first()
            seen_statuses.append(run.status if run is not None else "none")

        await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=[check_stage]
        )
        assert seen_statuses == [STATUS_IN_PROGRESS]

    @pytest.mark.asyncio
    async def test_stage_runs_in_order(self, db_session: Session) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        order: list[str] = []

        async def stage_one(session: Session, context: AnalysisContext) -> None:
            order.append("one")

        async def stage_two(session: Session, context: AnalysisContext) -> None:
            order.append("two")

        await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=[stage_one, stage_two]
        )
        assert order == ["one", "two"]


class TestFailure:
    @pytest.mark.asyncio
    async def test_stage_failure_marks_run_failed(self, db_session: Session) -> None:
        _, _, pr = _create_pr_with_user(db_session)

        async def failing_stage(session: Session, context: AnalysisContext) -> None:
            raise RuntimeError("stage exploded")

        with pytest.raises(RuntimeError, match="stage exploded"):
            await run_analysis_for_pull_request(
                pr.id, db=db_session, stages=[failing_stage]
            )

        run = db_session.query(AnalysisRun).one()
        assert run.status == STATUS_FAILED
        assert run.started_at is not None
        assert run.completed_at is not None