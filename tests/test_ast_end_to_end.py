import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, User
from quorum.database.repository import STATUS_COMPLETED, get_analysis_run
from quorum.orchestrator import runner
from quorum.orchestrator.runner import AnalysisContext, run_analysis_for_pull_request

DIFF_TEXT = r"""diff --git a/good.py b/good.py
new file mode 100644
--- /dev/null
+++ b/good.py
@@ -0,0 +1,2 @@
+def alpha(x):
+    return x
diff --git a/broken.py b/broken.py
new file mode 100644
--- /dev/null
+++ b/broken.py
@@ -0,0 +1,1 @@
+def broken(:
diff --git a/README.md b/README.md
new file mode 100644
--- /dev/null
+++ b/README.md
@@ -0,0 +1,1 @@
+# title
"""

GOOD_SOURCE = """def alpha(x):
    return x
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


CONTENTS = {
    "good.py": GOOD_SOURCE,
    "broken.py": "def broken(:\n",
    "README.md": "# title\n",
}


def _mock_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch_pr_diff(installation_id, owner, repo, pr_number):
        return DIFF_TEXT

    async def fake_fetch_pull_request(installation_id, owner, repo, pr_number):
        return {"head": {"sha": "abc123"}}

    async def fake_fetch_file_content(installation_id, owner, repo, path, ref):
        return CONTENTS.get(path, "")

    def fake_run_semgrep(scan_dir, ruleset=None, timeout_seconds=None):
        return '{"results": [], "errors": []}'

    async def fake_generate(prompt: str) -> str:
        return '{"findings": []}'

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
        lambda role=None: _FakeLLM(fake_generate),
    )


class _FakeLLM:
    def __init__(self, generate) -> None:
        self._generate = generate

    async def generate(self, prompt: str) -> str:
        return await self._generate(prompt)


def _signature(context: AnalysisContext):
    return [
        (info.path, [(f.name, f.modified) for f in info.functions])
        for info in context.ast_files
    ]


class TestAstEndToEnd:
    @pytest.mark.asyncio
    async def test_pipeline_extracts_ast_and_skips_unparseable(
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
        assert len(seen) == 1
        ast_files = seen[0].ast_files
        assert [info.path for info in ast_files] == ["good.py", "broken.py"]
        good = next(i for i in ast_files if i.path == "good.py")
        broken = next(i for i in ast_files if i.path == "broken.py")
        assert [f.name for f in good.functions] == ["alpha"]
        assert good.functions[0].modified is True
        assert broken.functions == []

    @pytest.mark.asyncio
    async def test_pipeline_is_deterministic(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pr = _create_pr_with_user(db_session)

        _mock_dependencies(monkeypatch)
        first: list[AnalysisContext] = []

        async def capture_first(session, context):
            first.append(context)

        await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=list(runner.STAGES) + [capture_first]
        )

        _mock_dependencies(monkeypatch)
        second: list[AnalysisContext] = []

        async def capture_second(session, context):
            second.append(context)

        await run_analysis_for_pull_request(
            pr.id, db=db_session, stages=list(runner.STAGES) + [capture_second]
        )

        assert _signature(first[0]) == _signature(second[0])