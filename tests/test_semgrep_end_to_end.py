import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, SecurityFinding, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.orchestrator.runner import run_analysis_for_pull_request

DIFF_TEXT = r"""diff --git a/src/app.py b/src/app.py
new file mode 100644
--- /dev/null
+++ b/src/app.py
@@ -0,0 +1,2 @@
+import subprocess
+subprocess.call('ls')
diff --git a/logo.png b/logo.png
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
                        "title": "dangerous call",
                        "file": "src/app.py",
                        "line": 2,
                        "evidence": "subprocess.call('ls')",
                        "explanation": "dangerous subprocess usage",
                        "confidence": 1.0,
                        "rule_id": "python.lang.security.audit.dangerous-system-call",
                    }
                ]
            }
        )


def _mock_dependencies(
    monkeypatch: pytest.MonkeyPatch, diff_text: str = DIFF_TEXT
) -> None:
    async def fake_fetch_pr_diff(
        installation_id: int, owner: str, repo: str, pr_number: int
    ) -> str:
        return diff_text

    async def fake_fetch_pull_request(
        installation_id: int, owner: str, repo: str, pr_number: int
    ) -> dict:
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(
        installation_id: int, owner: str, repo: str, path: str, ref: str
    ) -> str:
        return "import subprocess\nsubprocess.call('ls')\n"

    def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None) -> str:
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

    async def fake_post_review_comment(installation_id, owner, repo, pr_number, body):
        return {"id": 1}

    monkeypatch.setattr(
        "quorum.orchestrator.stages.post_review_comment", fake_post_review_comment
    )



class TestSemgrepEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline_stores_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        _mock_dependencies(monkeypatch)

        run_id = await run_analysis_for_pull_request(pr.id, db=db_session)

        assert run_id is not None
        assert get_analysis_run(db_session, run_id).status == STATUS_COMPLETED

        stored = db_session.scalars(select(SecurityFinding)).all()
        assert len(stored) == 1
        finding = stored[0]
        assert finding.analysis_run_id == run_id
        assert finding.rule_id == "python.lang.security.audit.dangerous-system-call"
        assert finding.severity == "high"
        assert finding.file == "src/app.py"
        assert finding.line == 2
        assert finding.title == "dangerous call"
        assert finding.evidence == "subprocess.call('ls')"
        assert finding.confidence == 1.0

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
    async def test_binary_only_pr_stores_no_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        binary_only = (
            "diff --git a/logo.png b/logo.png\n"
            "index 1111111..2222222 100644\n"
            "Binary files a/logo.png and b/logo.png differ\n"
        )
        _mock_dependencies(monkeypatch, diff_text=binary_only)

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
                (row.rule_id, row.severity, row.file, row.line, row.title)
                for row in rows
            ]

        assert _signature(first) == _signature(second)