"""Security Review Agent: structured output contract and LLM output validation.

Phase 10 agent. This module defines the Pydantic schema the Security Agent's
LLM output must satisfy and the parser that turns raw LLM text into a valid
:class:`SecurityAgentReview`. LLM output is untrusted: it is validated against
this strict schema before anything else consumes it. The prompt builder and
the agent itself are added in later chunks of this phase.
"""

import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from quorum.analysis.context import PreparedContext
from quorum.analysis.semgrep import SemgrepFinding

SEVERITY_VALUES: tuple[str, ...] = ("high", "medium", "low")

Severity = Literal["high", "medium", "low"]


class SecurityAgentFinding(BaseModel):
    """A single security finding produced by the agent."""

    severity: Severity
    title: str = Field(min_length=1)
    file: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    rule_id: str = ""
    line: int | None = Field(default=None, ge=1)
    explanation: str | None = None

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class SecurityAgentReview(BaseModel):
    """The structured output of the Security Review Agent."""

    findings: list[SecurityAgentFinding]


class SecurityAgentParseError(Exception):
    """Raised when raw agent output cannot be parsed or validated."""


def parse_security_review(raw: str) -> SecurityAgentReview:
    """Parse and validate raw LLM text into a :class:`SecurityAgentReview`."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SecurityAgentParseError("security review is not valid JSON") from exc
    if not isinstance(data, dict):
        raise SecurityAgentParseError("security review is not a JSON object")

    findings = data.get("findings")
    if findings is None:
        raise SecurityAgentParseError("security review has no findings list")
    if not isinstance(findings, list):
        raise SecurityAgentParseError("security review findings is not a list")

    try:
        return SecurityAgentReview(findings=findings)
    except ValidationError as exc:
        raise SecurityAgentParseError("security review failed validation") from exc


_PROMPT_INSTRUCTIONS = """You are the Quorum Security Review Agent. Analyze the pull request evidence below and report security issues.

Output ONLY strict JSON with this exact shape:
{"findings": [{"severity": "high|medium|low", "title": "...", "file": "...", "line": 42, "evidence": "...", "explanation": "...", "confidence": 0.0}]}

Rules:
- Base every finding on the Semgrep evidence provided. Never invent a finding that is not supported by the evidence.
- Only report issues in the changed files listed in the context.
- Preserve the exact file path and line number from the evidence.
- severity must be one of: high, medium, low.
- confidence must be a number between 0 and 1.
- evidence must quote the exact matched code from the input.
- If there is nothing worth reporting, return {"findings": []}."""


def build_security_prompt(
    prepared_context: PreparedContext | None,
    semgrep_findings: list[SemgrepFinding],
    owner: str = "",
    repo: str = "",
    pr_number: int | None = None,
) -> str:
    """Build a bounded, deterministic security-review prompt from evidence."""
    pr_label = f"{owner}/{repo}#{pr_number}" if pr_number is not None else f"{owner}/{repo}"
    sections = [f"Pull request: {pr_label}", ""]

    sections.append("## Semgrep findings (evidence)")
    if semgrep_findings:
        for finding in semgrep_findings:
            sections.append(
                f"- rule: {finding.rule_id}\n"
                f"  severity: {finding.severity}\n"
                f"  file: {finding.file}\n"
                f"  line: {finding.line}\n"
                f"  message: {finding.message}\n"
                f"  evidence: {finding.evidence}"
            )
    else:
        sections.append("(none)")
    sections.append("")

    sections.append("## Changed code context (bounded)")
    sections.append(
        prepared_context.render_text() if prepared_context is not None else "(no context)"
    )
    sections.append("")
    sections.append(_PROMPT_INSTRUCTIONS)

    return "\n".join(sections)