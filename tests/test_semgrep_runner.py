import subprocess
from unittest.mock import patch

import pytest

from quorum.analysis.semgrep import SemgrepError, run_semgrep
from quorum.config import settings


def _completed(returncode: int = 0, stdout: str = "{}", stderr: str = ""):
    return subprocess.CompletedProcess(
        ["semgrep"], returncode, stdout=stdout, stderr=stderr
    )


class TestRunSemgrep:
    def test_returns_stdout_on_success(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            return_value=_completed(stdout='{"results": []}'),
        ):
            assert (
                run_semgrep(
                    "C:/tmp/scan", ruleset="p/security-audit", timeout_seconds=120
                )
                == '{"results": []}'
            )

    def test_non_zero_exit_raises_with_stderr(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            return_value=_completed(returncode=2, stderr="scan failed"),
        ):
            with pytest.raises(SemgrepError, match="scan failed"):
                run_semgrep(
                    "C:/tmp/scan", ruleset="p/security-audit", timeout_seconds=120
                )

    def test_non_zero_exit_without_stderr_raises(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            return_value=_completed(returncode=2, stderr=""),
        ):
            with pytest.raises(SemgrepError, match="exited with code 2"):
                run_semgrep(
                    "C:/tmp/scan", ruleset="p/security-audit", timeout_seconds=120
                )

    def test_missing_binary_raises(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with pytest.raises(SemgrepError, match="not found"):
                run_semgrep(
                    "C:/tmp/scan", ruleset="p/security-audit", timeout_seconds=120
                )

    def test_timeout_raises(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            side_effect=subprocess.TimeoutExpired("semgrep", 120),
        ):
            with pytest.raises(SemgrepError, match="timed out after 120s"):
                run_semgrep(
                    "C:/tmp/scan", ruleset="p/security-audit", timeout_seconds=120
                )

    def test_command_args_and_timeout(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            run_semgrep(
                "C:/tmp/scan", ruleset="p/python", timeout_seconds=60
            )
        call = mock_run.call_args
        command = call.args[0]
        assert command == [
            "semgrep",
            "scan",
            "--json",
            "--config",
            "p/python",
            "C:/tmp/scan",
        ]
        assert call.kwargs["timeout"] == 60
        assert call.kwargs["capture_output"] is True
        assert call.kwargs["text"] is True

    def test_defaults_from_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "semgrep_ruleset", "p/custom")
        monkeypatch.setattr(settings, "semgrep_timeout_seconds", 30)
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            run_semgrep("C:/tmp/scan")
        call = mock_run.call_args
        command = call.args[0]
        assert command[4] == "p/custom"
        assert call.kwargs["timeout"] == 30

    def test_multiple_configs_become_separate_flags(self) -> None:
        with patch(
            "quorum.analysis.semgrep.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            run_semgrep(
                "C:/tmp/scan",
                ruleset="p/security-audit p/owasp-top-ten",
                timeout_seconds=60,
            )
        command = mock_run.call_args.args[0]
        assert command == [
            "semgrep",
            "scan",
            "--json",
            "--config",
            "p/security-audit",
            "--config",
            "p/owasp-top-ten",
            "C:/tmp/scan",
        ]