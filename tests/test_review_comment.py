from quorum.agents.review_comment import build_review_comment
from quorum.agents.security_agent import SecurityAgentFinding
from quorum.agents.synthesis import MergeReadinessResult
from quorum.agents.test_runner import STATUS_ERROR, STATUS_FAILED, STATUS_PASSED, STATUS_SKIPPED, TestOutcome
from quorum.database.models import CoverageResult


def _finding(severity: str) -> SecurityAgentFinding:
    return SecurityAgentFinding(
        severity=severity, title="t", file="f.py", evidence="e", confidence=0.8
    )


def _outcome(status: str) -> TestOutcome:
    return TestOutcome(name="t.py::t", status=status)


class TestBuildReviewComment:
    def test_full_comment(self) -> None:
        comment = build_review_comment(
            MergeReadinessResult(score=82, recommendation="Approve with minor concerns"),
            [_finding("high"), _finding("medium")],
            [_outcome(STATUS_PASSED), _outcome(STATUS_PASSED), _outcome(STATUS_FAILED)],
            CoverageResult(coverage_before=72.0, coverage_after=81.0, coverage_delta=9.0),
        )
        assert "## Quorum Review" in comment
        assert "### Merge Readiness" in comment
        assert "82/100" in comment
        assert "1 High, 1 Medium, 0 Low" in comment
        assert "Generated tests: 3" in comment
        assert "Passed: 2" in comment
        assert "Failed: 1" in comment
        assert "72% → 81%" in comment
        assert "Delta: +9%" in comment
        assert "Approve with minor concerns" in comment

    def test_error_counts_as_failed(self) -> None:
        comment = build_review_comment(
            MergeReadinessResult(score=70, recommendation="Approve with minor concerns"),
            [],
            [_outcome(STATUS_ERROR), _outcome(STATUS_SKIPPED)],
            None,
        )
        assert "Failed: 1" in comment
        assert "Skipped: 1" in comment

    def test_no_findings_shows_none(self) -> None:
        comment = build_review_comment(
            MergeReadinessResult(score=95, recommendation="Ready to merge"),
            [],
            [_outcome(STATUS_PASSED)],
            CoverageResult(coverage_before=50.0, coverage_after=99.0, coverage_delta=49.0),
        )
        assert "None" in comment

    def test_no_tests(self) -> None:
        comment = build_review_comment(
            MergeReadinessResult(score=80, recommendation="Approve with minor concerns"),
            [],
            [],
            None,
        )
        assert "Generated tests: 0" in comment
        assert "Passed: 0" in comment
        assert "Failed: 0" in comment

    def test_no_coverage_not_measured(self) -> None:
        comment = build_review_comment(
            MergeReadinessResult(score=80, recommendation="Approve with minor concerns"),
            [],
            [],
            None,
        )
        assert "Not measured" in comment

    def test_negative_delta(self) -> None:
        comment = build_review_comment(
            MergeReadinessResult(score=70, recommendation="Approve with minor concerns"),
            [],
            [],
            CoverageResult(coverage_before=80.0, coverage_after=75.0, coverage_delta=-5.0),
        )
        assert "Delta: -5%" in comment

    def test_deterministic(self) -> None:
        args = (
            MergeReadinessResult(score=60, recommendation="Needs review"),
            [_finding("low")],
            [_outcome(STATUS_PASSED), _outcome(STATUS_FAILED)],
            CoverageResult(coverage_before=10.0, coverage_after=55.0, coverage_delta=45.0),
        )
        assert build_review_comment(*args) == build_review_comment(*args)