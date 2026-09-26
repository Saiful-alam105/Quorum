import pytest

from evaluation.run import evaluate_entry, run_semgrep_on_files
from quorum.analysis.semgrep import SemgrepFinding


def _entry(files: dict[str, str], labeled: list[dict]) -> dict:
    return {
        "id": "pr-test",
        "repository": "quorum-dev/eval-demo",
        "pr_number": 1,
        "files": files,
        "labeled_findings": labeled,
    }


class TestRunSemgrepOnFiles:
    def test_normalizes_findings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_parse(raw: str, path_prefix: str) -> list[SemgrepFinding]:
            return [
                SemgrepFinding(
                    rule_id="python.lang.security.audit.subprocess-shell-true",
                    severity="high",
                    file="run_cmd.py",
                    line=5,
                    message="subprocess call with shell=True",
                    evidence="subprocess.call(cmd, shell=True)",
                    confidence=0.9,
                )
            ]

        monkeypatch.setattr("evaluation.run.parse_semgrep_json", fake_parse)
        monkeypatch.setattr("evaluation.run.run_semgrep", lambda scan_dir: "{}")

        findings = run_semgrep_on_files({"run_cmd.py": "import subprocess"})
        assert len(findings) == 1
        assert findings[0]["file"] == "run_cmd.py"
        assert findings[0]["line"] == 5
        assert findings[0]["severity"] == "high"
        assert findings[0]["title"] == "subprocess call with shell=True"


class TestEvaluateEntry:
    def test_computes_security_metrics_against_labels(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        labeled = [
            {"file": "run_cmd.py", "line": 5, "severity": "high"},
            {"file": "run_cmd.py", "line": 8, "severity": "medium"},
        ]

        def fake_parse(raw: str, path_prefix: str) -> list[SemgrepFinding]:
            return [
                SemgrepFinding("r1", "high", "run_cmd.py", 5, "subprocess", "e", 0.9),
            ]

        monkeypatch.setattr("evaluation.run.parse_semgrep_json", fake_parse)
        monkeypatch.setattr("evaluation.run.run_semgrep", lambda scan_dir: "{}")

        result = evaluate_entry(_entry({"run_cmd.py": "code"}, labeled))
        assert result["security"]["true_positives"] == 1
        assert result["security"]["false_negatives"] == 1
        assert result["security"]["precision"] == 1.0
        assert result["security"]["recall"] == pytest.approx(0.5)
        assert result["security"]["f1"] == pytest.approx(0.6667)

    def test_test_pass_rate_from_labels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("evaluation.run.parse_semgrep_json", lambda raw, path_prefix: [])
        monkeypatch.setattr("evaluation.run.run_semgrep", lambda scan_dir: "{}")

        entry = _entry({"a.py": "code"}, [])
        entry["labeled_tests"] = {"passed": 3, "total": 4}
        result = evaluate_entry(entry)
        assert result["tests"]["passed"] == 3
        assert result["tests"]["total"] == 4
        assert result["tests"]["pass_rate"] == pytest.approx(0.75)

    def test_coverage_accuracy_when_measured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("evaluation.run.parse_semgrep_json", lambda raw, path_prefix: [])
        monkeypatch.setattr("evaluation.run.run_semgrep", lambda scan_dir: "{}")

        entry = _entry({"a.py": "code"}, [])
        entry["expected_coverage_delta"] = 5.0
        result = evaluate_entry(entry, measured_coverage_delta=7.0)
        assert result["coverage"]["delta_accuracy"] == 2.0
