"""Build a bounded, review-scoped context string for the Ask Quorum assistant.

The context contains only the selected review's stored evidence (the Pull
Request, findings, tests, and coverage). It is capped so prompts stay within a
fixed budget, matching the project's context-window rules.
"""

from quorum.database.models import (
    AnalysisRun,
    CoverageResult,
    SecurityFinding,
    TestRun,
)

MAX_CONTEXT_CHARS = 8000
MAX_EVIDENCE_CHARS = 300
MAX_EXPLANATION_CHARS = 300
MAX_FAILURE_CHARS = 300


def _finding_text(finding: SecurityFinding) -> str:
    location = f"{finding.file}"
    if finding.line is not None:
        location += f":{finding.line}"
    severity = (finding.severity or "info").upper()
    text = f"[{severity}] {finding.title} ({location})"
    explanation = (finding.explanation or "").strip().replace("\n", " ")
    if explanation:
        text += f"; explanation: {explanation[:MAX_EXPLANATION_CHARS]}"
    evidence = (finding.evidence or "").strip().replace("\n", " ")
    if evidence:
        text += f"; evidence: {evidence[:MAX_EVIDENCE_CHARS]}"
    return text


def _test_text(test: TestRun) -> str:
    text = f"{test.test_name} — {test.status}"
    failure = (test.failure_reason or "").strip().replace("\n", " ")
    if failure:
        text += f"; failure: {failure[:MAX_FAILURE_CHARS]}"
    return text


def _coverage_text(coverage: CoverageResult | None) -> str:
    if coverage is None or coverage.coverage_after is None:
        return "coverage not measured"
    text = (
        f"coverage: {coverage.coverage_before:.1f}% "
        f"-> {coverage.coverage_after:.1f}%"
    )
    if coverage.coverage_delta is not None:
        text += f" (delta {coverage.coverage_delta:+.1f}%)"
    return text


def build_review_context(review: AnalysisRun) -> str:
    """Return a bounded plain-text summary of a review's stored evidence."""
    pull_request = review.pull_request
    repository = pull_request.repository if pull_request is not None else None
    repo = repository.full_name if repository is not None else "unknown"
    pr_number = pull_request.number if pull_request is not None else 0
    pr_title = pull_request.title if pull_request is not None else ""
    pr_author = pull_request.author if pull_request is not None else ""
    pr_state = pull_request.state if pull_request is not None else ""

    lines = [
        f"Review: {repo} #{pr_number} — {pr_title}",
        f"Author: {pr_author}; state: {pr_state}",
        f"Analysis status: {review.status}",
    ]
    if review.merge_readiness_score is not None:
        lines.append(f"Merge Readiness: {review.merge_readiness_score}/100")
    else:
        lines.append("Merge Readiness: not scored")

    if review.security_findings:
        lines.append("Security findings:")
        lines.extend(f"- {_finding_text(finding)}" for finding in review.security_findings)
    if review.test_runs:
        lines.append("Generated tests:")
        lines.extend(f"- {_test_text(test)}" for test in review.test_runs)

    coverage = review.coverage_results[0] if review.coverage_results else None
    lines.append(f"- {_coverage_text(coverage)}")

    context = "\n".join(lines)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n[...truncated]"
    return context