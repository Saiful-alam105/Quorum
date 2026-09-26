"""Offline Pull Request evaluation runner (Phase 18).

For each labeled dataset entry this writes the changed files to a temporary
directory, runs the real Semgrep evidence pipeline, compares the predicted
findings to the manual labels, and writes reproducible results under
``evaluation/results/``.

Run from the repository root:

    python -m evaluation.run
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evaluation.dataset import load_dataset  # noqa: E402
from evaluation.metrics import security_metrics, summarize, test_pass_rate  # noqa: E402
from quorum.analysis.semgrep import parse_semgrep_json, run_semgrep  # noqa: E402


def run_semgrep_on_files(files: dict[str, str]) -> list[dict]:
    """Scan changed file contents with Semgrep and return normalized findings."""
    with tempfile.TemporaryDirectory() as scan_dir:
        root = Path(scan_dir)
        for path, content in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        raw = run_semgrep(scan_dir)
        findings = parse_semgrep_json(raw, path_prefix=scan_dir)

    return [
        {
            "file": finding.file,
            "line": finding.line,
            "severity": finding.severity,
            "rule_id": finding.rule_id,
            "title": finding.message,
            "evidence": finding.evidence,
        }
        for finding in findings
    ]


def evaluate_entry(entry: dict, measured_coverage_delta: float | None = None) -> dict:
    """Run the evidence pipeline on one entry and compute its metrics."""
    predicted = run_semgrep_on_files(entry["files"])
    security = security_metrics(predicted, entry["labeled_findings"])
    labeled_tests = entry.get("labeled_tests") or {}
    tests = test_pass_rate(
        [{"status": "passed"}] * labeled_tests.get("passed", 0)
        + [{"status": "failed"}] * (labeled_tests.get("total", 0) - labeled_tests.get("passed", 0))
    )
    expected_delta = entry.get("expected_coverage_delta")
    coverage = {"expected_delta": expected_delta}
    if measured_coverage_delta is not None and expected_delta is not None:
        coverage["delta_accuracy"] = round(
            abs(measured_coverage_delta - expected_delta), 2
        )
    return {
        "id": entry["id"],
        "predicted_findings": predicted,
        "security": security,
        "tests": tests,
        "coverage": coverage,
    }


def run_evaluation(directory: Path | None = None) -> dict:
    """Evaluate every dataset entry and return a reproducible report."""
    entries = load_dataset(directory)
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": [evaluate_entry(entry) for entry in entries],
    }
    results["summary"] = summarize(results)
    return results


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the Quorum PR evaluation.")
    parser.add_argument("--dataset", default=None, help="dataset directory (default: evaluation/dataset)")
    parser.add_argument("--out", default=None, help="output results file (default: evaluation/results/TIMESTAMP.json)")
    args = parser.parse_args()

    results = run_evaluation(Path(args.dataset) if args.dataset else None)

    out = args.out
    if not out:
        results_dir = Path(__file__).resolve().parent / "results"
        results_dir.mkdir(exist_ok=True)
        out = results_dir / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
        )
    Path(out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())