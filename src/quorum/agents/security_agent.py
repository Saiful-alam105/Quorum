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