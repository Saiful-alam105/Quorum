import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.test_runner import STATUS_FAILED, STATUS_PASSED, TestExecution, TestOutcome
from quorum.agents.test_writer import TestWriterError
from quorum.analysis.ast_parser import AstFileInfo, FunctionInfo
from quorum.analysis.diff import ChangedFile
from quorum.database.base import Base
from quorum.database.models import (
    AnalysisRun,
    CoverageResult,
    PullRequest,
    Repository,
    TestRun,
    User,
)
from quorum.database.repository import create_analysis_run
from quorum.llm.base import LLMError, LLMProvider
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext
from quorum.orchestrator.stages import generate_tests_stage


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


def _context(analysis_run_id: int) -> AnalysisContext:
    return AnalysisContext(
        pull_request_id=1,
        repository_id=1,
        owner="octocat",
        repo="hello-world",
        pr_number=7,
        installation_id=555,
        analysis_run_id=analysis_run_id,
        changed_files=[ChangedFile(path="app.py", status="modified")],
        ast_files=[
            AstFileInfo(
                path="app.py",
                functions=[
                    FunctionInfo(
                        name="alpha",
                        kind="function",
                        arguments=["x"],
                        source="def alpha(x):\n    return x + 1",
                        modified=True,
                    )
                ],
            )
        ],
    )


_VALID_TESTS = json.dumps(
    {"tests": [{"name": "test_alpha.py", "code": "def test_alpha():\n    assert True\n"}]}
)


class FakeProvider(LLMProvider):
    def __init__(self, result) -> None:
        self.result = result

    async def generate(self, prompt: str) -> str:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _mock_dependencies(monkeypatch: pytest.MonkeyPatch, coverage_values=None) -> None:
    async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
        return "def alpha(x):\n    return x + 1\n"

    async def fake_build_workspace(changed_files, fetch_content, head_sha, workspace_dir):
        return Path(workspace_dir)

    def fake_write_test(workspace_dir, path, content):
        return Path(workspace_dir) / path

    covs = list(coverage_values) if coverage_values else [0.0, 80.0]

    def fake_measure_coverage(workspace_dir, test_paths=None, config=None):
        return covs.pop(0) if covs else 0.0

    def fake_run_tests(workspace_dir, test_paths=None, config=None):
        return TestExecution(
            outcomes=[
                TestOutcome(name="test_alpha.py::test_alpha", status=STATUS_PASSED),
                TestOutcome(name="test_alpha.py::test_beta", status=STATUS_FAILED),
            ],
            return_code=1,
            duration_seconds=2.0,
        )

    monkeypatch.setattr(
        "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
    )
    monkeypatch.setattr(
        "quorum.orchestrator.stages.fetch_file_content", fake_fetch_file_content
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


class TestTestWriterStage:
    @pytest.mark.asyncio
    async def test_stage_generates_runs_and_persists(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        _mock_dependencies(monkeypatch)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider",
            lambda role=None: FakeProvider(_VALID_TESTS),
        )

        await generate_tests_stage(db_session, context)

        assert len(context.generated_tests) == 1
        assert [o.status for o in context.test_results] == [STATUS_PASSED, STATUS_FAILED]
        assert context.coverage is not None

        test_runs = db_session.scalars(
            select(TestRun).where(TestRun.analysis_run_id == run.id)
        ).all()
        assert len(test_runs) == 2
        coverage = db_session.scalar(
            select(CoverageResult).where(CoverageResult.analysis_run_id == run.id)
        )
        assert coverage is not None
        assert coverage.coverage_before == 0.0
        assert coverage.coverage_after == 80.0
        assert coverage.coverage_delta == 80.0

    @pytest.mark.asyncio
    async def test_no_modified_functions_skips(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        context.ast_files = []
        called: list[str] = []

        def fake_factory(role=None):
            called.append("factory")
            return FakeProvider(_VALID_TESTS)

        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider", fake_factory
        )

        await generate_tests_stage(db_session, context)

        assert called == []
        assert context.generated_tests == []
        assert context.test_results == []
        assert context.coverage is None
        assert db_session.scalar(select(TestRun).limit(1)) is None

    @pytest.mark.asyncio
    async def test_llm_failure_raises(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider",
            lambda role=None: FakeProvider(LLMError("api down")),
        )

        with pytest.raises(TestWriterError, match="LLM call failed"):
            await generate_tests_stage(db_session, context)


class TestRegistration:
    def test_test_writer_stage_is_registered(self) -> None:
        assert generate_tests_stage in runner.STAGES