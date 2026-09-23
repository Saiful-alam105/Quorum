"""Sandbox test execution and result parsing (Phase 12).

Runs ``pytest -v`` in the Phase 11 Docker sandbox and parses the per-test
``PASSED``/``FAILED``/``ERROR``/``SKIPPED`` lines into :class:`TestOutcome`
records. This is the interface the Test Writer stage calls after writing
generated tests into the workspace.
"""

import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

from quorum.sandbox.runner import SandboxResult, run_in_sandbox
from quorum.sandbox.spec import SandboxConfig

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_ERROR = "error"
STATUS_SKIPPED = "skipped"

_STATUS_MAP = {
    "PASSED": STATUS_PASSED,
    "XPASS": STATUS_PASSED,
    "FAILED": STATUS_FAILED,
    "XFAIL": STATUS_FAILED,
    "ERROR": STATUS_ERROR,
    "SKIPPED": STATUS_SKIPPED,
}

_LINE_RE = re.compile(
    r"(?P<name>\S+::\S+)\s+(?P<result>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b"
)

_TOTAL_RE = re.compile(r"^TOTAL\b.*?(\d+)%", re.MULTILINE)


@dataclass
class TestOutcome:
    """The result of a single generated test."""

    __test__ = False

    name: str
    status: str


@dataclass
class TestExecution:
    """The sandbox run plus its parsed per-test outcomes."""

    __test__ = False

    outcomes: list[TestOutcome] = field(default_factory=list)
    timed_out: bool = False
    return_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0


def _build_command(test_paths: list[str] | None) -> str:
    parts = ["pytest", "-v", "-p", "no:cacheprovider"]
    if test_paths:
        parts.extend(shlex.quote(path) for path in test_paths)
    return " ".join(parts)


def _parse_outcomes(stdout: str) -> list[TestOutcome]:
    outcomes: list[TestOutcome] = []
    for line in stdout.splitlines():
        match = _LINE_RE.search(line)
        if match:
            outcomes.append(
                TestOutcome(
                    name=match.group("name"),
                    status=_STATUS_MAP[match.group("result")],
                )
            )
    return outcomes


def run_tests_in_sandbox(
    workspace_dir: str | Path,
    test_paths: list[str] | None = None,
    config: SandboxConfig | None = None,
) -> TestExecution:
    """Run ``pytest -v`` over ``test_paths`` and parse the results.

    ``config`` defaults to the application settings. A sandbox timeout is
    propagated as ``timed_out=True`` while any already-printed per-test lines
    are still parsed.
    """
    result: SandboxResult = run_in_sandbox(
        config, workspace_dir, _build_command(test_paths)
    )
    return TestExecution(
        outcomes=_parse_outcomes(result.stdout),
        timed_out=result.timed_out,
        return_code=result.return_code,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_seconds=result.duration_seconds,
    )


def _coverage_command(test_paths: list[str] | None) -> str:
    parts = [
        "COVERAGE_FILE=/tmp/.coverage",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--cov=/workspace",
        "--cov-report=term",
    ]
    if test_paths:
        parts.extend(shlex.quote(path) for path in test_paths)
    return " ".join(parts)


def measure_coverage(
    workspace_dir: str | Path,
    test_paths: list[str] | None = None,
    config: SandboxConfig | None = None,
) -> float:
    """Measure total workspace coverage via ``pytest --cov`` in the sandbox.

    Returns the ``TOTAL`` percentage from the term report, or ``0.0`` when no
    coverage data was produced (for example no tests collected).
    """
    result = run_in_sandbox(config, workspace_dir, _coverage_command(test_paths))
    match = _TOTAL_RE.search(result.stdout)
    if match is None:
        return 0.0
    return float(match.group(1))


def compute_coverage_delta(before: float, after: float) -> float:
    """Return the coverage delta (after - before), rounded to two decimals."""
    return round(after - before, 2)