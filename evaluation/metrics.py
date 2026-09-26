"""Deterministic evaluation metrics for Quorum (Phase 18).

All functions are pure and operate on plain dicts so results are reproducible
and unit-testable without a database or LLM.
"""

from __future__ import annotations


def _finding_key(finding: dict, by_severity: bool) -> tuple:
    file = str(finding.get("file") or "")
    line = finding.get("line")
    key = (file, line)
    if by_severity:
        key = (file, line, str(finding.get("severity") or "").lower())
    return key


def security_metrics(
    predicted: list[dict],
    labeled: list[dict],
    by_severity: bool = True,
) -> dict:
    """Compute precision/recall/F1 for predicted vs labeled findings.

    Findings are matched by ``(file, line[, severity])``. Missing ``line``
    values match only by file, which is a deliberate lenient fallback.
    """
    predicted_keys = {_finding_key(f, by_severity) for f in predicted}
    labeled_keys = {_finding_key(f, by_severity) for f in labeled}

    true_positives = len(predicted_keys & labeled_keys)
    false_positives = len(predicted_keys - labeled_keys)
    false_negatives = len(labeled_keys - predicted_keys)

    precision = true_positives / len(predicted_keys) if predicted_keys else 0.0
    recall = true_positives / len(labeled_keys) if labeled_keys else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def test_pass_rate(test_outcomes: list[dict]) -> dict:
    """Summarize generated-test outcomes as a pass rate."""
    passed = sum(1 for t in test_outcomes if t.get("status") == "passed")
    total = len(test_outcomes)
    rate = passed / total if total else 0.0
    return {
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": round(rate, 4),
    }


def coverage_delta_summary(coverage_results: list[dict]) -> dict:
    """Summarize coverage deltas across results."""
    deltas = [
        c.get("coverage_delta")
        for c in coverage_results
        if c.get("coverage_delta") is not None
    ]
    if not deltas:
        return {"count": 0, "mean_delta": None, "min_delta": None, "max_delta": None}
    return {
        "count": len(deltas),
        "mean_delta": round(sum(deltas) / len(deltas), 2),
        "min_delta": min(deltas),
        "max_delta": max(deltas),
    }


def summarize(evaluation: dict) -> dict:
    """Aggregate per-entry metrics into one reproducible summary."""
    entries = evaluation.get("entries", [])
    security = [e["security"] for e in entries if "security" in e]
    tests = [e["tests"] for e in entries if "tests" in e]

    def _mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 4) if values else None

    return {
        "entry_count": len(entries),
        "security": {
            "precision": _mean([s["precision"] for s in security]),
            "recall": _mean([s["recall"] for s in security]),
            "f1": _mean([s["f1"] for s in security]),
            "true_positives": sum(s["true_positives"] for s in security),
            "false_positives": sum(s["false_positives"] for s in security),
            "false_negatives": sum(s["false_negatives"] for s in security),
        },
        "tests": {
            "passed": sum(t["passed"] for t in tests),
            "total": sum(t["total"] for t in tests),
            "pass_rate": _mean([t["pass_rate"] for t in tests]),
        },
    }