import shlex
from pathlib import Path
from unittest.mock import patch

import pytest

from quorum.sandbox.pytest_runner import run_pytest_in_sandbox
from quorum.sandbox.runner import SandboxResult
from quorum.sandbox.spec import SandboxConfig


def _result() -> SandboxResult:
    return SandboxResult(return_code=0, stdout="1 passed", stderr="", duration_seconds=1.0)


class TestRunPytestInSandbox:
    def test_builds_pytest_command(self) -> None:
        with patch(
            "quorum.sandbox.pytest_runner.run_in_sandbox",
            return_value=_result(),
        ) as mock_run:
            run_pytest_in_sandbox("C:/ws", ["test_a.py", "test_b.py"])

        ws, command = mock_run.call_args.args[1:]
        assert ws == "C:/ws"
        assert command == "pytest -q -p no:cacheprovider test_a.py test_b.py"

    def test_collects_whole_workspace_when_no_paths(self) -> None:
        with patch(
            "quorum.sandbox.pytest_runner.run_in_sandbox",
            return_value=_result(),
        ) as mock_run:
            run_pytest_in_sandbox("C:/ws")

        assert mock_run.call_args.args[2] == "pytest -q -p no:cacheprovider"

    def test_quotes_untrusted_test_paths(self) -> None:
        with patch(
            "quorum.sandbox.pytest_runner.run_in_sandbox",
            return_value=_result(),
        ) as mock_run:
            run_pytest_in_sandbox("C:/ws", ["x; rm -rf /"])

        command = mock_run.call_args.args[2]
        assert command == (
            "pytest -q -p no:cacheprovider " + shlex.quote("x; rm -rf /")
        )

    def test_passes_config_through(self) -> None:
        config = SandboxConfig(memory_limit="128m")
        with patch(
            "quorum.sandbox.pytest_runner.run_in_sandbox",
            return_value=_result(),
        ) as mock_run:
            run_pytest_in_sandbox("C:/ws", ["test_a.py"], config)

        assert mock_run.call_args.args[0] is config