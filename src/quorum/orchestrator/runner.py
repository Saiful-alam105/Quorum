"""Orchestrator runner: drives the analysis pipeline for a pull request.

The runner creates an AnalysisRun, marks it in_progress, executes the
registered pipeline stages, and records completion or failure. It accepts an
injectable session for tests and otherwise opens its own SessionLocal so
background execution never touches the request-scoped session.
"""

import logging
from dataclasses import dataclass, field
from typing import Callable

from sqlalchemy.orm import Session

from quorum.analysis.context import PreparedContext
from quorum.analysis.diff import ChangedFile
from quorum.analysis.semgrep import SemgrepFinding
from quorum.database.base import SessionLocal
from quorum.database.models import PullRequest, Repository, User
from quorum.database.repository import (
    complete_analysis_run,
    create_analysis_run,
    fail_analysis_run,
    mark_analysis_run_in_progress,
)

logger = logging.getLogger(__name__)

# Registry of pipeline stages. Phases 6-14 register their stages here.
STAGES: list[Callable[["Session", "AnalysisContext"], None]] = []


@dataclass
class AnalysisContext:
    """Snapshot of pull-request context handed to every pipeline stage."""

    pull_request_id: int
    repository_id: int
    owner: str
    repo: str
    pr_number: int
    installation_id: int | None
    changed_files: list[ChangedFile] = field(default_factory=list)
    prepared_context: PreparedContext | None = None
    analysis_run_id: int | None = None
    semgrep_findings: list[SemgrepFinding] = field(default_factory=list)


def _build_context(db: Session, pull_request: PullRequest) -> AnalysisContext:
    repository = db.get(Repository, pull_request.repository_id)
    owner = repository.owner if repository is not None else ""
    repo = repository.name if repository is not None else ""
    repository_id = repository.id if repository is not None else pull_request.repository_id

    installation_id: int | None = None
    if repository is not None and repository.user_id is not None:
        user = db.get(User, repository.user_id)
        if user is not None:
            installation_id = user.github_installation_id

    return AnalysisContext(
        pull_request_id=pull_request.id,
        repository_id=repository_id,
        owner=owner,
        repo=repo,
        pr_number=pull_request.number,
        installation_id=installation_id,
    )


async def run_analysis_for_pull_request(
    pull_request_id: int,
    db: Session | None = None,
    stages: list[Callable[["Session", "AnalysisContext"], None]] | None = None,
) -> int | None:
    """Run the analysis pipeline for a pull request.

    Returns the analysis run id, or None if the pull request does not exist.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        pull_request = session.get(PullRequest, pull_request_id)
        if pull_request is None:
            return None

        analysis_run = create_analysis_run(session, pull_request_id)
        mark_analysis_run_in_progress(session, analysis_run.id)

        context = _build_context(session, pull_request)
        context.analysis_run_id = analysis_run.id
        pipeline = STAGES if stages is None else stages

        try:
            for stage in pipeline:
                await stage(session, context)
        except Exception:
            logger.exception("analysis run %s failed", analysis_run.id)
            session.rollback()
            fail_analysis_run(session, analysis_run.id)
            raise

        complete_analysis_run(session, analysis_run.id)
        return analysis_run.id
    finally:
        if owns_session:
            session.close()


from quorum.orchestrator.stages import (
    build_context_stage,
    extract_diff_stage,
    semgrep_stage,
)

STAGES.append(extract_diff_stage)
STAGES.append(build_context_stage)
STAGES.append(semgrep_stage)