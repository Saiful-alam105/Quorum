import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.test_runner import STATUS_FAILED, STATUS_PASSED, TestExecution, TestOutcome
from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, User
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
                {"tests": [{"name": "test_alpha.py", "code": "def test_alpha():\n    assert True\n"}]}
            )
        return json.dumps(
            {
                "findings": [
                    {
                        "severity": "high",
                        "title": "dangerous",
                        "file": "app.py",
                        "line": 2,
                        "evidence": "return x + 1",
                        "explanation": "high risk",
                        "confidence": 0.9,
                    }
                ]
            }
        )


def _mock_dependencies(
    monkeypatch: pytest.MonkeyPatch, diff_text: str = DIFF_TEXT
) -> list[str]:
    posted: list[str] = []

    async def fake_fetch_pr_diff(installation_id, owner, repo, pr_number):
        return diff_text

    async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
        return GOOD_SOURCE

    def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None):
        return json.dumps(
            {
                "results": [
                    {
                        "check_id": "r1",
                        "path": str(Path(scan_dir) / "app.py"),
                        "start": {"line": 2},
                        "extra": {"severity": "ERROR", "message": "m", "lines": "x"},
                    }
                ],
                "errors": [],
            }
        )

    async def fake_build_workspace(changed_files, fetch_content, head_sha, workspace_dir):
        return Path(workspace_dir)

    def fake_write_test(workspace_dir, path, content):
        return Path(workspace_dir) / path

    covs = [0.0, 80.0]

    def fake_measure_coverage(workspace_dir, test_paths=None, config=None):
        return covs.pop(0) if covs else 0.0

    def fake_run_tests(workspace_dir, test_paths=None, config=None):
        return TestExecution(
            outcomes=[
                TestOutcome(name="test_alpha.py::t1", status=STATUS_PASSED),
                TestOutcome(name="test_alpha.py::t2", status=STATUS_FAILED),
            ],
            return_code=1,
            duration_seconds=1.0,
        )

    async def fake_post_review_comment(installation_id, owner, repo, pr_number, body):
        posted.append(body)

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
    monkeypatch.setattr(
        "quorum.orchestrator.stages.post_review_comment", fake_post_review_comment
    )
    return posted


class TestSynthesisCommentEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline_scores_and_posts(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        posted = _mock_dependencies(monkeypatch)

        seen: list[AnalysisContext] = []

        async def capture_stage(session, context):
            seen.append(context)

        run_id = await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=list(runner.STAGES) + [capture_stage]
        )

        run = get_analysis_run(db_session, run_id)
        assert run.status == STATUS_COMPLETED
        assert run.merge_readiness_score == 75  # -20 high, -5 one failed test, 0 coverage(80)

        context = seen[0]
        assert context.merge_readiness is not None
        assert context.merge_readiness.recommendation == "Approve with minor concerns"

        assert len(posted) == 1
        body = posted[0]
        assert "## Quorum Review" in body
        assert "75/100" in body
        assert "1 High, 0 Medium, 0 Low" in body
        assert "Generated tests: 2" in body
        assert "Passed: 1" in body
        assert "Failed: 1" in body
        assert "0% → 80%" in body
        assert "Approve with minor concerns" in body

    @pytest.mark.asyncio
    async def test_empty_pr_still_scores_and_posts(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)
        posted = _mock_dependencies(monkeypatch, diff_text="")

        run_id = await run_analysis_for_pull_request(pr.id, db=db_session)

        run = get_analysis_run(db_session, run_id)
        assert run.status == STATUS_COMPLETED
        assert run.merge_readiness_score == 80  # no tests (-10), no coverage (-10)
        assert len(posted) == 1
        body = posted[0]
        assert "None" in body
        assert "Generated tests: 0" in body
        assert "Not measured" in body

    @pytest.mark.asyncio
    async def test_pipeline_is_deterministic(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)

        _mock_dependencies(monkeypatch)
        first_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        first = get_analysis_run(db_session, first_id).merge_readiness_score

        _mock_dependencies(monkeypatch)
        second_id = await run_analysis_for_pull_request(pr.id, db=db_session)
        second = get_analysis_run(db_session, second_id).merge_readiness_score

        assert first == second