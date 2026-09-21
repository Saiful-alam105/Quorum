import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import AnalysisRun, PullRequest, Repository, SecurityFinding
from quorum.database.repository import create_analysis_run, create_security_findings


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _enable_foreign_keys)
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _enable_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _create_pr(db: Session) -> PullRequest:
    repo = Repository(
        github_id=101,
        owner="octocat",
        name="hello-world",
        full_name="octocat/hello-world",
        is_private=False,
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


def _create_run(db: Session) -> AnalysisRun:
    pr = _create_pr(db)
    return create_analysis_run(db, pr.id)


class TestCreateSecurityFindings:
    def test_stores_all_fields(self, db_session: Session) -> None:
        run = _create_run(db_session)
        rows = create_security_findings(
            db_session,
            run.id,
            [
                {
                    "rule_id": "python.lang.security.audit.eval-detected",
                    "severity": "medium",
                    "title": "Detected use of eval()",
                    "file": "src/app.py",
                    "line": 4,
                    "evidence": "return eval(x)",
                    "explanation": None,
                    "confidence": 0.4,
                }
            ],
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.analysis_run_id == run.id
        assert row.rule_id == "python.lang.security.audit.eval-detected"
        assert row.severity == "medium"
        assert row.title == "Detected use of eval()"
        assert row.file == "src/app.py"
        assert row.line == 4
        assert row.evidence == "return eval(x)"
        assert row.confidence == 0.4

    def test_allows_nullable_fields(self, db_session: Session) -> None:
        run = _create_run(db_session)
        rows = create_security_findings(
            db_session,
            run.id,
            [
                {
                    "severity": "high",
                    "title": "t",
                    "file": "f.py",
                    "line": 1,
                    "evidence": "e",
                }
            ],
        )
        assert len(rows) == 1
        assert rows[0].rule_id is None
        assert rows[0].confidence is None
        assert rows[0].explanation is None

    def test_empty_list_returns_empty(self, db_session: Session) -> None:
        run = _create_run(db_session)
        assert create_security_findings(db_session, run.id, []) == []
        assert db_session.scalar(select(SecurityFinding).limit(1)) is None

    def test_invalid_run_id_raises(self, db_session: Session) -> None:
        with pytest.raises(IntegrityError):
            create_security_findings(
                db_session,
                999999,
                [
                    {
                        "severity": "low",
                        "title": "t",
                        "file": "f.py",
                        "line": 1,
                        "evidence": "e",
                    }
                ],
            )

    def test_findings_linked_to_run_relationship(self, db_session: Session) -> None:
        run = _create_run(db_session)
        create_security_findings(
            db_session,
            run.id,
            [
                {
                    "rule_id": "r1",
                    "severity": "high",
                    "title": "a",
                    "file": "f1.py",
                    "line": 1,
                    "evidence": "e",
                },
                {
                    "rule_id": "r2",
                    "severity": "low",
                    "title": "b",
                    "file": "f2.py",
                    "line": 2,
                    "evidence": "e",
                },
            ],
        )
        stored = db_session.scalars(
            select(SecurityFinding).where(SecurityFinding.analysis_run_id == run.id)
        ).all()
        assert len(stored) == 2
        assert run.security_findings == stored