from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from quorum.api.schemas import (
    AnalysisRunOut,
    CoverageResultOut,
    PullRequestOut,
    PullRequestSummaryOut,
    RepositoryOut,
    ReviewDetailOut,
    ReviewSummaryOut,
    SecurityFindingOut,
    TestRunOut,
    UserOut,
)
from quorum.auth.sessions import get_session
from quorum.database.base import get_db
from quorum.database.models import AnalysisRun, PullRequest, Repository, User
from quorum.database.repository import (
    get_coverage_result_for_run,
    get_pull_request_for_user,
    get_repository_for_user,
    get_review_for_user,
    get_user_by_github_id,
    list_analysis_runs_for_pull_request,
    list_pull_requests_for_user,
    list_repositories_for_user,
    list_repository_pull_requests_for_user,
    list_reviews_for_user,
    list_security_findings_for_run,
    list_test_runs_for_run,
)
from quorum.github.repo_sync import sync_user_repositories

router = APIRouter(prefix="/api", tags=["api"])


def _current_user_id(db: Session, session: str | None) -> int:
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = get_user_by_github_id(db, session_data.get("github_id"))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user.id


@router.get("/me", response_model=UserOut)
def read_current_user(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UserOut:
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session(session)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = get_user_by_github_id(db, session_data.get("github_id"))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    return UserOut(
        github_id=user.github_id,
        username=user.username,
        avatar_url=user.avatar_url,
    )


@router.get("/repositories", response_model=list[RepositoryOut])
async def read_repositories(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[RepositoryOut]:
    user_id = _current_user_id(db, session)
    user = db.get(User, user_id)
    if user is not None:
        await sync_user_repositories(db, user)
    return [
        RepositoryOut.model_validate(repo)
        for repo in list_repositories_for_user(db, user_id)
    ]


def _pull_request_summary(pull_request: PullRequest) -> PullRequestSummaryOut:
    return PullRequestSummaryOut(
        id=pull_request.id,
        github_id=pull_request.github_id,
        number=pull_request.number,
        title=pull_request.title,
        author=pull_request.author,
        state=pull_request.state,
        repository_id=pull_request.repository_id,
        repository_full_name=(
            pull_request.repository.full_name
            if pull_request.repository is not None
            else None
        ),
    )


@router.get("/pull-requests", response_model=list[PullRequestSummaryOut])
def read_pull_requests(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[PullRequestSummaryOut]:
    user_id = _current_user_id(db, session)
    return [_pull_request_summary(pr) for pr in list_pull_requests_for_user(db, user_id)]


@router.get("/pull-requests/{pull_request_id}", response_model=PullRequestSummaryOut)
def read_pull_request(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> PullRequestSummaryOut:
    user_id = _current_user_id(db, session)
    pull_request = get_pull_request_for_user(db, pull_request_id, user_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return _pull_request_summary(pull_request)


@router.get("/repositories/{repository_id}", response_model=RepositoryOut)
def read_repository(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> RepositoryOut:
    user_id = _current_user_id(db, session)
    repository = get_repository_for_user(db, repository_id, user_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryOut.model_validate(repository)


@router.get(
    "/repositories/{repository_id}/pull-requests",
    response_model=list[PullRequestOut],
)
def read_repository_pull_requests(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[PullRequestOut]:
    user_id = _current_user_id(db, session)
    if get_repository_for_user(db, repository_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return [
        PullRequestOut.model_validate(pr)
        for pr in list_repository_pull_requests_for_user(db, repository_id, user_id)
    ]


def _review_summary(run: AnalysisRun) -> ReviewSummaryOut:
    pull_request = run.pull_request
    repository = pull_request.repository if pull_request is not None else None
    return ReviewSummaryOut(
        id=run.id,
        pull_request_id=run.pull_request_id,
        pr_number=pull_request.number if pull_request is not None else 0,
        pr_title=pull_request.title if pull_request is not None else "",
        pr_author=pull_request.author if pull_request is not None else "",
        pr_state=pull_request.state if pull_request is not None else "",
        repository_id=repository.id if repository is not None else 0,
        repository_full_name=(
            repository.full_name if repository is not None else ""
        ),
        status=run.status,
        merge_readiness_score=run.merge_readiness_score,
        started_at=run.started_at,
        completed_at=run.completed_at,
        finding_count=len(run.security_findings),
        test_count=len(run.test_runs),
    )


def _review_detail(run: AnalysisRun) -> ReviewDetailOut:
    summary = _review_summary(run)
    return ReviewDetailOut(
        **summary.model_dump(),
        findings=[
            SecurityFindingOut.model_validate(finding)
            for finding in run.security_findings
        ],
        tests=[TestRunOut.model_validate(test) for test in run.test_runs],
        coverage=(
            CoverageResultOut.model_validate(run.coverage_results[0])
            if run.coverage_results
            else None
        ),
    )


def _latest_analysis_run(
    db: Session, pull_request_id: int
) -> AnalysisRun | None:
    runs = list_analysis_runs_for_pull_request(db, pull_request_id)
    return runs[0] if runs else None


def _require_owned_pull_request(
    db: Session, pull_request_id: int, user_id: int
) -> None:
    if get_pull_request_for_user(db, pull_request_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Pull request not found")


@router.get(
    "/pull-requests/{pull_request_id}/analysis",
    response_model=list[AnalysisRunOut],
)
def read_pull_request_analysis(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[AnalysisRunOut]:
    user_id = _current_user_id(db, session)
    _require_owned_pull_request(db, pull_request_id, user_id)
    return [
        AnalysisRunOut.model_validate(run)
        for run in list_analysis_runs_for_pull_request(db, pull_request_id)
    ]


@router.get(
    "/pull-requests/{pull_request_id}/security",
    response_model=list[SecurityFindingOut],
)
def read_pull_request_security(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[SecurityFindingOut]:
    user_id = _current_user_id(db, session)
    _require_owned_pull_request(db, pull_request_id, user_id)
    run = _latest_analysis_run(db, pull_request_id)
    if run is None:
        return []
    return [
        SecurityFindingOut.model_validate(finding)
        for finding in list_security_findings_for_run(db, run.id)
    ]


@router.get(
    "/pull-requests/{pull_request_id}/tests",
    response_model=list[TestRunOut],
)
def read_pull_request_tests(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[TestRunOut]:
    user_id = _current_user_id(db, session)
    _require_owned_pull_request(db, pull_request_id, user_id)
    run = _latest_analysis_run(db, pull_request_id)
    if run is None:
        return []
    return [
        TestRunOut.model_validate(test)
        for test in list_test_runs_for_run(db, run.id)
    ]


@router.get(
    "/pull-requests/{pull_request_id}/coverage",
    response_model=CoverageResultOut | None,
)
def read_pull_request_coverage(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> CoverageResultOut | None:
    user_id = _current_user_id(db, session)
    _require_owned_pull_request(db, pull_request_id, user_id)
    run = _latest_analysis_run(db, pull_request_id)
    if run is None:
        return None
    coverage = get_coverage_result_for_run(db, run.id)
    if coverage is None:
        return None
    return CoverageResultOut.model_validate(coverage)


@router.get("/reviews", response_model=list[ReviewSummaryOut])
def read_reviews(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[ReviewSummaryOut]:
    user_id = _current_user_id(db, session)
    return [_review_summary(run) for run in list_reviews_for_user(db, user_id)]


@router.get("/reviews/{review_id}", response_model=ReviewDetailOut)
def read_review(
    review_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> ReviewDetailOut:
    user_id = _current_user_id(db, session)
    run = get_review_for_user(db, review_id, user_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return _review_detail(run)
