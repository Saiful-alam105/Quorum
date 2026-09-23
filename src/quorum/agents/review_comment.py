"""GitHub review comment builder (Phase 14).

Builds the concise "## Quorum Review" summary from the deterministic
Merge Readiness result and the stored evidence. Pure and deterministic.
"""

from quorum.agents.synthesis import MergeReadinessResult
from quorum.agents.test_runner import (
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
)
from quorum.database.models import CoverageResult


def _severity_counts(security_findings) -> tuple[int, int, int]:
    high = sum(1 for f in security_findings if f.severity == "high")
    medium = sum(1 for f in security_findings if f.severity == "medium")
    low = sum(1 for f in security_findings if f.severity == "low")
    return high, medium, low


def build_review_comment(
    merge_readiness: MergeReadinessResult,
    security_findings,
    test_outcomes,
    coverage: CoverageResult | None,
) -> str:
    """Build the Quorum review summary comment for a pull request."""
    lines = ["## Quorum Review", ""]

    lines.append("### Merge Readiness")
    lines.append(f"{merge_readiness.score}/100")
    lines.append("")

    lines.append("### Security")
    high, medium, low = _severity_counts(security_findings)
    if security_findings:
        lines.append(f"{high} High, {medium} Medium, {low} Low")
    else:
        lines.append("None")
    lines.append("")

    lines.append("### Tests")
    passed = sum(1 for outcome in test_outcomes if outcome.status == STATUS_PASSED)
    failed = sum(
        1
        for outcome in test_outcomes
        if outcome.status in (STATUS_FAILED, STATUS_ERROR)
    )
    skipped = sum(1 for outcome in test_outcomes if outcome.status == STATUS_SKIPPED)
    lines.append(f"Generated tests: {len(test_outcomes)}")
    lines.append(f"Passed: {passed}")
    lines.append(f"Failed: {failed}")
    if skipped:
        lines.append(f"Skipped: {skipped}")
    lines.append("")

    lines.append("### Coverage")
    if coverage is None:
        lines.append("Not measured")
    else:
        lines.append(
            f"{coverage.coverage_before:.0f}% → {coverage.coverage_after:.0f}%"
        )
        lines.append(f"Delta: {coverage.coverage_delta:+.0f}%")
    lines.append("")

    lines.append("### Recommendation")
    lines.append(merge_readiness.recommendation)

    return "\n".join(lines)