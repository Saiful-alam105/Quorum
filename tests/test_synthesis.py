from quorum.agents.security_agent import SecurityAgentFinding
from quorum.agents.synthesis import (
    MergeReadinessResult,
    compute_merge_readiness_score,
    recommendation_for,
)
from quorum.agents.test_runner import STATUS_ERROR, STATUS_FAILED, STATUS_PASSED, TestOutcome


def _finding(severity: str) -> SecurityAgentFinding:
    return SecurityAgentFinding(
        severity=severity, title="t", file="f.py", evidence="e", confidence=0.8
    )


def _outcome(status: str) -> TestOutcome:
    return TestOutcome(name=f"t::{status}", status=status)


class TestComputeMergeReadinessScore:
    def test_clean_pr_with_high_coverage(self) -> None:
        result = compute_merge_readiness_score(
            [], [_outcome(STATUS_PASSED)], 90.0
        )
        assert result.score == 100

    def test_no_tests_deducts(self) -> None:
        result = compute_merge_readiness_score([], [], 90.0)
        assert result == MergeReadinessResult(
            score=90,
            recommendation="Ready to merge",
            test_deduction=10,
        )

    def test_no_tests_no_coverage(self) -> None:
        result = compute_merge_readiness_score([], [], None)
        assert result.score == 80
        assert result.test_deduction == 10
        assert result.coverage_deduction == 10

    def test_high_finding_deducts_20(self) -> None:
        result = compute_merge_readiness_score([_finding("high")], [_outcome(STATUS_PASSED)], 90.0)
        assert result.score == 80
        assert result.security_deduction == 20

    def test_medium_and_low_findings(self) -> None:
        result = compute_merge_readiness_score(
            [_finding("medium"), _finding("low")], [_outcome(STATUS_PASSED)], 90.0
        )
        assert result.security_deduction == 15
        assert result.score == 85

    def test_failed_tests_deduct_5_each(self) -> None:
        result = compute_merge_readiness_score(
            [],
            [_outcome(STATUS_FAILED), _outcome(STATUS_ERROR), _outcome(STATUS_PASSED)],
            90.0,
        )
        assert result.test_deduction == 10
        assert result.score == 90

    def test_failed_test_cap_at_25(self) -> None:
        outcomes = [_outcome(STATUS_FAILED) for _ in range(6)]
        result = compute_merge_readiness_score([], outcomes, 90.0)
        assert result.test_deduction == 25

    def test_coverage_bands(self) -> None:
        assert compute_merge_readiness_score([], [_outcome(STATUS_PASSED)], 30.0).coverage_deduction == 20
        assert compute_merge_readiness_score([], [_outcome(STATUS_PASSED)], 60.0).coverage_deduction == 10
        assert compute_merge_readiness_score([], [_outcome(STATUS_PASSED)], 95.0).coverage_deduction == 0
        assert compute_merge_readiness_score([], [_outcome(STATUS_PASSED)], None).coverage_deduction == 10

    def test_clamps_to_zero(self) -> None:
        result = compute_merge_readiness_score(
            [_finding("high") for _ in range(6)],
            [_outcome(STATUS_FAILED) for _ in range(6)],
            10.0,
        )
        assert result.score == 0

    def test_deterministic(self) -> None:
        args = ([_finding("high"), _finding("low")], [_outcome(STATUS_FAILED)], 55.0)
        assert compute_merge_readiness_score(*args) == compute_merge_readiness_score(*args)


class TestRecommendationFor:
    def test_bands(self) -> None:
        assert recommendation_for(95) == "Ready to merge"
        assert recommendation_for(90) == "Ready to merge"
        assert recommendation_for(80) == "Approve with minor concerns"
        assert recommendation_for(70) == "Approve with minor concerns"
        assert recommendation_for(60) == "Needs review"
        assert recommendation_for(50) == "Needs review"
        assert recommendation_for(40) == "Do not merge"