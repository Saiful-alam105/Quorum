import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, SecurityFinding, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request

DIFF_TEXT = r"""diff --git a/src/app.py b/src/app.py
new file mode 100644
--- /dev/null
+++ b/src/app.py
@@ -0,0 +1,2 @@
+import subprocess
+subprocess.call('ls')
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


class _FakeSecurityLLM:
    async def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "findings": [
                    {
                        "severity": "high",
                        "title": "curated A",
                        "file": "src/app.py",
                        "line": 1,
                        "evidence": "import subprocess",
                        "explanation": "explained A",
                        "confidence": 0.9,
                    },
                    {
                        "severity": "high",
                        "title": "ghost finding",
                        "file": "src/app.py",
                        "line": 99,
                        "evidence": "???",
                        "explanation": "should be filtered",
                        "confidence": 0.5,
                    },
                ]
            }
        )


def _mock_dependencies(monkeypatch: pytest.MonkeyPatch, diff_text: str = DIFF_TEXT) -> None:
    async def fake_fetch_pr_diff(installation_id, owner, repo, pr_number):
        return diff_text

    async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
        return "import subprocess\nsubprocess.call('ls')\n"

    def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None):
        return json.dumps(
            {
                "results": [
                    {
                        "check_id": "python.lang.security.audit.dangerous-system-call",
                        "path": str(Path(scan_dir) / "src" / "app.py"),
                        "start": {"line": 1},
                        "extra": {"severity": "ERROR", "message": "m1", "lines": "import subprocess"},
                    },
                    {
                        "check_id": "python.lang.security.audit.dangerous-system-call",
                        "path": str(Path(scan_dir) / "src" / "app.py"),
                        "start": {"line": 2},
                        "extra": {"severity": "WARNING", "message": "m2", "lines": "subprocess.call('ls')"},
                    },
                ],
                "errors": [],
            }
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
        lambda role=None: _FakeSecurityLLM(),
    )


class TestSecurityAgentEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline_stores_curated_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        _mock_dependencies(monkeypatch)

        seen: list[AnalysisContext] = []

        async def capture_stage(session: Session, context: AnalysisContext) -> None:
            seen.append(context)

        run_id = await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=list(runner.STAGES) + [capture_stage]
        )

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        assert len(seen) == 1
        assert len(seen[0].security_findings) == 1

        stored = db_session.scalars(
            select(SecurityFinding).where(SecurityFinding.analysis_run_id == run_id)
        ).all()
        assert len(stored) == 1
        finding = stored[0]
        assert finding.title == "curated A"
        assert finding.file == "src/app.py"
        assert finding.line == 1
        assert finding.explanation == "explained A"
        assert finding.confidence == 0.9

    @pytest.mark.asyncio
    async def test_empty_pr_stores_no_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        _mock_dependencies(monkeypatch, diff_text="")

        run_id = await run_analysis_for_pull_request(pr.id, db=db_session)

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED
        assert db_session.scalar(select(SecurityFinding).limit(1)) is None

    @pytest.mark.asyncio
    async def test_pipeline_is_deterministic(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)

        _mock_dependencies(monkeypatch)
        first_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        first = db_session.scalars(
            select(SecurityFinding).where(SecurityFinding.analysis_run_id == first_id)
        ).all()

        _mock_dependencies(monkeypatch)
        second_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        second = db_session.scalars(
            select(SecurityFinding).where(SecurityFinding.analysis_run_id == second_id)
        ).all()

        def _signature(rows):
            return [
                (row.severity, row.title, row.file, row.line, row.explanation)
                for row in rows
            ]

        assert _signature(first) == _signature(second)