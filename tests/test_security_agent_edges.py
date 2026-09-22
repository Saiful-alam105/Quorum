import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.security_agent import (
    SecurityAgent,
    SecurityAgentError,
    build_security_prompt,
)
from quorum.analysis.semgrep import SemgrepFinding
from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, SecurityFinding, User
from quorum.database.repository import (
    create_analysis_run,
    create_security_findings,
    replace_security_findings,
)
from quorum.llm.base import LLMError, LLMProvider
from quorum.orchestrator.runner import AnalysisContext
from quorum.orchestrator.stages import security_agent_stage


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


def _run(db: Session) -> int:
    repo = Repository(
        github_id=101, owner="octocat", name="hello-world",
        full_name="octocat/hello-world", is_private=False,
    )
    db.add(repo)
    db.commit()
    pr = PullRequest(
        github_id=301, repository_id=repo.id, number=7,
        title="t", author="octocat", state="open",
    )
    db.add(pr)
    db.commit()
    return create_analysis_run(db, pr.id).id


def _semgrep(**overrides) -> SemgrepFinding:
    entry = {
        "rule_id": "r1", "severity": "high", "file": "src/app.py",
        "line": 2, "message": "m", "evidence": "eval(x)", "confidence": 0.7,
    }
    entry.update(overrides)
    return SemgrepFinding(**entry)


class FakeProvider(LLMProvider):
    def __init__(self, result) -> None:
        self.result = result

    async def generate(self, prompt: str) -> str:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class TestReplaceAtomicity:
    def test_replace_clears_rows_when_empty(self, db_session: Session) -> None:
        run_id = _run(db_session)
        create_security_findings(
            db_session, run_id, [{"severity": "high", "title": "raw", "file": "f.py", "line": 1, "evidence": "e"}]
        )
        assert db_session.scalar(select(SecurityFinding).limit(1)) is not None
        assert replace_security_findings(db_session, run_id, []) == []
        assert db_session.scalar(select(SecurityFinding).limit(1)) is None

    def test_replace_inserts_new_rows(self, db_session: Session) -> None:
        run_id = _run(db_session)
        create_security_findings(
            db_session, run_id, [{"severity": "high", "title": "raw", "file": "f.py", "line": 1, "evidence": "e"}]
        )
        rows = replace_security_findings(
            db_session, run_id, [{"severity": "low", "title": "curated", "file": "f.py", "line": 1, "evidence": "e"}]
        )
        assert len(rows) == 1
        stored = db_session.scalars(
            select(SecurityFinding).where(SecurityFinding.analysis_run_id == run_id)
        ).all()
        assert len(stored) == 1
        assert stored[0].title == "curated"


class TestStageEdges:
    @pytest.mark.asyncio
    async def test_missing_run_id_raises(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        context = AnalysisContext(
            pull_request_id=1, repository_id=1, owner="o", repo="r", pr_number=1,
            installation_id=555, analysis_run_id=None, semgrep_findings=[_semgrep()],
        )
        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider",
            lambda role=None: FakeProvider("{}"),
        )
        with pytest.raises(SecurityAgentError, match="no analysis run id"):
            await security_agent_stage(db_session, context)


class TestAgentEdges:
    @pytest.mark.asyncio
    async def test_whitespace_output_raises(self) -> None:
        agent = SecurityAgent(FakeProvider("   \n  "))
        with pytest.raises(SecurityAgentError, match="invalid output"):
            await agent.review(None, [_semgrep()])

    @pytest.mark.asyncio
    async def test_missing_api_key_wraps(self) -> None:
        agent = SecurityAgent(FakeProvider(LLMError("OpenAI API key not configured")))
        with pytest.raises(SecurityAgentError, match="API key not configured"):
            await agent.review(None, [_semgrep()])

    @pytest.mark.asyncio
    async def test_empty_findings_skips_without_prompt(self) -> None:
        provider = FakeProvider(AssertionError("should not be called"))
        agent = SecurityAgent(provider)
        review = await agent.review(None, [])
        assert review.findings == []


class TestLargeFindings:
    def test_many_findings_produce_deterministic_prompt(self) -> None:
        findings = [_semgrep(rule_id=f"r{i}", line=i + 1) for i in range(50)]
        first = build_security_prompt(None, findings, "o", "r", 1)
        second = build_security_prompt(None, findings, "o", "r", 1)
        assert first == second
        assert first.count("rule:") == 50
        assert "r49" in first