"""Orchestrator pipeline stages.

Each stage receives the current database session and an AnalysisContext and
advances one part of the pull-request analysis pipeline.
"""

import logging
from typing import TYPE_CHECKING

from quorum.analysis.diff import parse_unified_diff
from quorum.github.diff_service import DiffFetchError, fetch_pr_diff

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from quorum.orchestrator.runner import AnalysisContext

logger = logging.getLogger(__name__)


async def extract_diff_stage(
    session: "Session", context: "AnalysisContext"
) -> None:
    """Fetch and parse the pull request diff into ``context.changed_files``."""
    if context.installation_id is None:
        raise DiffFetchError(
            f"cannot extract diff for {context.owner}/{context.repo}#"
            f"{context.pr_number}: no GitHub installation id"
        )

    diff_text = await fetch_pr_diff(
        context.installation_id,
        context.owner,
        context.repo,
        context.pr_number,
    )
    context.changed_files = parse_unified_diff(diff_text)
    logger.info(
        "extracted diff for %s/%s#%s: %d changed file(s)",
        context.owner,
        context.repo,
        context.pr_number,
        len(context.changed_files),
    )