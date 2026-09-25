from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from quorum.database.models import (
    AnalysisRun,
    ChatMessage,
    CoverageResult,
    PullRequest,
    Repository,
    SecurityFinding,
    TestRun,
    User,
    utcnow,
)

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def upsert_user(
    db: Session,
    github_id: int | None,
    username: str | None,
    avatar_url: str | None = None,
    github_installation_id: int | None = None,
) -> User | None:
    if github_id is None:
        return None

    user = db.scalar(select(User).where(User.github_id == github_id))
    if user is None:
        user = User(github_id=github_id)
        db.add(user)

    if username is not None:
        user.username = username
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if github_installation_id is not None:
        user.github_installation_id = github_installation_id
    db.commit()
    return user


def revoke_installation(
    db: Session,
    installation_id: int | None,
    account_id: int | None = None,
) -> int:
    revoked = 0
    if installation_id is not None:
        for user in db.scalars(
            select(User).where(User.github_installation_id == installation_id)
        ):
            user.github_installation_id = None
            revoked += 1
    if account_id is not None:
        for user in db.scalars(select(User).where(User.github_id == account_id)):
            if user.github_installation_id is not None:
                user.github_installation_id = None
                revoked += 1
    db.commit()
    return revoked


def upsert_repository(
    db: Session, data: dict, user_id: int | None = None
) -> Repository | None:
    github_id = data.get("id")
    if github_id is None:
        return None

    repository = db.scalar(
        select(Repository).where(Repository.github_id == github_id)
    )
    if repository is None:
        repository = Repository(github_id=github_id)
        db.add(repository)

    owner = data.get("owner") or {}
    repository.owner = owner.get("login", "")
    repository.name = data.get("name", "")
    repository.full_name = data.get("full_name", "")
    repository.is_private = bool(data.get("private", False))
    if user_id is not None:
        repository.user_id = user_id
    db.commit()
    return repository


def upsert_pull_request(
    db: Session, data: dict, repository: Repository
) -> PullRequest | None:
    github_id = data.get("id")
    if github_id is None:
        return None

    pull_request = db.scalar(
        select(PullRequest).where(PullRequest.github_id == github_id)
    )
    if pull_request is None:
        pull_request = PullRequest(github_id=github_id, repository_id=repository.id)
        db.add(pull_request)

    author = data.get("user") or {}
    pull_request.repository_id = repository.id
    pull_request.number = data.get("number", 0)
    pull_request.title = data.get("title", "")
    pull_request.author = author.get("login", "")
    pull_request.state = data.get("state", "")
    pull_request.updated_at = utcnow()
    db.commit()
    return pull_request


def list_repositories(db: Session) -> list[Repository]:
    return list(db.scalars(select(Repository).order_by(Repository.full_name)))


def get_repository_by_id(db: Session, repository_id: int) -> Repository | None:
    return db.get(Repository, repository_id)


def list_pull_requests_by_repository(
    db: Session, repository_id: int
) -> list[PullRequest]:
    return list(
        db.scalars(
            select(PullRequest)
            .where(PullRequest.repository_id == repository_id)
            .order_by(PullRequest.number.desc())
        )
    )


def list_pull_requests(db: Session) -> list[PullRequest]:
    return list(db.scalars(select(PullRequest).order_by(PullRequest.id.desc())))


def get_repository_by_full_name(db: Session, full_name: str) -> Repository | None:
    return db.scalar(
        select(Repository).where(Repository.full_name == full_name)
    )


def get_pull_request(db: Session, github_id: int) -> PullRequest | None:
    return db.scalar(
        select(PullRequest).where(PullRequest.github_id == github_id)
    )


def get_pull_request_by_id(db: Session, pull_request_id: int) -> PullRequest | None:
    return db.get(PullRequest, pull_request_id)


def get_user_by_github_id(db: Session, github_id: int | None) -> User | None:
    if github_id is None:
        return None
    return db.scalar(select(User).where(User.github_id == github_id))


def get_user_by_installation(db: Session, installation_id: int | None) -> User | None:
    if installation_id is None:
        return None
    return db.scalar(
        select(User).where(User.github_installation_id == installation_id)
    )


def list_repositories_for_user(db: Session, user_id: int) -> list[Repository]:
    return list(
        db.scalars(
            select(Repository)
            .options(
                selectinload(Repository.pull_requests).selectinload(
                    PullRequest.analysis_runs
                )
            )
            .where(Repository.user_id == user_id)
            .order_by(Repository.full_name)
        )
    )


def detach_repositories_not_in(
    db: Session, user_id: int, authorized_full_names: set[str]
) -> int:
    detached = 0
    for repository in db.scalars(
        select(Repository).where(Repository.user_id == user_id)
    ):
        if repository.full_name not in authorized_full_names:
            repository.user_id = None
            detached += 1
    db.commit()
    return detached


def get_repository_for_user(
    db: Session, repository_id: int, user_id: int
) -> Repository | None:
    return db.scalar(
        select(Repository)
        .options(
            selectinload(Repository.pull_requests).selectinload(
                PullRequest.analysis_runs
            )
        )
        .where(Repository.id == repository_id, Repository.user_id == user_id)
    )


def list_pull_requests_for_user(db: Session, user_id: int) -> list[PullRequest]:
    return list(
        db.scalars(
            select(PullRequest)
            .options(
                selectinload(PullRequest.repository),
                selectinload(PullRequest.analysis_runs).selectinload(
                    AnalysisRun.security_findings
                ),
                selectinload(PullRequest.analysis_runs).selectinload(
                    AnalysisRun.test_runs
                ),
            )
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.user_id == user_id)
            .order_by(PullRequest.id.desc())
        )
    )


def list_repository_pull_requests_for_user(
    db: Session, repository_id: int, user_id: int
) -> list[PullRequest]:
    return list(
        db.scalars(
            select(PullRequest)
            .options(
                selectinload(PullRequest.repository),
                selectinload(PullRequest.analysis_runs).selectinload(
                    AnalysisRun.security_findings
                ),
                selectinload(PullRequest.analysis_runs).selectinload(
                    AnalysisRun.test_runs
                ),
            )
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(
                PullRequest.repository_id == repository_id,
                Repository.user_id == user_id,
            )
            .order_by(PullRequest.number.desc())
        )
    )


def get_pull_request_for_user(
    db: Session, pull_request_id: int, user_id: int
) -> PullRequest | None:
    return db.scalar(
        select(PullRequest)
        .options(
            selectinload(PullRequest.repository),
            selectinload(PullRequest.analysis_runs).selectinload(
                AnalysisRun.security_findings
            ),
            selectinload(PullRequest.analysis_runs).selectinload(
                AnalysisRun.test_runs
            ),
        )
        .join(Repository, PullRequest.repository_id == Repository.id)
        .where(PullRequest.id == pull_request_id, Repository.user_id == user_id)
    )


def create_analysis_run(
    db: Session, pull_request_id: int, status: str = STATUS_PENDING
) -> AnalysisRun:
    analysis_run = AnalysisRun(pull_request_id=pull_request_id, status=status)
    db.add(analysis_run)
    db.commit()
    return analysis_run


def get_analysis_run(db: Session, analysis_run_id: int) -> AnalysisRun | None:
    return db.get(AnalysisRun, analysis_run_id)


def list_analysis_runs_for_pull_request(
    db: Session, pull_request_id: int
) -> list[AnalysisRun]:
    return list(
        db.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.pull_request_id == pull_request_id)
            .order_by(AnalysisRun.id.desc())
        )
    )


def mark_analysis_run_in_progress(
    db: Session, analysis_run_id: int
) -> AnalysisRun | None:
    analysis_run = db.get(AnalysisRun, analysis_run_id)
    if analysis_run is None:
        return None
    analysis_run.status = STATUS_IN_PROGRESS
    analysis_run.started_at = utcnow()
    db.commit()
    return analysis_run


def complete_analysis_run(
    db: Session, analysis_run_id: int
) -> AnalysisRun | None:
    analysis_run = db.get(AnalysisRun, analysis_run_id)
    if analysis_run is None:
        return None
    analysis_run.status = STATUS_COMPLETED
    analysis_run.completed_at = utcnow()
    db.commit()
    return analysis_run


def fail_analysis_run(db: Session, analysis_run_id: int) -> AnalysisRun | None:
    analysis_run = db.get(AnalysisRun, analysis_run_id)
    if analysis_run is None:
        return None
    analysis_run.status = STATUS_FAILED
    analysis_run.completed_at = utcnow()
    db.commit()
    return analysis_run


def _security_finding_from_dict(
    analysis_run_id: int, finding: dict
) -> SecurityFinding:
    return SecurityFinding(
        analysis_run_id=analysis_run_id,
        severity=finding.get("severity", ""),
        title=finding.get("title", ""),
        file=finding.get("file", ""),
        line=finding.get("line"),
        evidence=finding.get("evidence", ""),
        explanation=finding.get("explanation"),
        confidence=finding.get("confidence"),
        rule_id=finding.get("rule_id"),
    )


def create_security_findings(
    db: Session, analysis_run_id: int, findings: list[dict]
) -> list[SecurityFinding]:
    """Persist security findings for an analysis run and return the rows."""
    if not findings:
        return []
    rows = [_security_finding_from_dict(analysis_run_id, f) for f in findings]
    db.add_all(rows)
    db.commit()
    return rows


def create_test_runs(
    db: Session, analysis_run_id: int, outcomes: list[dict]
) -> list[TestRun]:
    """Persist sandbox test outcomes for an analysis run and return the rows."""
    if not outcomes:
        return []
    rows = [
        TestRun(
            analysis_run_id=analysis_run_id,
            test_name=outcome.get("test_name", ""),
            status=outcome.get("status", ""),
            duration=outcome.get("duration"),
            stdout=outcome.get("stdout"),
            stderr=outcome.get("stderr"),
            failure_reason=outcome.get("failure_reason"),
        )
        for outcome in outcomes
    ]
    db.add_all(rows)
    db.commit()
    return rows


def create_coverage_result(
    db: Session,
    analysis_run_id: int,
    coverage_before: float,
    coverage_after: float,
    coverage_delta: float,
) -> CoverageResult:
    """Persist a coverage result for an analysis run and return the row."""
    row = CoverageResult(
        analysis_run_id=analysis_run_id,
        coverage_before=coverage_before,
        coverage_after=coverage_after,
        coverage_delta=coverage_delta,
    )
    db.add(row)
    db.commit()
    return row


def set_merge_readiness_score(
    db: Session, analysis_run_id: int, score: int
) -> AnalysisRun | None:
    """Store the Merge Readiness Score on an analysis run."""
    analysis_run = db.get(AnalysisRun, analysis_run_id)
    if analysis_run is None:
        return None
    analysis_run.merge_readiness_score = score
    db.commit()
    return analysis_run


def replace_security_findings(
    db: Session, analysis_run_id: int, findings: list[dict]
) -> list[SecurityFinding]:
    """Replace all security findings for a run with the curated set (atomic)."""
    db.execute(
        delete(SecurityFinding).where(
            SecurityFinding.analysis_run_id == analysis_run_id
        )
    )
    if not findings:
        db.commit()
        return []
    rows = [_security_finding_from_dict(analysis_run_id, f) for f in findings]
    db.add_all(rows)
    db.commit()
    return rows


def list_security_findings_for_run(
    db: Session, analysis_run_id: int
) -> list[SecurityFinding]:
    return list(
        db.scalars(
            select(SecurityFinding)
            .where(SecurityFinding.analysis_run_id == analysis_run_id)
            .order_by(SecurityFinding.id)
        )
    )


def list_test_runs_for_run(db: Session, analysis_run_id: int) -> list[TestRun]:
    return list(
        db.scalars(
            select(TestRun)
            .where(TestRun.analysis_run_id == analysis_run_id)
            .order_by(TestRun.id)
        )
    )


def get_coverage_result_for_run(
    db: Session, analysis_run_id: int
) -> CoverageResult | None:
    return db.scalar(
        select(CoverageResult)
        .where(CoverageResult.analysis_run_id == analysis_run_id)
        .order_by(CoverageResult.id.desc())
    )


def list_reviews_for_user(db: Session, user_id: int) -> list[AnalysisRun]:
    """List all analysis runs (reviews) for the repositories owned by a user."""
    return list(
        db.scalars(
            select(AnalysisRun)
            .options(
                selectinload(AnalysisRun.security_findings),
                selectinload(AnalysisRun.test_runs),
                selectinload(AnalysisRun.coverage_results),
                selectinload(AnalysisRun.pull_request).selectinload(
                    PullRequest.repository
                ),
            )
            .join(PullRequest, AnalysisRun.pull_request_id == PullRequest.id)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.user_id == user_id)
            .order_by(AnalysisRun.id.desc())
        )
    )


def get_review_for_user(
    db: Session, review_id: int, user_id: int
) -> AnalysisRun | None:
    """Return an analysis run scoped to a user's repositories, or None."""
    return db.scalar(
        select(AnalysisRun)
        .options(
            selectinload(AnalysisRun.security_findings),
            selectinload(AnalysisRun.test_runs),
            selectinload(AnalysisRun.coverage_results),
            selectinload(AnalysisRun.pull_request).selectinload(
                PullRequest.repository
            ),
        )
        .join(PullRequest, AnalysisRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .where(AnalysisRun.id == review_id, Repository.user_id == user_id)
    )


def list_recent_findings_for_user(
    db: Session, user_id: int, limit: int = 10
) -> list[SecurityFinding]:
    """List the latest-run security findings for a user's repositories.

    Only findings from each pull request's most recent analysis run are
    returned, so re-analysed pull requests do not duplicate the feed.
    """
    latest_run_ids = (
        select(func.max(AnalysisRun.id))
        .join(PullRequest, AnalysisRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .where(Repository.user_id == user_id)
        .group_by(PullRequest.id)
    )
    return list(
        db.scalars(
            select(SecurityFinding)
            .options(
                selectinload(SecurityFinding.analysis_run)
                .selectinload(AnalysisRun.pull_request)
                .selectinload(PullRequest.repository),
            )
            .join(AnalysisRun, SecurityFinding.analysis_run_id == AnalysisRun.id)
            .where(SecurityFinding.analysis_run_id.in_(latest_run_ids))
            .order_by(SecurityFinding.id.desc())
            .limit(limit)
        )
    )


def list_chat_messages_for_review(
    db: Session, analysis_run_id: int
) -> list[ChatMessage]:
    """Return the chat history for a review, oldest first."""
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.analysis_run_id == analysis_run_id)
            .order_by(ChatMessage.id)
        )
    )


def create_chat_message(
    db: Session,
    analysis_run_id: int,
    user_id: int | None,
    role: str,
    message: str,
) -> ChatMessage:
    """Persist a chat message for a review and return the row."""
    row = ChatMessage(
        analysis_run_id=analysis_run_id,
        user_id=user_id,
        role=role,
        message=message,
    )
    db.add(row)
    db.commit()
    return row