import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from quorum.database.base import Base
from quorum.database.models import PullRequest, Repository
from quorum.database.repository import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    complete_analysis_run,
    create_analysis_run,
    fail_analysis_run,
    get_analysis_run,
    list_analysis_runs_for_pull_request,
    mark_analysis_run_in_progress,
)


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


class TestCreateAnalysisRun:
    def test_create_defaults_to_pending(self, db_session: Session) -> None:
        pr = _create_pr(db_session)
        run = create_analysis_run(db_session, pr.id)
        assert run.id is not None
        assert run.pull_request_id == pr.id
        assert run.status == STATUS_PENDING
        assert run.started_at is None
        assert run.completed_at is None

    def test_create_with_custom_status(self, db_session: Session) -> None:
        pr = _create_pr(db_session)
        run = create_analysis_run(db_session, pr.id, status=STATUS_IN_PROGRESS)
        assert run.status == STATUS_IN_PROGRESS


class TestGetAnalysisRun:
    def test_get_existing(self, db_session: Session) -> None:
        pr = _create_pr(db_session)
        run = create_analysis_run(db_session, pr.id)
        fetched = get_analysis_run(db_session, run.id)
        assert fetched is not None
        assert fetched.id == run.id

    def test_get_missing_returns_none(self, db_session: Session) -> None:
        assert get_analysis_run(db_session, 999999) is None


class TestAnalysisRunLifecycle:
    def test_pending_to_in_progress_sets_started_at(
        self, db_session: Session
    ) -> None:
        pr = _create_pr(db_session)
        run = create_analysis_run(db_session, pr.id)
        updated = mark_analysis_run_in_progress(db_session, run.id)
        assert updated is not None
        assert updated.status == STATUS_IN_PROGRESS
        assert updated.started_at is not None
        assert updated.completed_at is None

    def test_in_progress_to_completed_sets_completed_at(
        self, db_session: Session
    ) -> None:
        pr = _create_pr(db_session)
        run = create_analysis_run(db_session, pr.id)
        mark_analysis_run_in_progress(db_session, run.id)
        updated = complete_analysis_run(db_session, run.id)
        assert updated is not None
        assert updated.status == STATUS_COMPLETED
        assert updated.started_at is not None
        assert updated.completed_at is not None

    def test_failed_sets_completed_at(self, db_session: Session) -> None:
        pr = _create_pr(db_session)
        run = create_analysis_run(db_session, pr.id)
        updated = fail_analysis_run(db_session, run.id)
        assert updated is not None
        assert updated.status == STATUS_FAILED
        assert updated.completed_at is not None

    def test_transition_missing_run_returns_none(self, db_session: Session) -> None:
        assert mark_analysis_run_in_progress(db_session, 999999) is None
        assert complete_analysis_run(db_session, 999999) is None
        assert fail_analysis_run(db_session, 999999) is None


class TestListAnalysisRunsForPullRequest:
    def test_lists_runs_newest_first(self, db_session: Session) -> None:
        pr = _create_pr(db_session)
        run1 = create_analysis_run(db_session, pr.id)
        run2 = create_analysis_run(db_session, pr.id)
        run3 = create_analysis_run(db_session, pr.id)
        runs = list_analysis_runs_for_pull_request(db_session, pr.id)
        assert [r.id for r in runs] == [run3.id, run2.id, run1.id]

    def test_empty_when_no_runs(self, db_session: Session) -> None:
        pr = _create_pr(db_session)
        assert list_analysis_runs_for_pull_request(db_session, pr.id) == []

    def test_only_returns_that_prs_runs(self, db_session: Session) -> None:
        pr1 = _create_pr(db_session)
        repo2 = Repository(
            github_id=102,
            owner="octocat",
            name="other",
            full_name="octocat/other",
            is_private=False,
        )
        db_session.add(repo2)
        db_session.commit()
        pr2 = PullRequest(
            github_id=302,
            repository_id=repo2.id,
            number=8,
            title="Other PR",
            author="octocat",
            state="open",
        )
        db_session.add(pr2)
        db_session.commit()
        create_analysis_run(db_session, pr1.id)
        create_analysis_run(db_session, pr2.id)
        runs = list_analysis_runs_for_pull_request(db_session, pr1.id)
        assert len(runs) == 1
        assert runs[0].pull_request_id == pr1.id