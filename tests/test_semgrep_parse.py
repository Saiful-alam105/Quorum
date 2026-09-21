import json

import pytest

from quorum.analysis.semgrep import (
    SemgrepFinding,
    SemgrepParseError,
    parse_semgrep_json,
)


def _finding(**overrides) -> dict:
    entry = {
        "check_id": "python.lang.security.audit.dangerous-system-call",
        "path": "src/app.py",
        "start": {"line": 12, "col": 1},
        "end": {"line": 12, "col": 40},
        "extra": {
            "message": "Detected dangerous subprocess call",
            "severity": "ERROR",
            "metadata": {"confidence": "HIGH"},
            "lines": "    subprocess.call(cmd)",
        },
    }
    entry.update(overrides)
    return entry


def _raw(*entries: dict) -> str:
    return json.dumps({"results": list(entries), "errors": []})


class TestParseBasic:
    def test_parses_all_fields(self) -> None:
        findings = parse_semgrep_json(_raw(_finding()))
        assert len(findings) == 1
        finding = findings[0]
        assert isinstance(finding, SemgrepFinding)
        assert finding.rule_id == "python.lang.security.audit.dangerous-system-call"
        assert finding.severity == "high"
        assert finding.file == "src/app.py"
        assert finding.line == 12
        assert finding.message == "Detected dangerous subprocess call"
        assert finding.evidence == "    subprocess.call(cmd)"
        assert finding.confidence == 1.0

    def test_multiple_findings_in_order(self) -> None:
        findings = parse_semgrep_json(
            _raw(_finding(), _finding(path="src/other.py", start={"line": 3, "col": 1}))
        )
        assert [f.file for f in findings] == ["src/app.py", "src/other.py"]
        assert [f.line for f in findings] == [12, 3]

    def test_empty_results_returns_empty_list(self) -> None:
        assert parse_semgrep_json('{"results": [], "errors": []}') == []

    def test_missing_results_field_returns_empty_list(self) -> None:
        assert parse_semgrep_json('{"errors": []}') == []


class TestSeverityMapping:
    def test_error_to_high(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra=_extra("ERROR"))))[0].severity == "high"

    def test_warning_to_medium(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra=_extra("WARNING"))))[0].severity == "medium"

    def test_info_to_low(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra=_extra("INFO"))))[0].severity == "low"

    def test_unknown_severity_defaults_to_low(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra=_extra("CATASTROPHIC"))))[0].severity == "low"

    def test_missing_severity_defaults_to_low(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra={})))[0].severity == "low"


class TestConfidenceMapping:
    def test_high_medium_low(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra=_metadata("HIGH"))))[0].confidence == 1.0
        assert parse_semgrep_json(_raw(_finding(extra=_metadata("MEDIUM"))))[0].confidence == 0.7
        assert parse_semgrep_json(_raw(_finding(extra=_metadata("LOW"))))[0].confidence == 0.4

    def test_missing_confidence_is_none(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra={"severity": "ERROR"})))[0].confidence is None

    def test_numeric_confidence_passes_through(self) -> None:
        assert parse_semgrep_json(_raw(_finding(extra=_metadata(0.55))))[0].confidence == 0.55


class TestInvalidInput:
    def test_malformed_json_raises(self) -> None:
        with pytest.raises(SemgrepParseError, match="valid JSON"):
            parse_semgrep_json("not json at all")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(SemgrepParseError, match="valid JSON"):
            parse_semgrep_json("")

    def test_non_object_root_raises(self) -> None:
        with pytest.raises(SemgrepParseError, match="JSON object"):
            parse_semgrep_json("[1, 2, 3]")

    def test_results_not_a_list_raises(self) -> None:
        with pytest.raises(SemgrepParseError, match="results list"):
            parse_semgrep_json('{"results": "oops"}')


class TestMissingFields:
    def test_missing_rule_id_skipped(self) -> None:
        entry = _finding()
        del entry["check_id"]
        assert parse_semgrep_json(_raw(entry)) == []

    def test_missing_path_skipped(self) -> None:
        entry = _finding()
        del entry["path"]
        assert parse_semgrep_json(_raw(entry)) == []

    def test_missing_line_skipped(self) -> None:
        entry = _finding()
        del entry["start"]
        assert parse_semgrep_json(_raw(entry)) == []

    def test_non_string_line_skipped(self) -> None:
        entry = _finding(start={"line": "12", "col": 1})
        assert parse_semgrep_json(_raw(entry)) == []

    def test_non_dict_entry_skipped(self) -> None:
        assert parse_semgrep_json(_raw([1, 2])) == []


class TestPathPrefix:
    def test_prefix_stripped(self) -> None:
        entry = _finding(path="C:/tmp/quorum_scan/src/app.py")
        findings = parse_semgrep_json(_raw(entry), path_prefix="C:/tmp/quorum_scan")
        assert findings[0].file == "src/app.py"

    def test_prefix_with_trailing_separator(self) -> None:
        entry = _finding(path="C:/tmp/quorum_scan/src/app.py")
        findings = parse_semgrep_json(_raw(entry), path_prefix="C:/tmp/quorum_scan/")
        assert findings[0].file == "src/app.py"

    def test_path_not_under_prefix_unchanged(self) -> None:
        entry = _finding(path="other/src/app.py")
        findings = parse_semgrep_json(_raw(entry), path_prefix="C:/tmp/quorum_scan")
        assert findings[0].file == "other/src/app.py"

    def test_no_prefix_keeps_path(self) -> None:
        findings = parse_semgrep_json(_raw(_finding()))
        assert findings[0].file == "src/app.py"


class TestDeterminism:
    def test_same_input_same_output(self) -> None:
        raw = _raw(_finding(), _finding(path="src/other.py", start={"line": 3, "col": 1}))
        first = parse_semgrep_json(raw)
        second = parse_semgrep_json(raw)
        assert first == second


def _extra(severity: str) -> dict:
    return {
        "message": "m",
        "severity": severity,
        "metadata": {"confidence": "HIGH"},
        "lines": "code",
    }


def _metadata(confidence) -> dict:
    return {
        "message": "m",
        "severity": "ERROR",
        "metadata": {"confidence": confidence},
        "lines": "code",
    }