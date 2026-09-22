import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from quorum.sandbox import SandboxConfig, run_in_sandbox
from quorum.sandbox.pytest_runner import run_pytest_in_sandbox
from quorum.sandbox.workspace import write_generated_test

pytestmark = pytest.mark.skipif(
    os.getenv("SANDBOX_LIVE_TESTS") != "1",
    reason="set SANDBOX_LIVE_TESTS=1 and build the sandbox image to run",
)


def _workspace(files: dict[str, str]) -> str:
    ws = tempfile.mkdtemp(prefix="q-live-")
    for path, content in files.items():
        target = Path(ws) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return ws


def _leftover_containers() -> list[str]:
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=quorum-sandbox-",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


class TestValidTest:
    def test_valid_pytest_passes(self) -> None:
        ws = _workspace(
            {
                "app.py": "def add(a, b):\n    return a + b\n",
                "test_app.py": (
                    "from app import add\n"
                    "def test_add():\n"
                    "    assert add(1, 2) == 3\n"
                ),
            }
        )
        result = run_in_sandbox(
            SandboxConfig(timeout_seconds=60), ws, "pytest -q -p no:cacheprovider"
        )
        assert result.timed_out is False
        assert result.return_code == 0
        assert "1 passed" in result.stdout


class TestInfiniteLoop:
    def test_infinite_loop_is_terminated(self) -> None:
        ws = _workspace(
            {
                "test_hang.py": "def test_infinite():\n    while True:\n        pass\n"
            }
        )
        result = run_in_sandbox(
            SandboxConfig(timeout_seconds=10), ws, "pytest -q -p no:cacheprovider"
        )
        assert result.timed_out is True
        assert result.return_code == -1
        assert "timed out" in result.stderr


class TestNetworkIsolated:
    def test_external_network_is_unreachable(self) -> None:
        ws = _workspace(
            {
                "test_net.py": (
                    "import socket\n"
                    "import pytest\n"
                    "def test_no_external_network():\n"
                    "    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                    "    sock.settimeout(5)\n"
                    "    with pytest.raises(OSError):\n"
                    "        sock.connect((\"1.1.1.1\", 53))\n"
                )
            }
        )
        result = run_in_sandbox(
            SandboxConfig(timeout_seconds=60), ws, "pytest -q -p no:cacheprovider"
        )
        assert result.timed_out is False
        assert result.return_code == 0
        assert "1 passed" in result.stdout


class TestMemoryLimit:
    def test_memory_hog_is_killed(self) -> None:
        ws = _workspace({})
        result = run_in_sandbox(
            SandboxConfig(memory_limit="64m", timeout_seconds=60),
            ws,
            'python -c "x = [0] * (10**8)"',
        )
        assert result.timed_out is False
        assert result.return_code == 137


class TestCleanup:
    def test_no_containers_left_after_terminations(self) -> None:
        ws = _workspace({})
        run_in_sandbox(SandboxConfig(timeout_seconds=5), ws, "sleep 60")
        run_in_sandbox(
            SandboxConfig(memory_limit="64m", timeout_seconds=60),
            ws,
            'python -c "x = [0] * (10**8)"',
        )
        assert _leftover_containers() == []


class TestPytestPrimitive:
    def test_runs_generated_test_end_to_end(self) -> None:
        ws = _workspace(
            {"app.py": "def add(a, b):\n    return a + b\n"}
        )
        write_generated_test(
            ws,
            "test_gen.py",
            "from app import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        )
        result = run_pytest_in_sandbox(
            ws, ["test_gen.py"], SandboxConfig(timeout_seconds=60)
        )
        assert result.timed_out is False
        assert result.return_code == 0
        assert "1 passed" in result.stdout