import pytest

from quorum.agents.test_runner import compute_coverage_delta, measure_coverage
from quorum.sandbox.runner import SandboxResult


def _result(stdout: str) -> SandboxResult:
    return SandboxResult(
        return_code=0, stdout=stdout, stderr="", duration_seconds=1.0
    )


COVERAGE_WITH_MISS = """Name      Stmts   Miss  Cover
-------------------------------
app.py         4      1    75%
-------------------------------
TOTAL          4      1    75%
"""

COVERAGE_NO_MISS = """Name      Stmts   Cover
--------------------------
app.py         4    100%
--------------------------
TOTAL          4    100%
"""


class TestMeasureCoverage:
    def test_parses_total_with_miss_column(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result(COVERAGE_WITH_MISS),
        )
        assert measure_coverage("ws", test_paths=["test_app.py"]) == 75.0

    def test_parses_total_without_miss_column(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result(COVERAGE_NO_MISS),
        )
        assert measure_coverage("ws") == 100.0

    def test_no_total_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "quorum.agents.test_runner.run_in_sandbox",
            lambda config, ws, cmd: _result("no tests ran\n"),
        )
        assert measure_coverage("ws") == 0.0

    def test_command_uses_cov(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict = {}

        def fake_run(config, workspace_dir, command):
            captured["command"] = command
            return _result(COVERAGE_NO_MISS)

        monkeypatch.setattr("quorum.agents.test_runner.run_in_sandbox", fake_run)
        measure_coverage("ws", test_paths=["test_app.py"])
        command = captured["command"]
        assert "COVERAGE_FILE=/tmp/.coverage" in command
        assert "--cov=/workspace" in command
        assert "--cov-report=term" in command
        assert "test_app.py" in command


class TestComputeCoverageDelta:
    def test_delta(self) -> None:
        assert compute_coverage_delta(72.0, 81.0) == 9.0

    def test_negative_delta(self) -> None:
        assert compute_coverage_delta(50.0, 40.0) == -10.0

    def test_zero_delta(self) -> None:
        assert compute_coverage_delta(0.0, 0.0) == 0.0

    def test_rounds(self) -> None:
        assert compute_coverage_delta(10.0, 15.123) == 5.12