import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.agents.security_agent import SecurityAgentError
from quorum.analysis.diff import ChangedFile
from quorum.analysis.semgrep import SemgrepFinding
from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository, SecurityFinding, User
from quorum.database.repository import (
    create_analysis_run,
    create_security_findings,
)
from quorum.llm.base import LLMError, LLMProvider
from quorum.orchestrator import runner
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
        changed_files=[ChangedFile(path="src/app.py", status="added")],
        semgrep_findings=[
            SemgrepFinding(
                rule_id="r1",
                severity="high",
                file="src/app.py",
                line=2,
                message="dangerous",
                evidence="subprocess.call('ls')",
                confidence=0.7,
            )
        ],
    )


class FakeProvider(LLMProvider):
    def __init__(self, result) -> None:
        self.result = result
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


_VALID_JSON = json.dumps(
    {
        "findings": [
            {
                "severity": "high",
                "title": "dangerous subprocess",
                "file": "src/app.py",
                "line": 2,
                "evidence": "subprocess.call('ls')",
                "explanation": "shell injection",
                "confidence": 0.9,
            }
        ]
    }
)


class TestSecurityAgentStage:
    @pytest.mark.asyncio
    async def test_stage_persists_and_replaces_findings(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        create_security_findings(
            db_session,
            run.id,
            [
                {
                    "rule_id": "raw-rule",
                    "severity": "high",
                    "title": "raw",
                    "file": "src/app.py",
                    "line": 2,
                    "evidence": "x",
                }
            ],
        )
        context = _context(run.id)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider",
            lambda role=None: FakeProvider(_VALID_JSON),
        )

        await security_agent_stage(db_session, context)

        assert len(context.security_findings) == 1
        stored = db_session.scalars(
            select(SecurityFinding).where(SecurityFinding.analysis_run_id == run.id)
        ).all()
        assert len(stored) == 1
        assert stored[0].title == "dangerous subprocess"
        assert stored[0].explanation == "shell injection"
        assert stored[0].rule_id == ""

    @pytest.mark.asyncio
    async def test_empty_semgrep_skips_llm(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        context.semgrep_findings = []
        called: list[str] = []

        def fake_factory(role=None):
            called.append("factory")
            return FakeProvider(_VALID_JSON)

        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider", fake_factory
        )

        await security_agent_stage(db_session, context)

        assert called == []
        assert context.security_findings == []
        assert db_session.scalar(select(SecurityFinding).limit(1)) is None

    @pytest.mark.asyncio
    async def test_llm_failure_raises_security_agent_error(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, pr = _create_pr_with_user(db_session)
        run = create_analysis_run(db_session, pr.id)
        context = _context(run.id)
        monkeypatch.setattr(
            "quorum.orchestrator.stages.create_llm_provider",
            lambda role=None: FakeProvider(LLMError("api down")),
        )

        with pytest.raises(SecurityAgentError, match="LLM call failed"):
            await security_agent_stage(db_session, context)


class TestRegistration:
    def test_security_agent_stage_is_registered(self) -> None:
        assert security_agent_stage in runner.STAGES