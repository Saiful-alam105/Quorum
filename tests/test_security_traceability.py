from quorum.agents.security_agent import (
    SecurityAgentFinding,
    SecurityAgentReview,
    filter_unsupported_findings,
)
from quorum.analysis.diff import ChangedFile
from quorum.analysis.semgrep import SemgrepFinding


def _finding(**overrides) -> SecurityAgentFinding:
    entry = {
        "severity": "high",
        "title": "t",
        "file": "src/app.py",
        "evidence": "eval(x)",
        "confidence": 0.9,
        "line": 8,
    }
    entry.update(overrides)
    return SecurityAgentFinding(**entry)


def _semgrep(**overrides) -> SemgrepFinding:
    entry = {
        "rule_id": "r1",
        "severity": "high",
        "file": "src/app.py",
        "line": 8,
        "message": "m",
        "evidence": "eval(x)",
        "confidence": 0.7,
    }
    entry.update(overrides)
    return SemgrepFinding(**entry)


def _changed(path: str) -> ChangedFile:
    return ChangedFile(path=path, status="modified")


class TestFilterUnsupportedFindings:
    def test_matching_finding_kept(self) -> None:
        review = SecurityAgentReview(findings=[_finding()])
        filtered = filter_unsupported_findings(review, [_semgrep()], [_changed("src/app.py")])
        assert len(filtered.findings) == 1

    def test_unknown_file_dropped(self) -> None:
        review = SecurityAgentReview(findings=[_finding(file="other/evil.py")])
        filtered = filter_unsupported_findings(review, [_semgrep()], [_changed("src/app.py")])
        assert filtered.findings == []

    def test_file_not_changed_dropped(self) -> None:
        review = SecurityAgentReview(findings=[_finding(file="unchanged.py")])
        filtered = filter_unsupported_findings(
            review,
            [_semgrep(file="unchanged.py")],
            [_changed("src/app.py")],
        )
        assert filtered.findings == []

    def test_line_not_in_evidence_dropped(self) -> None:
        review = SecurityAgentReview(findings=[_finding(file="src/app.py", line=99)])
        filtered = filter_unsupported_findings(review, [_semgrep(line=8)], [_changed("src/app.py")])
        assert filtered.findings == []

    def test_none_line_kept_when_file_matches(self) -> None:
        review = SecurityAgentReview(findings=[_finding(line=None)])
        filtered = filter_unsupported_findings(review, [_semgrep()], [_changed("src/app.py")])
        assert len(filtered.findings) == 1

    def test_file_without_semgrep_evidence_dropped(self) -> None:
        review = SecurityAgentReview(findings=[_finding()])
        filtered = filter_unsupported_findings(review, [], [_changed("src/app.py")])
        assert filtered.findings == []

    def test_empty_review_returns_empty(self) -> None:
        review = SecurityAgentReview(findings=[])
        filtered = filter_unsupported_findings(review, [_semgrep()], [_changed("src/app.py")])
        assert filtered.findings == []

    def test_partial_keep(self) -> None:
        review = SecurityAgentReview(
            findings=[
                _finding(),
                _finding(file="other.py"),
                _finding(file="src/app.py", line=99),
            ]
        )
        filtered = filter_unsupported_findings(
            review,
            [_semgrep()],
            [_changed("src/app.py"), _changed("other.py")],
        )
        assert [f.file for f in filtered.findings] == ["src/app.py"]

    def test_deterministic(self) -> None:
        review = SecurityAgentReview(findings=[_finding(), _finding(file="x.py")])
        args = ([_semgrep()], [_changed("src/app.py")])
        assert filter_unsupported_findings(review, *args) == filter_unsupported_findings(review, *args)