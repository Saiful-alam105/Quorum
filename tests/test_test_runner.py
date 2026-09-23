import pytest

from quorum.agents.test_runner import (
    STATUS_ERROR,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
    run_tests_in_sandbox,
)
from quorum.sandbox.runner import SandboxResult


def _result(
    stdout: str,
    return_code: int = 0,
    timed_out: bool = False,
    stderr: str = "",
) -> SandboxResult:
    return SandboxResult(
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=1.25,
        timed_out=timed_out,
    )


STDOUT = (
    "tests/test_alpha.py::test_one PASSED\n"
    "tests/test_alpha.py::test_two FAILED\n"
    "tests/test_beta.py::test_three ERROR\n"
    "tests/test_beta.py::test_four SKIPPED\n"
)


class TestParseOutcomes:
    def test_parses_each_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result(STDOUT, return_code=1),
        )
        execution = run_tests_in_sandbox("ws", test_paths=["tests/test_alpha.py"])
        statuses = {o.name: o.status for o in execution.outcomes}
        assert statuses == {
            "tests/test_alpha.py::test_one": STATUS_PASSED,
            "tests/test_alpha.py::test_two": STATUS_FAILED,
            "tests/test_beta.py::test_three": STATUS_ERROR,
            "tests/test_beta.py::test_four": STATUS_SKIPPED,
        }
        assert execution.return_code == 1

    def test_ignores_summary_lines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        stdout = (
            "tests/test_alpha.py::test_one PASSED\n"
            "=== short test summary info ===\n"
            "FAILED tests/test_alpha.py::test_one - assertion\n"
        )
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result(stdout),
        )
        execution = run_tests_in_sandbox("ws")
        assert len(execution.outcomes) == 1

    def test_empty_stdout_no_outcomes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result(""),
        )
        assert run_tests_in_sandbox("ws").outcomes == []

    def test_timeout_propagated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result(
                "tests/test_alpha.py::test_one PASSED\n", timed_out=True, return_code=-1
            ),
        )
        execution = run_tests_in_sandbox("ws")
        assert execution.timed_out is True
        assert len(execution.outcomes) == 1


class TestCommand:
    def test_verbose_pytest_with_quoted_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict = {}

        def fake_run_in_sandbox(config, workspace_dir, command):
            captured["command"] = command
            return _result("")

        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox", fake_run_in_sandbox
        )
        run_tests_in_sandbox("ws", test_paths=["tests/test_a.py", "tests/test b.py"])
        command = captured["command"]
        assert command.startswith("pytest -v -p no:cacheprovider")
        assert "tests/test_a.py" in command
        assert "tests/test b.py" in command

    def test_no_test_paths_means_whole_workspace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict = {}

        def fake_run_in_sandbox(config, workspace_dir, command):
            captured["command"] = command
            return _result("")

        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox", fake_run_in_sandbox
        )
        run_tests_in_sandbox("ws")
        assert captured["command"] == "pytest -v -p no:cacheprovider"