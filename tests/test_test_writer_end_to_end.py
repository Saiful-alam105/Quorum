import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.test_runner import STATUS_FAILED, STATUS_PASSED, TestExecution, TestOutcome
from quorum.database.base import Base
from quorum.database.models import CoverageResult, PullRequest, Repository, TestRun, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request

DIFF_TEXT = r"""diff --git a/app.py b/app.py
new file mode 100644
--- /dev/null
+++ b/app.py
@@ -0,0 +1,2 @@
+def alpha(x):
+    return x + 1
"""

GOOD_SOURCE = "def alpha(x):\n    return x + 1\n"


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


class _FakeLLM:
    def __init__(self, role: str | None = None) -> None:
        self.role = role

    async def generate(self, prompt: str) -> str:
        if self.role == "test":
            return json.dumps(
                {
                    "tests": [
                        {"name": "test_alpha.py", "code": "def test_alpha():\n    assert True\n"},
                        {"name": "../evil.py", "code": "def test_evil():\n    assert True\n"},
                    ]
                }
            )
        return '{"findings": []}'


def _mock_dependencies(monkeypatch: pytest.MonkeyPatch, timed_out: bool = False) -> None:
    async def fake_fetch_pr_diff(installation_id, owner, repo, pr_number):
        return DIFF_TEXT

    async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
        return GOOD_SOURCE

    def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None):
        return '{"results": [], "errors": []}'

    async def fake_build_workspace(changed_files, fetch_content, head_sha, workspace_dir):
        return Path(workspace_dir)

    def fake_write_test(workspace_dir, path, content):
        if path == "../evil.py" or ".." in Path(path).parts:
            raise ValueError(f"unsafe generated test path: {path}")
        return Path(workspace_dir) / path

    covs = [0.0, 80.0]

    def fake_measure_coverage(workspace_dir, test_paths=None, config=None):
        return covs.pop(0) if covs else 0.0

    def fake_run_tests(workspace_dir, test_paths=None, config=None):
        return TestExecution(
            outcomes=[
                TestOutcome(name="test_alpha.py::test_alpha", status=STATUS_PASSED)
            ],
            return_code=0,
            duration_seconds=1.0,
            timed_out=timed_out,
        )

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
        lambda role=None: _FakeLLM(role),
    )
    monkeypatch.setattr(
        "quorum.orchestrator.stages.build_sandbox_workspace", fake_build_workspace
    )
    monkeypatch.setattr(
        "quorum.orchestrator.stages.write_generated_test", fake_write_test
    )
    monkeypatch.setattr(
        "quorum.orchestrator.stages.measure_coverage", fake_measure_coverage
    )
    monkeypatch.setattr(
        "quorum.orchestrator.stages.run_tests_in_sandbox", fake_run_tests
    )


class TestTestWriterEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline_stores_tests_and_coverage(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        _mock_dependencies(monkeypatch)

        seen: list[AnalysisContext] = []

        async def capture_stage(session, context):
            seen.append(context)

        run_id = await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=list(runner.STAGES) + [capture_stage]
        )

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        context = seen[0]
        assert [t.name for t in context.generated_tests] == ["test_alpha.py", "../evil.py"]

        test_runs = db_session.scalars(
            select(TestRun).where(TestRun.analysis_run_id == run_id)
        ).all()
        assert len(test_runs) == 1
        assert test_runs[0].test_name == "test_alpha.py::test_alpha"
        assert test_runs[0].status == STATUS_PASSED

        coverage = db_session.scalar(
            select(CoverageResult).where(CoverageResult.analysis_run_id == run_id)
        )
        assert coverage is not None
        assert coverage.coverage_after == 80.0
        assert coverage.coverage_delta == 80.0

    @pytest.mark.asyncio
    async def test_timeout_records_failure(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        _mock_dependencies(monkeypatch, timed_out=True)

        run_id = await run_analysis_for_pull_request(pr.id, db=db_session)

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        test_runs = db_session.scalars(
            select(TestRun).where(TestRun.analysis_run_id == run_id)
        ).all()
        statuses = {t.status for t in test_runs}
        assert STATUS_FAILED in statuses
        assert any("timed out" in t.test_name for t in test_runs)

    @pytest.mark.asyncio
    async def test_pipeline_is_deterministic(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)

        _mock_dependencies(monkeypatch)
        first_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        first = db_session.scalars(
            select(TestRun).where(TestRun.analysis_run_id == first_id)
        ).all()

        _mock_dependencies(monkeypatch)
        second_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        second = db_session.scalars(
            select(TestRun).where(TestRun.analysis_run_id == second_id)
        ).all()

        def _sig(rows):
            return [(r.test_name, r.status) for r in rows]

        assert _sig(first) == _sig(second)