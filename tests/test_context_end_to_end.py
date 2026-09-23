import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request
from quorum.orchestrator.stages import build_context_stage, extract_diff_stage

SMALL_DIFF_TEXT = r"""diff --git a/calculator.py b/calculator.py
index 1234567..89abcde 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""


def _large_diff(
    file_count: int = 30, lines_per_file: int = 100, line_length: int = 30
) -> str:
    parts: list[str] = []
    for index in range(file_count):
        path = f"src/module_{index:02d}/file_{index:02d}.py"
        parts.append(f"diff --git a/{path} b/{path}")
        parts.append("new file mode 100644")
        parts.append("--- /dev/null")
        parts.append(f"+++ b/{path}")
        parts.append(f"@@ -0,0 +1,{lines_per_file} @@")
        for line_number in range(1, lines_per_file + 1):
            parts.append(f"+line_{line_number} " + "x" * line_length)
    return "\n".join(parts)


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


def _fake_fetch(diff_text: str):
    async def fake(
        installation_id: int, owner: str, repo: str, pr_number: int
    ) -> str:
        return diff_text

    return fake


def _fake_fetch_pull_request():
    async def fake(
        installation_id: int, owner: str, repo: str, pr_number: int
    ) -> dict:
        return {"head": {"sha": "abc123"}}

    return fake


def _fake_fetch_file_content():
    async def fake(
        installation_id: int, owner: str, repo: str, path: str, ref: str
    ) -> str:
        return "def f():\n    return 1\n"

    return fake


def _fake_run_semgrep(raw: str):
    def fake(scan_dir, ruleset=None, timeout_seconds=None) -> str:
        return raw

    return fake


async def _run_pipeline(
    db: Session,
    pr_id: int,
    diff_text: str,
    monkeypatch: pytest.MonkeyPatch,
) -> AnalysisContext:
    monkeypatch.setattr(
        "quorum.orchestrator.stages.fetch_pr_diff", _fake_fetch(diff_text)
    )
    seen: list = []

    async def capture_stage(session: Session, context: AnalysisContext) -> None:
        seen.append(context.prepared_context)

    run_id = await run_analysis_for_pull_request(
        pr_id,
        db=db,
        stages=[extract_diff_stage, build_context_stage, capture_stage],
    )
    assert run_id is not None
    assert get_analysis_run(db, run_id).status == STATUS_COMPLETED
    assert len(seen) == 1
    return seen[0]


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_registered_pipeline_completes_for_small_pr(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pr_diff", _fake_fetch(SMALL_DIFF_TEXT)
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request",
            _fake_fetch_pull_request(),
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_file_content",
            _fake_fetch_file_content(),
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.run_semgrep", _fake_run_semgrep("{}")
        )

        async def fake_post_review_comment(installation_id, owner, repo, pr_number, body):
            return {"id": 1}

        monkeypatch.setattr(
            "quorum.orchestrator.stages.post_review_comment", fake_post_review_comment
        )

        run_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED

    @pytest.mark.asyncio
    async def test_small_pr_fits_completely(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        context = await _run_pipeline(db_session, pr.id, SMALL_DIFF_TEXT, monkeypatch)
        assert context is not None
        assert context.truncated is False
        assert context.truncated_files == []
        assert [file.path for file in context.files] == ["calculator.py"]
        assert context.total_estimated_tokens <= context.budget_estimated_tokens

    @pytest.mark.asyncio
    async def test_oversized_pr_is_bounded_and_truncated(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        context = await _run_pipeline(db_session, pr.id, _large_diff(), monkeypatch)
        assert context is not None
        assert context.truncated is True
        assert context.truncated_files
        assert len(context.files) > 0
        assert context.total_estimated_tokens <= context.budget_estimated_tokens

    @pytest.mark.asyncio
    async def test_oversized_pr_keeps_valid_metadata(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        context = await _run_pipeline(db_session, pr.id, _large_diff(), monkeypatch)
        top = context.files[0]
        assert top.hunks
        first_line = top.hunks[0].lines[0]
        assert first_line.kind == "add"
        assert first_line.new_line == 1
        assert first_line.old_line is None

    @pytest.mark.asyncio
    async def test_oversized_pr_is_deterministic(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        first = await _run_pipeline(db_session, pr.id, _large_diff(), monkeypatch)
        second = await _run_pipeline(db_session, pr.id, _large_diff(), monkeypatch)
        assert first.render_text() == second.render_text()
        assert first.truncated_files == second.truncated_files
        assert first.total_estimated_tokens == second.total_estimated_tokens