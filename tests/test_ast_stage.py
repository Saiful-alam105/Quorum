import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.analysis.diff import (
    LINE_ADDED,
    ChangedFile,
    DiffHunk,
    DiffLine,
)
from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.github.content_service import ContentFetchError
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request
from quorum.orchestrator.stages import extract_ast_stage, extract_diff_stage

SOURCE = """import os


def alpha(x):
    return x


def beta():
    return 1
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


def _context(db: Session, pr: PullRequest, repo: Repository) -> AnalysisContext:
    return AnalysisContext(
        pull_request_id=pr.id,
        repository_id=repo.id,
        owner="octocat",
        repo="hello-world",
        pr_number=7,
        installation_id=555,
    )


def _mock_fetch(monkeypatch: pytest.MonkeyPatch, content: str = SOURCE) -> None:
    async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
        return content

    monkeypatch.setattr(
        "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
    )
    monkeypatch.setattr(
        "quorum.orchestrator.stages.fetch_file_content", fake_fetch_file_content
    )


class TestExtractAstStage:
    @pytest.mark.asyncio
    async def test_populates_ast_files_with_modified_structures(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _context(db_session, pr, repo)
        total = len(SOURCE.splitlines())
        hunk = DiffHunk(
            old_start=0,
            old_count=0,
            new_start=1,
            new_count=total,
            lines=[
                DiffLine(kind=LINE_ADDED, old_line=None, new_line=i + 1, content="x")
                for i in range(total)
            ],
        )
        context.changed_files = [ChangedFile(path="app.py", status="added", hunks=[hunk])]
        _mock_fetch(monkeypatch)

        await extract_ast_stage(db_session, context)

        assert len(context.ast_files) == 1
        info = context.ast_files[0]
        assert info.path == "app.py"
        assert [f.name for f in info.functions] == ["alpha", "beta"]
        assert all(f.modified for f in info.functions)

    @pytest.mark.asyncio
    async def test_skips_non_python_files(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _context(db_session, pr, repo)
        context.changed_files = [
            ChangedFile(path="logo.png", status="added"),
            ChangedFile(path="README.md", status="modified"),
        ]
        called: list[str] = []

        async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
            called.append("pr")
            return {"head": {"sha": "abc"}}

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
        )

        await extract_ast_stage(db_session, context)

        assert called == []
        assert context.ast_files == []

    @pytest.mark.asyncio
    async def test_empty_changed_files_skips(self, db_session, monkeypatch) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _context(db_session, pr, repo)
        _mock_fetch(monkeypatch)

        await extract_ast_stage(db_session, context)

        assert context.ast_files == []

    @pytest.mark.asyncio
    async def test_missing_head_sha_raises(self, db_session, monkeypatch) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _context(db_session, pr, repo)
        context.changed_files = [ChangedFile(path="app.py", status="added")]

        async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
            return {"head": {}}

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
        )

        with pytest.raises(ContentFetchError, match="no head sha"):
            await extract_ast_stage(db_session, context)


class TestIntegration:
    @pytest.mark.asyncio
    async def test_pipeline_populates_ast(self, db_session, monkeypatch) -> None:
        _, _, pr = _create_pr_with_user(db_session)

        async def fake_fetch_pr_diff(installation_id, owner, repo, pr_number):
            return (
                "diff --git a/app.py b/app.py\n"
                "new file mode 100644\n"
                "--- /dev/null\n"
                "+++ b/app.py\n"
                "@@ -0,0 +1,5 @@\n"
                "+import os\n"
                "+\n"
                "+\n"
                "+def alpha(x):\n"
                "+    return x\n"
            )

        async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
            return {"head": {"sha": "abc123"}}

        async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
            return SOURCE

        def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None):
            return '{"results": [], "errors": []}'

        async def fake_llm_provider(prompt: str) -> str:
            return '{"findings": []}'

        seen: list[AnalysisContext] = []

        async def capture_stage(session, context):
            seen.append(context)

        monkeypatch.setattr("quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_file_content", fake_fetch_file_content
        )
        monkeypatch.setattr("quorum.orchestrator.stages.run_semgrep", fake_run_semgrep)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider",
            lambda role=None: _FakeLLM(),
        )

        run_id = await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=list(runner.STAGES) + [capture_stage]
        )

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        assert len(seen) == 1
        assert len(seen[0].ast_files) == 1
        assert seen[0].ast_files[0].functions[0].name == "alpha"
        assert seen[0].ast_files[0].functions[0].modified is True


class _FakeLLM:
    async def generate(self, prompt: str) -> str:
        return '{"findings": []}'


class TestRegistration:
    def test_extract_ast_stage_is_registered(self) -> None:
        assert extract_ast_stage in runner.STAGES