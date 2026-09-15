import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import AnalysisRun, PullRequest, Repository, User
from quorum.database.repository import STATUS_COMPLETED, STATUS_FAILED, get_analysis_run
from quorum.github.diff_service import DiffFetchError
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request
from quorum.orchestrator.stages import extract_diff_stage

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


class TestExtractDiffStage:
    @pytest.mark.asyncio
    async def test_parses_diff_into_context(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, repo, pr = _create_pr_with_user(db_session)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return DIFF_TEXT

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff
        )

        context = _build_context(db_session, pr, repo)
        await extract_diff_stage(db_session, context)

        assert len(context.changed_files) == 1
        changed = context.changed_files[0]
        assert changed.path == "calculator.py"
        assert changed.status == "modified"
        assert changed.added_lines == 1
        assert changed.removed_lines == 0

    @pytest.mark.asyncio
    async def test_empty_diff_yields_no_changed_files(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, repo, pr = _create_pr_with_user(db_session)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return ""

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff
        )

        context = _build_context(db_session, pr, repo)
        await extract_diff_stage(db_session, context)

        assert context.changed_files == []

    @pytest.mark.asyncio
    async def test_missing_installation_id_raises(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _build_context(db_session, pr, repo)
        context.installation_id = None

        with pytest.raises(DiffFetchError, match="no GitHub installation id"):
            await extract_diff_stage(db_session, context)


class TestIntegration:
    @pytest.mark.asyncio
    async def test_runner_completes_with_extracted_diff(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return DIFF_TEXT

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff
        )

        seen: list[list] = []

        async def capture_stage(session: Session, context: AnalysisContext) -> None:
            seen.append(context.changed_files)

        run_id = await run_analysis_for_pull_request(
            pr.id,
            db=db_session,
            stages=[extract_diff_stage, capture_stage],
        )

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        assert len(seen) == 1
        assert seen[0][0].path == "calculator.py"
        assert seen[0][0].added_lines == 1

    @pytest.mark.asyncio
    async def test_runner_marks_run_failed_on_fetch_error(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)

        async def failing_fetch(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            raise DiffFetchError("github down")

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pr_diff", failing_fetch
        )

        with pytest.raises(DiffFetchError, match="github down"):
            await run_analysis_for_pull_request(
                pr.id, db=db_session, stages=[extract_diff_stage]
            )

        run = db_session.query(AnalysisRun).one()
        assert run.status == STATUS_FAILED


class TestRegistration:
    def test_diff_stage_is_registered(self) -> None:
        assert extract_diff_stage in runner.STAGES