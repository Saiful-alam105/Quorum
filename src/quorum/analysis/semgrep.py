"""Semgrep security analysis: finding contract, JSON parsing, scanning, and
scan-directory assembly (Phase 8).

This module converts Semgrep ``--json`` output into structured
:class:`SemgrepFinding` records, runs the Semgrep CLI, and builds the
temporary scan directory from a pull request's changed files. The parser is
intentionally pure so later phases (Security Agent, dashboard) consume the
same structure and the LLM can never invent a finding — every finding maps
back to real Semgrep evidence.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Awaitable, Callable

from quorum.analysis.diff import (
    STATUS_ADDED,
    STATUS_MODIFIED,
    STATUS_RENAMED,
    ChangedFile,
)
from quorum.config import settings

_SCANNABLE_STATUSES = {STATUS_ADDED, STATUS_MODIFIED, STATUS_RENAMED}

_SEVERITY_MAP = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}

_CONFIDENCE_MAP = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}


class SemgrepParseError(Exception):
    """Raised when Semgrep JSON output cannot be parsed."""


class SemgrepError(Exception):
    """Raised when the Semgrep CLI cannot run successfully."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


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


def run_semgrep(
    scan_dir: str | Path,
    ruleset: str | None = None,
    timeout_seconds: int | None = None,
) -> str:
    """Run ``semgrep scan --json`` over ``scan_dir`` and return raw JSON text.

    Missing binary, timeout, and non-zero exit codes raise
    :class:`SemgrepError`. The ruleset and timeout default to the configured
    values.
    """
    resolved_ruleset = settings.semgrep_ruleset if ruleset is None else ruleset
    resolved_timeout = (
        settings.semgrep_timeout_seconds if timeout_seconds is None else timeout_seconds
    )
    command = [
        "semgrep",
        "scan",
        "--json",
        "--config",
        resolved_ruleset,
        str(scan_dir),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=resolved_timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SemgrepError("semgrep executable not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise SemgrepError(
            f"semgrep scan timed out after {resolved_timeout}s"
        ) from exc
    if result.returncode != 0:
        raise SemgrepError(
            result.stderr.strip() or f"semgrep exited with code {result.returncode}"
        )
    return result.stdout


async def build_scan_directory(
    changed_files: list[ChangedFile],
    fetch_content: Callable[[str, str], Awaitable[str]],
    head_sha: str,
    scan_dir: str | Path,
) -> Path:
    """Write the full contents of scannable changed files into ``scan_dir``.

    Only added, modified, and renamed files are fetched; deleted and binary
    files are skipped. Paths that could escape ``scan_dir`` (absolute paths or
    ``..`` segments) are skipped so a malicious repository cannot write outside
    the temporary directory. The caller owns the directory lifecycle.
    """
    root = Path(scan_dir)
    root.mkdir(parents=True, exist_ok=True)
    for file in changed_files:
        if file.status not in _SCANNABLE_STATUSES:
            continue
        if _unsafe_path(file.path):
            continue
        content = await fetch_content(file.path, head_sha)
        target = root / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def _unsafe_path(path: str) -> bool:
    pure = PurePath(path)
    if pure.is_absolute():
        return True
    return any(segment == ".." for segment in pure.parts)