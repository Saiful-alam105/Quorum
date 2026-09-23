"""Orchestrator pipeline stages.

Each stage receives the current database session and an AnalysisContext and
advances one part of the pull-request analysis pipeline.
"""

import asyncio
import logging
import tempfile
from typing import TYPE_CHECKING

from quorum.agents.security_agent import (
    SecurityAgent,
    SecurityAgentError,
    filter_unsupported_findings,
)
from quorum.agents.test_runner import (
    measure_coverage,
    run_tests_in_sandbox,
    compute_coverage_delta,
)
from quorum.agents.test_writer import TestWriterAgent, TestWriterError
from quorum.analysis.ast_parser import analyze_changed_python
from quorum.analysis.context_selector import build_prepared_context
from quorum.analysis.diff import (
    STATUS_ADDED,
    STATUS_MODIFIED,
    STATUS_RENAMED,
    parse_unified_diff,
)
from quorum.analysis.semgrep import (
    build_scan_directory,
    has_scannable_files,
    parse_semgrep_json,
    run_semgrep,
)
from quorum.database.repository import (
    create_coverage_result,
    create_security_findings,
    create_test_runs,
    replace_security_findings,
)
from quorum.github.content_service import (
    ContentFetchError,
    fetch_file_content,
    fetch_pull_request,
)
from quorum.github.diff_service import DiffFetchError, fetch_pr_diff
from quorum.llm.factory import create_llm_provider
from quorum.sandbox.workspace import build_sandbox_workspace, write_generated_test

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


_PYTHON_STATUSES = {STATUS_ADDED, STATUS_MODIFIED, STATUS_RENAMED}


def _is_python_file(path: str) -> bool:
    return path.endswith(".py")


async def extract_ast_stage(
    session: "Session", context: "AnalysisContext"
) -> None:
    """Fetch changed Python files and extract their modified structures."""
    python_files = [
        file
        for file in context.changed_files
        if file.status in _PYTHON_STATUSES and _is_python_file(file.path)
    ]
    if not python_files:
        context.ast_files = []
        logger.info(
            "no changed python files for %s/%s#%s; skipping AST extraction",
            context.owner,
            context.repo,
            context.pr_number,
        )
        return
    if context.installation_id is None:
        raise ContentFetchError(
            f"cannot extract AST for {context.owner}/{context.repo}#"
            f"{context.pr_number}: no GitHub installation id"
        )

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

    context.ast_files = []
    for file in python_files:
        content = await fetch_content(file.path, head_sha)
        context.ast_files.append(analyze_changed_python(content, file))
    logger.info(
        "extracted AST for %d python file(s) for %s/%s#%s",
        len(context.ast_files),
        context.owner,
        context.repo,
        context.pr_number,
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


async def security_agent_stage(
    session: "Session", context: "AnalysisContext"
) -> None:
    """Run the Security Agent over Semgrep evidence and persist the findings."""
    if not context.semgrep_findings:
        context.security_findings = []
        logger.info(
            "no Semgrep findings for %s/%s#%s; skipping security agent",
            context.owner,
            context.repo,
            context.pr_number,
        )
        return
    if context.analysis_run_id is None:
        raise SecurityAgentError("cannot persist findings: no analysis run id")

    provider = create_llm_provider(role="security")
    agent = SecurityAgent(provider)
    review = await agent.review(
        context.prepared_context,
        context.semgrep_findings,
        context.owner,
        context.repo,
        context.pr_number,
    )
    filtered = filter_unsupported_findings(
        review, context.semgrep_findings, context.changed_files
    )
    context.security_findings = filtered.findings
    replace_security_findings(
        session,
        context.analysis_run_id,
        [
            {
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "title": finding.title,
                "file": finding.file,
                "line": finding.line,
                "evidence": finding.evidence,
                "explanation": finding.explanation,
                "confidence": finding.confidence,
            }
            for finding in filtered.findings
        ],
    )
    logger.info(
        "security agent produced %d finding(s) for %s/%s#%s",
        len(filtered.findings),
        context.owner,
        context.repo,
        context.pr_number,
    )


async def generate_tests_stage(
    session: "Session", context: "AnalysisContext"
) -> None:
    """Generate tests for modified functions, run them, and store results."""
    modified_functions = [
        function
        for info in context.ast_files
        for function in info.functions
        if function.modified
    ]
    if not modified_functions:
        context.generated_tests = []
        context.test_results = []
        context.coverage = None
        logger.info(
            "no modified functions for %s/%s#%s; skipping test writer",
            context.owner,
            context.repo,
            context.pr_number,
        )
        return
    if context.analysis_run_id is None:
        raise TestWriterError("cannot persist tests: no analysis run id")

    provider = create_llm_provider(role="test")
    agent = TestWriterAgent(provider)
    generated = await agent.generate_tests(
        context.ast_files,
        context.prepared_context,
        context.owner,
        context.repo,
        context.pr_number,
    )
    context.generated_tests = generated.tests
    if not generated.tests:
        context.test_results = []
        context.coverage = None
        logger.info(
            "test writer produced no tests for %s/%s#%s",
            context.owner,
            context.repo,
            context.pr_number,
        )
        return

    if context.installation_id is None:
        raise TestWriterError("cannot build workspace: no GitHub installation id")
    pr = await fetch_pull_request(
        context.installation_id,
        context.owner,
        context.repo,
        context.pr_number,
    )
    head_sha = (pr.get("head") or {}).get("sha")
    if not head_sha:
        raise TestWriterError(
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

    with tempfile.TemporaryDirectory() as workspace:
        await build_sandbox_workspace(
            context.changed_files, fetch_content, head_sha, workspace
        )
        coverage_before = measure_coverage(workspace)
        test_paths: list[str] = []
        for test in generated.tests:
            write_generated_test(workspace, test.name, test.code)
            test_paths.append(test.name)
        coverage_after = measure_coverage(workspace, test_paths=test_paths)
        execution = run_tests_in_sandbox(workspace, test_paths=test_paths)

    context.test_results = execution.outcomes
    create_test_runs(
        session,
        context.analysis_run_id,
        [
            {"test_name": outcome.name, "status": outcome.status}
            for outcome in execution.outcomes
        ],
    )
    delta = compute_coverage_delta(coverage_before, coverage_after)
    context.coverage = create_coverage_result(
        session, context.analysis_run_id, coverage_before, coverage_after, delta
    )
    logger.info(
        "test writer ran %d test(s) for %s/%s#%s: coverage %.1f%% -> %.1f%% "
        "(delta %+.1f)",
        len(execution.outcomes),
        context.owner,
        context.repo,
        context.pr_number,
        coverage_before,
        coverage_after,
        delta,
    )