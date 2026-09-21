"""Semgrep security analysis: finding contract and JSON parsing (Phase 8).

This module converts Semgrep ``--json`` output into structured
:class:`SemgrepFinding` records. The parser is intentionally pure (no network,
no subprocess, no database) so later phases (Security Agent, dashboard) consume
the same structure and the LLM can never invent a finding — every finding maps
back to real Semgrep evidence. The Semgrep CLI runner and the scan-directory
assembly are added in later chunks of this phase.
"""

import json
from dataclasses import dataclass

_SEVERITY_MAP = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}

_CONFIDENCE_MAP = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}


class SemgrepParseError(Exception):
    """Raised when Semgrep JSON output cannot be parsed."""


@dataclass
class SemgrepFinding:
    """A single Semgrep finding mapped to the Quorum security model."""

    rule_id: str
    severity: str
    file: str
    line: int
    message: str
    evidence: str
    confidence: float | None = None


def _map_severity(value: object) -> str:
    if isinstance(value, str):
        return _SEVERITY_MAP.get(value.upper(), "low")
    return "low"


def _map_confidence(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return _CONFIDENCE_MAP.get(value.upper())
    return None


def _strip_prefix(path: str, path_prefix: str) -> str:
    if not path_prefix:
        return path
    prefix = path_prefix.rstrip("/\\")
    if prefix and path.startswith(prefix):
        return path[len(prefix):].lstrip("/\\")
    return path


def parse_semgrep_json(raw: str, path_prefix: str = "") -> list[SemgrepFinding]:
    """Parse Semgrep ``--json`` output into a list of findings.

    Entries missing a rule id, path, or line number are skipped. Empty results
    produce an empty list. Malformed JSON or a non-object root raises
    :class:`SemgrepParseError`.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SemgrepParseError("semgrep output is not valid JSON") from exc
    if not isinstance(data, dict):
        raise SemgrepParseError("semgrep output is not a JSON object")

    results = data.get("results", [])
    if not isinstance(results, list):
        raise SemgrepParseError("semgrep output has no results list")

    findings: list[SemgrepFinding] = []
    for entry in results:
        if not isinstance(entry, dict):
            continue
        rule_id = entry.get("check_id")
        path = entry.get("path")
        start = entry.get("start") if isinstance(entry.get("start"), dict) else {}
        line = start.get("line")
        if not rule_id or not path or not isinstance(line, int):
            continue

        extra = entry.get("extra") if isinstance(entry.get("extra"), dict) else {}
        findings.append(
            SemgrepFinding(
                rule_id=rule_id,
                severity=_map_severity(extra.get("severity")),
                file=_strip_prefix(path, path_prefix),
                line=line,
                message=extra.get("message") or "",
                evidence=extra.get("lines") or "",
                confidence=_map_confidence(
                    (extra.get("metadata") or {}).get("confidence")
                    if isinstance(extra.get("metadata"), dict)
                    else None
                ),
            )
        )
    return findings