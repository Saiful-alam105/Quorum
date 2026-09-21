import json

import pytest

from quorum.agents.security_agent import (
    SEVERITY_VALUES,
    SecurityAgentParseError,
    parse_security_review,
)


def _finding(**overrides) -> dict:
    entry = {
        "severity": "high",
        "title": "Detected eval()",
        "file": "src/app.py",
        "evidence": "return eval(x)",
        "confidence": 0.9,
        "rule_id": "python.lang.security.audit.eval-detected",
        "line": 8,
        "explanation": "eval on untrusted input enables code injection",
    }
    entry.update(overrides)
    return entry


def _raw(findings) -> str:
    return json.dumps({"findings": findings})


class TestParseValidReview:
    def test_full_finding_parses(self) -> None:
        review = parse_security_review(_raw([_finding()]))
        assert len(review.findings) == 1
        finding = review.findings[0]
        assert finding.severity == "high"
        assert finding.title == "Detected eval()"
        assert finding.file == "src/app.py"
        assert finding.line == 8
        assert finding.evidence == "return eval(x)"
        assert finding.explanation == "eval on untrusted input enables code injection"
        assert finding.confidence == 0.9
        assert finding.rule_id == "python.lang.security.audit.eval-detected"

    def test_optional_fields_can_be_omitted(self) -> None:
        review = parse_security_review(
            _raw(
                [
                    _finding(
                        rule_id="",
                        line=None,
                        explanation=None,
                    )
                ]
            )
        )
        finding = review.findings[0]
        assert finding.rule_id == ""
        assert finding.line is None
        assert finding.explanation is None

    def test_empty_findings_is_valid(self) -> None:
        review = parse_security_review(_raw([]))
        assert review.findings == []

    def test_multiple_findings_in_order(self) -> None:
        review = parse_security_review(
            _raw([_finding(title="a"), _finding(title="b")])
        )
        assert [f.title for f in review.findings] == ["a", "b"]

    def test_severity_is_case_insensitive(self) -> None:
        review = parse_security_review(_raw([_finding(severity="HIGH")]))
        assert review.findings[0].severity == "high"


class TestSeverity:
    def test_severity_values_are_controlled(self) -> None:
        assert SEVERITY_VALUES == ("high", "medium", "low")

    def test_invalid_severity_rejected(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([_finding(severity="critical")]))

    def test_missing_severity_rejected(self) -> None:
        entry = _finding()
        del entry["severity"]
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([entry]))


class TestConfidence:
    def test_out_of_range_confidence_rejected(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([_finding(confidence=1.5)]))

    def test_negative_confidence_rejected(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([_finding(confidence=-0.1)]))

    def test_string_confidence_coerced(self) -> None:
        review = parse_security_review(_raw([_finding(confidence="0.8")]))
        assert review.findings[0].confidence == 0.8


class TestRequiredFields:
    def test_missing_title_rejected(self) -> None:
        entry = _finding()
        del entry["title"]
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([entry]))

    def test_missing_file_rejected(self) -> None:
        entry = _finding()
        del entry["file"]
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([entry]))

    def test_missing_evidence_rejected(self) -> None:
        entry = _finding()
        del entry["evidence"]
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review(_raw([entry]))


class TestInvalidInput:
    def test_malformed_json_raises(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="valid JSON"):
            parse_security_review("not json")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="valid JSON"):
            parse_security_review("")

    def test_non_object_root_raises(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="JSON object"):
            parse_security_review("[1, 2, 3]")

    def test_missing_findings_key_raises(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="no findings"):
            parse_security_review("{}")

    def test_findings_not_a_list_raises(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="not a list"):
            parse_security_review('{"findings": "oops"}')

    def test_non_dict_finding_raises(self) -> None:
        with pytest.raises(SecurityAgentParseError, match="validation"):
            parse_security_review('{"findings": [1, 2]}')


class TestDeterminism:
    def test_same_input_same_output(self) -> None:
        raw = _raw([_finding(), _finding(title="b", severity="medium")])
        assert parse_security_review(raw) == parse_security_review(raw)