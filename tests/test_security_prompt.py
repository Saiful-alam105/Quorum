from quorum.agents.security_agent import build_security_prompt
from quorum.analysis.context import ContextFile, ContextHunk, ContextLine, PreparedContext
from quorum.analysis.semgrep import SemgrepFinding


def _finding(**overrides) -> SemgrepFinding:
    entry = {
        "rule_id": "python.lang.security.audit.eval-detected",
        "severity": "medium",
        "file": "src/app.py",
        "line": 8,
        "message": "Detected use of eval()",
        "evidence": "return eval(x)",
        "confidence": 0.4,
    }
    entry.update(overrides)
    return SemgrepFinding(**entry)


def _context() -> PreparedContext:
    return PreparedContext(
        files=[
            ContextFile(
                path="src/app.py",
                status="modified",
                hunks=[
                    ContextHunk(
                        old_start=1,
                        old_count=2,
                        new_start=1,
                        new_count=2,
                        lines=[
                            ContextLine(kind="add", old_line=None, new_line=1, content="import subprocess"),
                            ContextLine(kind="add", old_line=None, new_line=2, content="eval(x)"),
                        ],
                    )
                ],
            )
        ]
    )


class TestBuildSecurityPrompt:
    def test_includes_pr_metadata(self) -> None:
        prompt = build_security_prompt(_context(), [_finding()], owner="octocat", repo="hello-world", pr_number=7)
        assert "octocat/hello-world#7" in prompt

    def test_includes_each_finding(self) -> None:
        findings = [
            _finding(rule_id="r1", severity="high", file="a.py", line=1, message="m1", evidence="e1"),
            _finding(rule_id="r2", severity="low", file="b.py", line=2, message="m2", evidence="e2"),
        ]
        prompt = build_security_prompt(None, findings)
        for finding in findings:
            assert finding.rule_id in prompt
            assert finding.severity in prompt
            assert finding.file in prompt
            assert str(finding.line) in prompt
            assert finding.message in prompt
            assert finding.evidence in prompt

    def test_includes_context_render(self) -> None:
        prompt = build_security_prompt(_context(), [_finding()])
        assert "=== src/app.py (modified) ===" in prompt
        assert "import subprocess" in prompt

    def test_no_context_renders_placeholder(self) -> None:
        prompt = build_security_prompt(None, [_finding()])
        assert "(no context)" in prompt

    def test_empty_findings_lists_none(self) -> None:
        prompt = build_security_prompt(_context(), [])
        assert "(none)" in prompt

    def test_instructions_are_present(self) -> None:
        prompt = build_security_prompt(_context(), [_finding()])
        assert "findings" in prompt
        assert "Never invent a finding" in prompt
        assert "high, medium, low" in prompt
        assert "between 0 and 1" in prompt

    def test_findings_order_preserved(self) -> None:
        prompt = build_security_prompt(None, [_finding(rule_id="first"), _finding(rule_id="second")])
        assert prompt.index("first") < prompt.index("second")

    def test_deterministic(self) -> None:
        context = _context()
        findings = [_finding(), _finding(rule_id="r2")]
        assert build_security_prompt(context, findings, "o", "r", 1) == build_security_prompt(
            context, findings, "o", "r", 1
        )

    def test_returns_bounded_string(self) -> None:
        prompt = build_security_prompt(_context(), [_finding()])
        assert isinstance(prompt, str)
        assert len(prompt) > 0