"""Build a bounded, review-scoped context string for the Ask Quorum assistant.

The context contains only the selected review's stored evidence (the Pull
Request, findings, tests, and coverage). It is capped so prompts stay within a
fixed budget, matching the project's context-window rules.
"""

from quorum.agents.synthesis import (
    _coverage_deduction,
    _security_deduction,
    _test_deduction,
    recommendation_for,
)
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


def _score_text(review: AnalysisRun) -> str:
    """Explain a review's Merge Readiness score.

    Uses the deduction breakdown stored at synthesis time when available
    (including docs-only PRs that skipped test/coverage deductions), otherwise
    recomputes it from the stored evidence.
    """
    score = review.merge_readiness_score
    if score is None:
        return "Merge Readiness: not scored"
    if (
        review.security_deduction is not None
        and review.test_deduction is not None
        and review.coverage_deduction is not None
    ):
        security = review.security_deduction
        tests = review.test_deduction
        coverage = review.coverage_deduction
    else:
        security = _security_deduction(review.security_findings)
        tests = _test_deduction(review.test_runs)
        coverage_after = (
            review.coverage_results[0].coverage_after
            if review.coverage_results
            else None
        )
        coverage = _coverage_deduction(coverage_after)
    breakdown = f"{100} - {security} (security findings) - {tests} (tests) - {coverage} (coverage)"
    return (
        f"Merge Readiness: {score}/100 ({recommendation_for(score)}). "
        f"Score breakdown: {breakdown} = {score}."
    )


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
        _score_text(review),
    ]

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