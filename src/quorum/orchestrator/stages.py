"""Orchestrator pipeline stages.

Each stage receives the current database session and an AnalysisContext and
advances one part of the pull-request analysis pipeline.
"""

import asyncio
import logging
import tempfile
from typing import TYPE_CHECKING

from quorum.analysis.context_selector import build_prepared_context
from quorum.analysis.diff import parse_unified_diff
from quorum.analysis.semgrep import (
    build_scan_directory,
    has_scannable_files,
    parse_semgrep_json,
    run_semgrep,
)
from quorum.database.repository import create_security_findings
from quorum.github.content_service import (
    ContentFetchError,
    fetch_file_content,
    fetch_pull_request,
)
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


async def build_context_stage(
    session: "Session", context: "AnalysisContext"
) -> None:
    """Build the bounded, prioritized context from the extracted diff."""
    context.prepared_context = build_prepared_context(context.changed_files)
    logger.info(
        "prepared context for %s/%s#%s: %d file(s), %d estimated token(s), "
        "truncated=%s",
        context.owner,
        context.repo,
        context.pr_number,
        len(context.prepared_context.files),
        context.prepared_context.total_estimated_tokens,
        context.prepared_context.truncated,
    )


async def semgrep_stage(
    session: "Session", context: "AnalysisContext"
) -> None:
    """Run Semgrep over the changed files and persist the findings."""
    if not has_scannable_files(context.changed_files):
        context.semgrep_findings = []
        logger.info(
            "no scannable files for %s/%s#%s; skipping Semgrep",
            context.owner,
            context.repo,
            context.pr_number,
        )
        return
    if context.installation_id is None:
        raise ContentFetchError(
            f"cannot scan {context.owner}/{context.repo}#{context.pr_number}: "
            "no GitHub installation id"
        )
    if context.analysis_run_id is None:
        raise ContentFetchError("cannot persist findings: no analysis run id")

    pr = await fetch_pull_request(
        context.installation_id,
        context.owner,
        context.repo,
        context.pr_number,
    )
    head_sha = (pr.get("head") or {}).get("sha")
    if not head_sha:
        raise ContentFetchError(
            f"pull request {context.owner}/{context.repo}#{context.pr_number} "
            "has no head sha"
        )

    async def fetch_content(path: str, ref: str) -> str:
        return await fetch_file_content(
            context.installation_id,
            context.owner,
            context.repo,
            path,
            ref,
        )

    with tempfile.TemporaryDirectory() as scan_dir:
        await build_scan_directory(
            context.changed_files, fetch_content, head_sha, scan_dir
        )
        raw = await asyncio.to_thread(run_semgrep, scan_dir)
        findings = parse_semgrep_json(raw, path_prefix=scan_dir)

    context.semgrep_findings = findings
    create_security_findings(
        session,
        context.analysis_run_id,
        [
            {
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "title": finding.message,
                "file": finding.file,
                "line": finding.line,
                "evidence": finding.evidence,
                "confidence": finding.confidence,
            }
            for finding in findings
        ],
    )
    logger.info(
        "semgrep found %d finding(s) for %s/%s#%s",
        len(findings),
        context.owner,
        context.repo,
        context.pr_number,
    )