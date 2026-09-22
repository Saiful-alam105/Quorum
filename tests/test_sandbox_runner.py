import subprocess
from unittest.mock import patch

import pytest

from quorum.sandbox.runner import SandboxError, _cleanup_container, run_in_sandbox
from quorum.sandbox.spec import SandboxConfig


def _completed(
    returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        ["docker", "run"], returncode, stdout=stdout, stderr=stderr
    )


def _name_from(argv: list[str]) -> str:
    return argv[argv.index("--name") + 1]


class TestRunInSandbox:
    def test_success_returns_result_with_unique_container(self) -> None:
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            return_value=_completed(stdout="ok"),
        ) as mock_run:
            result = run_in_sandbox(None, "C:/ws", "true")

        assert result.return_code == 0
        assert result.stdout == "ok"
        assert result.timed_out is False
        assert result.duration_seconds >= 0
        argv = mock_run.call_args.args[0]
        assert _name_from(argv).startswith("quorum-sandbox-")
        assert mock_run.call_args.kwargs["timeout"] == 60

    def test_explicit_config_is_used(self) -> None:
        config = SandboxConfig(image="custom:v1", memory_limit="512m")
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            run_in_sandbox(config, "C:/ws", "true")

        argv = mock_run.call_args.args[0]
        assert "custom:v1" in argv
        assert argv[argv.index("--memory") + 1] == "512m"

    def test_container_names_are_unique_across_runs(self) -> None:
        names: list[str] = []
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            run_in_sandbox(None, "C:/ws", "true")
            names.append(_name_from(mock_run.call_args.args[0]))
            run_in_sandbox(None, "C:/ws", "true")
            names.append(_name_from(mock_run.call_args.args[0]))

        assert len(set(names)) == 2

    def test_nonzero_exit_is_a_result_not_an_error(self) -> None:
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            return_value=_completed(returncode=2, stderr="tests failed"),
        ):
            result = run_in_sandbox(None, "C:/ws", "pytest -q")

        assert result.return_code == 2
        assert result.stderr == "tests failed"
        assert result.timed_out is False

    def test_missing_docker_raises(self) -> None:
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with pytest.raises(SandboxError, match="not found"):
                run_in_sandbox(None, "C:/ws", "true")

    def test_daemon_error_raises(self) -> None:
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            return_value=_completed(returncode=125, stderr="image not found"),
        ):
            with pytest.raises(SandboxError, match="image not found"):
                run_in_sandbox(None, "C:/ws", "true")

    def test_timeout_kills_and_removes_container(self) -> None:
        calls: list[list[str]] = []

        def fake_run(argv, **kwargs):
            calls.append(argv)
            if len(calls) == 1:
                raise subprocess.TimeoutExpired(
                    argv, 60, output="partial", stderr="hung"
                )
            return _completed()

        with patch(
            "quorum.sandbox.runner.subprocess.run", side_effect=fake_run
        ):
            result = run_in_sandbox(None, "C:/ws", "while true; do :; done")

        name = _name_from(calls[0])
        assert result.timed_out is True
        assert result.return_code == -1
        assert "partial" in result.stdout
        assert "timed out" in result.stderr
        assert calls[1] == ["docker", "kill", name]
        assert calls[2] == ["docker", "rm", "-f", name]


class TestCleanupContainer:
    def test_kills_and_removes(self) -> None:
        calls: list[list[str]] = []
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            _cleanup_container("sandbox-1")

        calls = [mock_run.call_args_list[0].args[0], mock_run.call_args_list[1].args[0]]
        assert calls[0] == ["docker", "kill", "sandbox-1"]
        assert calls[1] == ["docker", "rm", "-f", "sandbox-1"]

    def test_missing_docker_is_swallowed(self) -> None:
        with patch(
            "quorum.sandbox.runner.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            _cleanup_container("sandbox-1")