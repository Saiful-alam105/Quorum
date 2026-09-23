"""Result synthesis and Merge Readiness scoring (Phase 13).

Combines the security, test, and coverage results into a deterministic
0-100 Merge Readiness Score. The formula is fully documented here and never
involves the LLM: the same evidence always produces the same score.

Formula (start at 100):
- Security: -20 per high, -10 per medium, -5 per low finding.
- Tests: -10 when no tests were generated/run; -5 per failed/error outcome
  (capped at -25).
- Coverage: -10 when not measured; -20 when after < 50%; -10 when after < 80%;
  otherwise 0.
The result is clamped to [0, 100].
"""

from dataclasses import dataclass

from quorum.agents.test_runner import STATUS_ERROR, STATUS_FAILED

_SECURITY_DEDUCTIONS = {"high": 20, "medium": 10, "low": 5}


@dataclass(frozen=True)
class MergeReadinessResult:
    """The deterministic scoring outcome plus its component deductions."""

    score: int
    recommendation: str
    security_deduction: int = 0
    test_deduction: int = 0
    coverage_deduction: int = 0


def _security_deduction(security_findings) -> int:
    total = 0
    for finding in security_findings:
        severity = (getattr(finding, "severity", None) or "low").lower()
        total += _SECURITY_DEDUCTIONS.get(severity, 5)
    return min(total, 100)


def _test_deduction(test_outcomes) -> int:
    if not test_outcomes:
        return 10
    failed = sum(
        1
        for outcome in test_outcomes
        if outcome.status in (STATUS_FAILED, STATUS_ERROR)
    )
    return min(failed * 5, 25)


def _coverage_deduction(coverage_after: float | None) -> int:
    if coverage_after is None:
        return 10
    if coverage_after < 50:
        return 20
    if coverage_after < 80:
        return 10
    return 0


def recommendation_for(score: int) -> str:
    """Return the deterministic recommendation band for a score."""
    if score >= 90:
        return "Ready to merge"
    if score >= 70:
        return "Approve with minor concerns"
    if score >= 50:
        return "Needs review"
    return "Do not merge"


def compute_merge_readiness_score(
    security_findings,
    test_outcomes,
    coverage_after: float | None,
) -> MergeReadinessResult:
    """Compute the deterministic Merge Readiness Score from the evidence."""
    security = _security_deduction(security_findings)
    tests = _test_deduction(test_outcomes)
    coverage = _coverage_deduction(coverage_after)
    score = max(0, min(100, 100 - security - tests - coverage))
    return MergeReadinessResult(
        score=score,
        recommendation=recommendation_for(score),
        security_deduction=security,
        test_deduction=tests,
        coverage_deduction=coverage,
    )