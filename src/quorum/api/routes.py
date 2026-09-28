from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Query
import httpx
from sqlalchemy.orm import Session

from quorum.api.schemas import (
    AnalysisRunOut,
    ChatMessageOut,
    ChatPostRequest,
    ChatPostResponse,
    ConnectUrlOut,
    CoverageResultOut,
    CreatePullRequestRequest,
    DiscoveredRepositoryOut,
    FindingOut,
    PullRequestActionOut,
    PullRequestActionRequest,
    PullRequestSummaryOut,
    RepositoryOut,
    ReviewDetailOut,
    ReviewSummaryOut,
    SecurityFindingOut,
    TestRunOut,
    UnconnectOut,
    UserOut,
)
from quorum.auth.sessions import get_session
from quorum.agents.synthesis import recommendation_for
from quorum.chat.service import answer_question
from quorum.config import settings
from quorum.database.base import get_db
from quorum.database.models import (
    AnalysisRun,
    PullRequest,
    Repository,
    SecurityFinding,
    User,
    utcnow,
)
from quorum.database.repository import (
    create_chat_message,
    exclude_repository,
    get_coverage_result_for_run,
    get_pull_request_for_user,
    get_repository_for_user,
    get_review_for_user,
    get_user_by_github_id,
    list_analysis_runs_for_pull_request,
    list_chat_messages_for_review,
    list_pull_requests_for_user,
    list_recent_findings_for_user,
    list_repositories_for_user,
    list_repository_pull_requests_for_user,
    list_reviews_for_user,
    list_security_findings_for_run,
    list_test_runs_for_run,
    upsert_pull_request,
)
from quorum.github.api import (
    close_pull_request,
    create_pr_comment,
    create_pull_request,
    get_pull_request as github_get_pull_request,
    get_repositories,
    list_branches,
    merge_pull_request,
)
from quorum.github.app_auth import get_installation_token
from quorum.github.repo_sync import (
    maybe_sync_user_repositories,
    sync_user_repositories,
)
from quorum.llm.base import LLMError
from quorum.orchestrator.runner import run_analysis_for_pull_request

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
        created_at=user.created_at,
        github_authorized=user.github_installation_id is not None,
    )


@router.get("/repositories", response_model=list[RepositoryOut])
async def read_repositories(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[RepositoryOut]:
    user_id = _current_user_id(db, session)
    user = db.get(User, user_id)
    if user is not None:
        await maybe_sync_user_repositories(db, user)
    return [
        _repository_out(repo)
        for repo in list_repositories_for_user(db, user_id)
    ]


def _repository_out(repository: Repository) -> RepositoryOut:
    pull_requests = repository.pull_requests
    runs = [
        run
        for pull_request in pull_requests
        for run in pull_request.analysis_runs
    ]
    latest_status = max(runs, key=lambda run: run.id).status if runs else None
    return RepositoryOut(
        id=repository.id,
        github_id=repository.github_id,
        owner=repository.owner,
        name=repository.name,
        full_name=repository.full_name,
        is_private=repository.is_private,
        pull_request_count=len(pull_requests),
        open_pull_request_count=sum(
            1 for pull_request in pull_requests if pull_request.state == "open"
        ),
        latest_analysis_status=latest_status,
    )


def _pull_request_summary(pull_request: PullRequest) -> PullRequestSummaryOut:
    latest = _latest_analysis_run_of(pull_request)
    findings = latest.security_findings if latest is not None else []
    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = (finding.severity or "").lower() or "info"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return PullRequestSummaryOut(
        id=pull_request.id,
        github_id=pull_request.github_id,
        number=pull_request.number,
        title=pull_request.title,
        author=pull_request.author,
        state=pull_request.state,
        head_ref=pull_request.head_ref,
        base_ref=pull_request.base_ref,
        repository_id=pull_request.repository_id,
        repository_full_name=(
            pull_request.repository.full_name
            if pull_request.repository is not None
            else None
        ),
        updated_at=pull_request.updated_at,
        latest_analysis_status=latest.status if latest is not None else None,
        merge_readiness_score=(
            latest.merge_readiness_score if latest is not None else None
        ),
        finding_count=len(findings),
        critical_count=severity_counts.get("critical", 0),
        high_count=severity_counts.get("high", 0),
        medium_count=severity_counts.get("medium", 0),
        low_count=severity_counts.get("low", 0),
        info_count=severity_counts.get("info", 0),
        test_count=len(latest.test_runs) if latest is not None else 0,
    )


def _latest_analysis_run_of(pull_request: PullRequest) -> AnalysisRun | None:
    if not pull_request.analysis_runs:
        return None
    return max(pull_request.analysis_runs, key=lambda run: run.id)


@router.get("/pull-requests", response_model=list[PullRequestSummaryOut])
def read_pull_requests(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[PullRequestSummaryOut]:
    user_id = _current_user_id(db, session)
    return [_pull_request_summary(pr) for pr in list_pull_requests_for_user(db, user_id)]


PR_STATE_STALE_AFTER_SECONDS = 300


def _as_aware(dt) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=utcnow().tzinfo)
    return dt


async def _reconcile_pull_request_state(
    db: Session, pull_request: PullRequest, user_id: int
) -> None:
    """Refresh a PR's state from GitHub when the local copy is stale.

    Webhooks can be missed (tunnel restarts, backend downtime), so the detail
    view reconciles itself when the local record is old. This makes PRs that
    were closed or merged on GitHub appear correctly without a manual refresh.
    """
    if pull_request.updated_at is None:
        return
    age = (utcnow() - _as_aware(pull_request.updated_at)).total_seconds()
    if age < PR_STATE_STALE_AFTER_SECONDS:
        return
    repository = pull_request.repository
    try:
        token = await _pull_request_installation_token(db, pull_request, user_id)
    except HTTPException:
        return
    try:
        data = await github_get_pull_request(
            token, repository.owner, repository.name, pull_request.number
        )
        upsert_pull_request(db, data, repository)
    except Exception:
        pass


@router.get("/pull-requests/{pull_request_id}", response_model=PullRequestSummaryOut)
async def read_pull_request(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> PullRequestSummaryOut:
    user_id = _current_user_id(db, session)
    pull_request = get_pull_request_for_user(db, pull_request_id, user_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    await _reconcile_pull_request_state(db, pull_request, user_id)
    pull_request = get_pull_request_for_user(db, pull_request_id, user_id) or pull_request
    return _pull_request_summary(pull_request)


async def _pull_request_installation_token(
    db: Session, pull_request: PullRequest, user_id: int
) -> str:
    user = db.get(User, user_id)
    installation_id = user.github_installation_id if user is not None else None
    if not installation_id:
        raise HTTPException(
            status_code=400,
            detail="GitHub App is not installed for this repository",
        )
    try:
        auth = await get_installation_token(
            settings.github_app_id,
            settings.github_app_private_key_path,
            installation_id,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Could not authenticate with GitHub",
        )
    token = auth.get("token")
    if not token:
        raise HTTPException(
            status_code=502,
            detail="Could not authenticate with GitHub",
        )
    return token


@router.post(
    "/pull-requests/{pull_request_id}/merge",
    response_model=PullRequestActionOut,
)
async def merge_pull_request_endpoint(
    pull_request_id: int,
    body: PullRequestActionRequest,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> PullRequestActionOut:
    user_id = _current_user_id(db, session)
    pull_request = get_pull_request_for_user(db, pull_request_id, user_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    repository = pull_request.repository
    token = await _pull_request_installation_token(db, pull_request, user_id)

    try:
        result = await merge_pull_request(
            token,
            repository.owner,
            repository.name,
            pull_request.number,
            commit_title=pull_request.title,
            commit_message=body.comment.strip() if body.comment else None,
            merge_method="merge",
        )
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        try:
            detail = exc.response.json().get("message", detail)
        except Exception:
            pass
        raise HTTPException(
            status_code=409,
            detail=f"Could not merge the pull request: {detail}",
        )

    merged = bool(result.get("merged"))
    pull_request.state = "merged" if merged else pull_request.state
    db.commit()

    comment_posted = False
    if body.comment and body.comment.strip() and merged:
        try:
            await create_pr_comment(
                token,
                repository.owner,
                repository.name,
                pull_request.number,
                body.comment.strip(),
            )
            comment_posted = True
        except Exception:
            comment_posted = False

    return PullRequestActionOut(
        status=pull_request.state,
        message=result.get("message"),
        comment_posted=comment_posted,
        pull_request=_pull_request_summary(pull_request),
    )


@router.post(
    "/pull-requests/{pull_request_id}/close",
    response_model=PullRequestActionOut,
)
async def close_pull_request_endpoint(
    pull_request_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> PullRequestActionOut:
    user_id = _current_user_id(db, session)
    pull_request = get_pull_request_for_user(db, pull_request_id, user_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail="Pull request not found")
    repository = pull_request.repository
    token = await _pull_request_installation_token(db, pull_request, user_id)

    try:
        await close_pull_request(
            token,
            repository.owner,
            repository.name,
            pull_request.number,
        )
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        try:
            detail = exc.response.json().get("message", detail)
        except Exception:
            pass
        raise HTTPException(
            status_code=409,
            detail=f"Could not close the pull request: {detail}",
        )

    pull_request.state = "closed"
    db.commit()
    return PullRequestActionOut(
        status=pull_request.state,
        message=None,
        comment_posted=False,
        pull_request=_pull_request_summary(pull_request),
    )


@router.get("/repositories/discover", response_model=list[DiscoveredRepositoryOut])
async def discover_repositories(
    force: bool = Query(default=False),
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[DiscoveredRepositoryOut]:
    """List all GitHub repositories the authenticated user can access.

    Uses the GitHub OAuth access token stored in the session (server-side only)
    and marks each repository as ``connected`` when it is already linked to the
    user through the GitHub App installation. Pass ``?force=1`` to always
    re-sync with the installation (used when the user opens this page).
    """
    user_id = _current_user_id(db, session)
    session_data = get_session(session)
    access_token = session_data.get("access_token") if session_data else None
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub access token not available; please sign in again",
        )

    user = db.get(User, user_id)
    if user is not None:
        try:
            await maybe_sync_user_repositories(db, user, force=force)
        except Exception:
            pass

    try:
        github_repos = await get_repositories(access_token)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch repositories from GitHub",
        )

    connected = {
        repository.github_id: repository
        for repository in list_repositories_for_user(db, user_id)
    }
    return [
        DiscoveredRepositoryOut(
            id=connected[repo.get("id")].id if repo.get("id") in connected else None,
            github_id=repo.get("id"),
            owner=(repo.get("owner") or {}).get("login", ""),
            name=repo.get("name", ""),
            full_name=repo.get("full_name", ""),
            is_private=bool(repo.get("private", False)),
            language=repo.get("language"),
            default_branch=repo.get("default_branch"),
            connected=repo.get("id") in connected,
            pull_request_count=(
                len(connected[repo.get("id")].pull_requests)
                if repo.get("id") in connected
                else 0
            ),
        )
        for repo in sorted(github_repos, key=lambda r: r.get("full_name", ""))
    ]


@router.get("/repositories/connect-url", response_model=ConnectUrlOut)
def repository_connect_url(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> ConnectUrlOut:
    """Return the GitHub App installation URL to connect repositories."""
    _current_user_id(db, session)
    if not settings.github_app_slug:
        raise HTTPException(
            status_code=500, detail="GitHub App slug not configured"
        )
    return ConnectUrlOut(
        install_url=(
            f"https://github.com/apps/{settings.github_app_slug}/installations/new"
        )
    )


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
    return _repository_out(repository)


@router.get(
    "/repositories/{repository_id}/pull-requests",
    response_model=list[PullRequestSummaryOut],
)
def read_repository_pull_requests(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[PullRequestSummaryOut]:
    user_id = _current_user_id(db, session)
    if get_repository_for_user(db, repository_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return [
        _pull_request_summary(pr)
        for pr in list_repository_pull_requests_for_user(db, repository_id, user_id)
    ]


async def _repository_installation_token(
    db: Session, repository: Repository, user_id: int
) -> str:
    user = db.get(User, user_id)
    installation_id = user.github_installation_id if user is not None else None
    if not installation_id:
        raise HTTPException(
            status_code=400,
            detail="GitHub App is not installed for this repository",
        )
    try:
        auth = await get_installation_token(
            settings.github_app_id,
            settings.github_app_private_key_path,
            installation_id,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Could not authenticate with the GitHub App",
        )
    token = auth.get("token")
    if not token:
        raise HTTPException(
            status_code=502,
            detail="Could not authenticate with the GitHub App",
        )
    return token


@router.post(
    "/repositories/{repository_id}/unconnect",
    response_model=UnconnectOut,
)
def unconnect_repository(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UnconnectOut:
    """Disconnect a repository from the current user.

    Detaches locally, remembers the disconnect so re-syncs do not re-attach
    it, and returns the GitHub App installation page so the user can remove
    repository access there too. When GitHub redirects back, Quorum shows the
    "disconnected" confirmation.
    """
    user_id = _current_user_id(db, session)
    repository = get_repository_for_user(db, repository_id, user_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    user = db.get(User, user_id)
    if user is not None:
        exclude_repository(db, user, repository.full_name)
    repository.user_id = None
    db.commit()

    install_url = None
    if user is not None and user.github_installation_id is not None:
        user.expects_disconnect = True
        db.commit()
        install_url = (
            f"https://github.com/settings/installations/"
            f"{user.github_installation_id}"
        )
    return UnconnectOut(install_url=install_url)


@router.get("/repositories/{repository_id}/branches", response_model=list[str])
async def read_repository_branches(
    repository_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[str]:
    """List the branches of a connected repository from GitHub."""
    user_id = _current_user_id(db, session)
    repository = get_repository_for_user(db, repository_id, user_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    token = await _repository_installation_token(db, repository, user_id)
    try:
        branches = await list_branches(token, repository.owner, repository.name)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch branches from GitHub",
        )
    return sorted(branches)


@router.post(
    "/repositories/{repository_id}/pull-requests",
    response_model=PullRequestSummaryOut,
    status_code=201,
)
async def create_repository_pull_request(
    repository_id: int,
    body: CreatePullRequestRequest,
    background_tasks: BackgroundTasks,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> PullRequestSummaryOut:
    """Create a real pull request on GitHub and start Quorum analysis."""
    user_id = _current_user_id(db, session)
    repository = get_repository_for_user(db, repository_id, user_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    title = body.title.strip()
    head = body.head.strip()
    base = body.base.strip()
    if not title or not head or not base:
        raise HTTPException(
            status_code=400,
            detail="title, head, and base are required",
        )

    token = await _repository_installation_token(db, repository, user_id)
    try:
        created = await create_pull_request(
            token,
            repository.owner,
            repository.name,
            title,
            head,
            base,
            body.body,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Could not create the pull request on GitHub",
        )

    pull_request = upsert_pull_request(db, created, repository)
    if pull_request is None:
        raise HTTPException(
            status_code=502,
            detail="GitHub did not return a valid pull request",
        )
    background_tasks.add_task(run_analysis_for_pull_request, pull_request.id)
    return _pull_request_summary(pull_request)


def _review_summary(run: AnalysisRun) -> ReviewSummaryOut:
    pull_request = run.pull_request
    repository = pull_request.repository if pull_request is not None else None
    severity_counts: dict[str, int] = {}
    for finding in run.security_findings:
        severity = (finding.severity or "").lower() or "info"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    coverage = run.coverage_results[0] if run.coverage_results else None
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
        recommendation=(
            recommendation_for(run.merge_readiness_score)
            if run.merge_readiness_score is not None
            else None
        ),
        started_at=run.started_at,
        completed_at=run.completed_at,
        finding_count=len(run.security_findings),
        critical_count=severity_counts.get("critical", 0),
        high_count=severity_counts.get("high", 0),
        medium_count=severity_counts.get("medium", 0),
        low_count=severity_counts.get("low", 0),
        info_count=severity_counts.get("info", 0),
        test_count=len(run.test_runs),
        coverage_before=coverage.coverage_before if coverage is not None else None,
        coverage_after=coverage.coverage_after if coverage is not None else None,
        coverage_delta=coverage.coverage_delta if coverage is not None else None,
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
        _analysis_run_out(run)
        for run in list_analysis_runs_for_pull_request(db, pull_request_id)
    ]


def _analysis_run_out(run: AnalysisRun) -> AnalysisRunOut:
    return AnalysisRunOut(
        id=run.id,
        pull_request_id=run.pull_request_id,
        status=run.status,
        merge_readiness_score=run.merge_readiness_score,
        started_at=run.started_at,
        completed_at=run.completed_at,
        recommendation=(
            recommendation_for(run.merge_readiness_score)
            if run.merge_readiness_score is not None
            else None
        ),
    )


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


def _finding_out(finding: SecurityFinding) -> FindingOut:
    run = finding.analysis_run
    pull_request = run.pull_request if run is not None else None
    repository = pull_request.repository if pull_request is not None else None
    return FindingOut(
        id=finding.id,
        analysis_run_id=finding.analysis_run_id,
        rule_id=finding.rule_id,
        severity=finding.severity,
        title=finding.title,
        file=finding.file,
        line=finding.line,
        evidence=finding.evidence,
        explanation=finding.explanation,
        confidence=finding.confidence,
        pull_request_id=pull_request.id if pull_request is not None else 0,
        pr_number=pull_request.number if pull_request is not None else 0,
        pr_title=pull_request.title if pull_request is not None else "",
        repository_id=repository.id if repository is not None else 0,
        repository_full_name=(
            repository.full_name if repository is not None else ""
        ),
    )


@router.get("/findings", response_model=list[FindingOut])
def read_findings(
    limit: int = Query(default=10, ge=1, le=100),
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[FindingOut]:
    user_id = _current_user_id(db, session)
    return [
        _finding_out(finding)
        for finding in list_recent_findings_for_user(db, user_id, limit)
    ]


@router.get("/reviews/{review_id}/chat", response_model=list[ChatMessageOut])
def read_review_chat(
    review_id: int,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> list[ChatMessageOut]:
    user_id = _current_user_id(db, session)
    if get_review_for_user(db, review_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return [
        ChatMessageOut.model_validate(message)
        for message in list_chat_messages_for_review(db, review_id)
    ]


@router.post("/reviews/{review_id}/chat", response_model=ChatPostResponse)
async def post_review_chat(
    review_id: int,
    body: ChatPostRequest,
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> ChatPostResponse:
    user_id = _current_user_id(db, session)
    review = get_review_for_user(db, review_id, user_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty")

    history = list_chat_messages_for_review(db, review_id)
    create_chat_message(db, review_id, user_id, "user", question)
    try:
        answer = await answer_question(review, history, question)
    except LLMError:
        raise HTTPException(
            status_code=503,
            detail="Ask Quorum is temporarily unavailable",
        )
    create_chat_message(db, review_id, user_id, "assistant", answer)
    return ChatPostResponse(answer=answer)
