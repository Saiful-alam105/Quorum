import pytest

from evaluation.metrics import (
    coverage_delta_summary,
    security_metrics,
    summarize,
    test_pass_rate as compute_test_pass_rate,
)


def _finding(file: str, line: int | None, severity: str = "high") -> dict:
    return {"file": file, "line": line, "severity": severity}


class TestSecurityMetrics:
    def test_perfect_match(self) -> None:
        predicted = [
            _finding("app.py", 5, "high"),
            _finding("app.py", 8, "medium"),
        ]
        labeled = [
            _finding("app.py", 5, "high"),
            _finding("app.py", 8, "medium"),
        ]
        result = security_metrics(predicted, labeled)
        assert result["true_positives"] == 2
        assert result["false_positives"] == 0
        assert result["false_negatives"] == 0
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_no_predicted(self) -> None:
        result = security_metrics([], [_finding("app.py", 5)])
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0
        assert result["f1"] == 0.0
        assert result["false_negatives"] == 1

    def test_partial_overlap(self) -> None:
        predicted = [
            _finding("app.py", 5, "high"),
            _finding("other.py", 1, "low"),
        ]
        labeled = [
            _finding("app.py", 5, "high"),
            _finding("app.py", 9, "medium"),
        ]
        result = security_metrics(predicted, labeled)
        assert result["true_positives"] == 1
        assert result["false_positives"] == 1
        assert result["false_negatives"] == 1
        assert result["precision"] == pytest.approx(0.5)
        assert result["recall"] == pytest.approx(0.5)
        assert result["f1"] == pytest.approx(0.5)

    def test_severity_matters_by_default(self) -> None:
        predicted = [_finding("app.py", 5, "high")]
        labeled = [_finding("app.py", 5, "medium")]
        result = security_metrics(predicted, labeled)
        assert result["true_positives"] == 0

    def test_severity_ignored_when_disabled(self) -> None:
        predicted = [_finding("app.py", 5, "high")]
        labeled = [_finding("app.py", 5, "medium")]
        result = security_metrics(predicted, labeled, by_severity=False)
        assert result["true_positives"] == 1

    def test_missing_line_matches_by_file(self) -> None:
        predicted = [_finding("app.py", None, "high")]
        labeled = [_finding("app.py", None, "high")]
        result = security_metrics(predicted, labeled)
        assert result["true_positives"] == 1


class TestTestPassRate:
    def test_all_passed(self) -> None:
        outcomes = [
            {"test_name": "t1", "status": "passed"},
            {"test_name": "t2", "status": "passed"},
        ]
        result = compute_test_pass_rate(outcomes)
        assert result == {"passed": 2, "failed": 0, "total": 2, "pass_rate": 1.0}

    def test_mixed(self) -> None:
        outcomes = [
            {"test_name": "t1", "status": "passed"},
            {"test_name": "t2", "status": "failed"},
        ]
        result = compute_test_pass_rate(outcomes)
        assert result["passed"] == 1
        assert result["failed"] == 1
        assert result["pass_rate"] == pytest.approx(0.5)

    def test_empty(self) -> None:
        result = compute_test_pass_rate([])
        assert result["total"] == 0
        assert result["pass_rate"] == 0.0


class TestCoverageDeltaSummary:
    def test_aggregates(self) -> None:
        results = [
            {"coverage_delta": 5.0},
            {"coverage_delta": -1.0},
            {"coverage_delta": 3.0},
        ]
        summary = coverage_delta_summary(results)
        assert summary["count"] == 3
        assert summary["mean_delta"] == pytest.approx(2.33)
        assert summary["min_delta"] == -1.0
        assert summary["max_delta"] == 5.0

    def test_empty(self) -> None:
        summary = coverage_delta_summary([])
        assert summary["count"] == 0
        assert summary["mean_delta"] is None


class TestSummarize:
    def test_aggregates_entries(self) -> None:
        evaluation = {
            "entries": [
                {
                    "id": "a",
                    "security": {
                        "true_positives": 1,
                        "false_positives": 0,
                        "false_negatives": 0,
                        "precision": 1.0,
                        "recall": 1.0,
                        "f1": 1.0,
                    },
                    "tests": {"passed": 4, "total": 5, "pass_rate": 0.8},
                },
                {
                    "id": "b",
                    "security": {
                        "true_positives": 0,
                        "false_positives": 1,
                        "false_negatives": 1,
                        "precision": 0.0,
                        "recall": 0.0,
                        "f1": 0.0,
                    },
                    "tests": {"passed": 1, "total": 1, "pass_rate": 1.0},
                },
            ]
        }
        summary = summarize(evaluation)
        assert summary["entry_count"] == 2
        assert summary["security"]["f1"] == pytest.approx(0.5)
        assert summary["tests"]["total"] == 6
        assert summary["tests"]["pass_rate"] == pytest.approx(0.9)
