import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.config import settings
from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request
from quorum.orchestrator.stages import build_context_stage, extract_diff_stage

DIFF_TEXT = r"""diff --git a/calculator.py b/calculator.py
index 1234567..89abcde 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,6 +1,7 @@
 def add(a, b):
     return a + b
 
+
 def subtract(a, b):
     return a - b
 
"""


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


def _build_context(db: Session, pr: PullRequest, repo: Repository) -> AnalysisContext:
    return AnalysisContext(
        pull_request_id=pr.id,
        repository_id=repo.id,
        owner="octocat",
        repo="hello-world",
        pr_number=7,
        installation_id=555,
    )


def _monkeypatch_fetch(db: Session, monkeypatch: pytest.MonkeyPatch, diff_text: str) -> AnalysisContext:
    _, repo, pr = _create_pr_with_user(db)

    async def fake_fetch_pr_diff(
        installation_id: int, owner: str, repo: str, pr_number: int
    ) -> str:
        return diff_text

    monkeypatch.setattr(
        "quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff
    )
    return _build_context(db, pr, repo)


class TestBuildContextStage:
    @pytest.mark.asyncio
    async def test_populates_prepared_context(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        context = _monkeypatch_fetch(db_session, monkeypatch, DIFF_TEXT)
        await extract_diff_stage(db_session, context)
        await build_context_stage(db_session, context)

        assert context.prepared_context is not None
        assert len(context.prepared_context.files) == 1
        assert context.prepared_context.files[0].path == "calculator.py"
        assert context.prepared_context.truncated is False
        assert context.prepared_context.budget_estimated_tokens == 8000

    @pytest.mark.asyncio
    async def test_empty_diff_yields_empty_context(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        context = _monkeypatch_fetch(db_session, monkeypatch, "")
        await extract_diff_stage(db_session, context)
        await build_context_stage(db_session, context)

        assert context.prepared_context is not None
        assert context.prepared_context.files == []
        assert context.prepared_context.truncated is False

    @pytest.mark.asyncio
    async def test_context_bounded_when_over_budget(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "context_budget_estimated_tokens", 1)
        context = _monkeypatch_fetch(db_session, monkeypatch, DIFF_TEXT)
        await extract_diff_stage(db_session, context)
        await build_context_stage(db_session, context)

        assert context.prepared_context is not None
        assert context.prepared_context.truncated is True
        assert context.prepared_context.total_estimated_tokens <= 1
        assert context.prepared_context.budget_estimated_tokens == 1


class TestIntegration:
    @pytest.mark.asyncio
    async def test_runner_builds_context_after_diff(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        context = _monkeypatch_fetch(db_session, monkeypatch, DIFF_TEXT)
        seen: list = []

        async def capture_stage(session: Session, context: AnalysisContext) -> None:
            seen.append(context.prepared_context)

        run_id = await run_analysis_for_pull_request(
            context.pull_request_id,
            db=db_session,
            stages=[extract_diff_stage, build_context_stage, capture_stage],
        )

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        assert len(seen) == 1
        assert seen[0] is not None
        assert len(seen[0].files) == 1


class TestRegistration:
    def test_stages_are_registered(self) -> None:
        assert extract_diff_stage in runner.STAGES
        assert build_context_stage in runner.STAGES