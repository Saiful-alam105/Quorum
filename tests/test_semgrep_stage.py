import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
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
from quorum.database.repository import STATUS_COMPLETED, STATUS_FAILED, get_analysis_run
from quorum.github.content_service import ContentFetchError
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request
from quorum.orchestrator.stages import (
    build_context_stage,
    extract_diff_stage,
    semgrep_stage,
)

DIFF_TEXT = r"""diff --git a/src/app.py b/src/app.py
new file mode 100644
--- /dev/null
+++ b/src/app.py
@@ -0,0 +1,2 @@
+import subprocess
+subprocess.call('ls')
"""

BINARY_ONLY_DIFF = r"""diff --git a/logo.png b/logo.png
index 1111111..2222222 100644
Binary files a/logo.png and b/logo.png differ
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


def _build_context(
    db: Session, pr: PullRequest, repo: Repository
) -> AnalysisContext:
    return AnalysisContext(
        pull_request_id=pr.id,
        repository_id=repo.id,
        owner="octocat",
        repo="hello-world",
        pr_number=7,
        installation_id=555,
        analysis_run_id=1,
    )


def _fake_semgrep_output(scan_dir: str) -> str:
    return json.dumps(
        {
            "results": [
                {
                    "check_id": "python.lang.security.audit.dangerous-system-call",
                    "path": str(Path(scan_dir) / "src" / "app.py"),
                    "start": {"line": 2},
                    "extra": {
                        "severity": "ERROR",
                        "message": "dangerous call",
                        "lines": "subprocess.call('ls')",
                        "metadata": {"confidence": "HIGH"},
                    },
                }
            ],
            "errors": [],
        }
    )


class TestSemgrepStage:
    @pytest.mark.asyncio
    async def test_populates_and_persists_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _build_context(db_session, pr, repo)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return DIFF_TEXT

        async def fake_fetch_pull_request(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> dict:
            return {"head": {"sha": "abc123"}}

        async def fake_fetch_file_content(
            installation_id: int, owner: str, repo: str, path: str, ref: str
        ) -> str:
            return "import subprocess\nsubprocess.call('ls')\n"

        def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None) -> str:
            return _fake_semgrep_output(scan_dir)

        monkeypatch.setattr("quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_file_content", fake_fetch_file_content
        )
        monkeypatch.setattr("quorum.orchestrator.stages.run_semgrep", fake_run_semgrep)

        await extract_diff_stage(db_session, context)
        await build_context_stage(db_session, context)
        await semgrep_stage(db_session, context)

        assert len(context.semgrep_findings) == 1
        finding = context.semgrep_findings[0]
        assert finding.rule_id == "python.lang.security.audit.dangerous-system-call"
        assert finding.severity == "high"
        assert finding.file == "src/app.py"
        assert finding.line == 2

        stored = db_session.scalar(select(SecurityFinding).limit(1))
        assert stored is not None
        assert stored.analysis_run_id == context.analysis_run_id
        assert stored.rule_id == finding.rule_id
        assert stored.title == "dangerous call"
        assert stored.file == "src/app.py"
        assert stored.line == 2

    @pytest.mark.asyncio
    async def test_empty_diff_no_findings(self, db_session, monkeypatch) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _build_context(db_session, pr, repo)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return ""

        monkeypatch.setattr("quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff)

        await extract_diff_stage(db_session, context)
        await build_context_stage(db_session, context)
        await semgrep_stage(db_session, context)

        assert context.semgrep_findings == []
        assert db_session.scalar(select(SecurityFinding).limit(1)) is None

    @pytest.mark.asyncio
    async def test_binary_only_pr_skips_scan(self, db_session, monkeypatch) -> None:
        _, repo, pr = _create_pr_with_user(db_session)
        context = _build_context(db_session, pr, repo)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return BINARY_ONLY_DIFF

        monkeypatch.setattr("quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff)
        called: list[str] = []

        async def fake_fetch_pull_request(*args, **kwargs) -> dict:
            called.append("pr")
            return {"head": {"sha": "abc"}}

        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
        )

        await extract_diff_stage(db_session, context)
        await semgrep_stage(db_session, context)

        assert called == []
        assert context.semgrep_findings == []


class TestIntegration:
    @pytest.mark.asyncio
    async def test_runner_completes_with_stored_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        seen: list[AnalysisContext] = []

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return DIFF_TEXT

        async def fake_fetch_pull_request(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> dict:
            return {"head": {"sha": "abc123"}}

        async def fake_fetch_file_content(
            installation_id: int, owner: str, repo: str, path: str, ref: str
        ) -> str:
            return "import subprocess\nsubprocess.call('ls')\n"

        def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None) -> str:
            return _fake_semgrep_output(scan_dir)

        async def capture_stage(session: Session, context: AnalysisContext) -> None:
            seen.append(context)

        monkeypatch.setattr("quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", fake_fetch_pull_request
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_file_content", fake_fetch_file_content
        )
        monkeypatch.setattr("quorum.orchestrator.stages.run_semgrep", fake_run_semgrep)

        run_id = await run_analysis_for_pull_request(
            pr.id,
            db=db_session,
            stages=[extract_diff_stage, build_context_stage, semgrep_stage, capture_stage],
        )

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        assert len(seen) == 1
        assert seen[0].analysis_run_id == run_id
        assert len(seen[0].semgrep_findings) == 1
        assert db_session.scalar(select(SecurityFinding).limit(1)) is not None

    @pytest.mark.asyncio
    async def test_fetch_failure_marks_run_failed(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)

        async def fake_fetch_pr_diff(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> str:
            return DIFF_TEXT

        async def failing_fetch_pull_request(
            installation_id: int, owner: str, repo: str, pr_number: int
        ) -> dict:
            raise ContentFetchError("github down")

        monkeypatch.setattr("quorum.orchestrator.stages.fetch_pr_diff", fake_fetch_pr_diff)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.fetch_pull_request", failing_fetch_pull_request
        )

        with pytest.raises(ContentFetchError, match="github down"):
            await run_analysis_for_pull_request(
                pr.id,
                db=db_session,
                stages=[extract_diff_stage, build_context_stage, semgrep_stage],
            )

        run = db_session.query(AnalysisRun).one()
        assert run.status == STATUS_FAILED


class TestRegistration:
    def test_semgrep_stage_is_registered(self) -> None:
        assert semgrep_stage in runner.STAGES