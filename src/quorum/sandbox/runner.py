"""Sandbox runner (Phase 11): execute a command inside a hardened Docker
container with a hard timeout and guaranteed container cleanup.

Runs the ``docker run`` command produced by :func:`build_docker_run_command`
and normalizes the outcome into a :class:`SandboxResult`. A hard timeout
terminates the container with ``docker kill`` + ``docker rm -f`` so no
container can leak. Docker-level failures raise :class:`SandboxError`; the
container's own non-zero exit code is a normal result.
"""

import logging
import subprocess
import time
import uuid
from dataclasses import replace
from pathlib import Path

from quorum.sandbox.spec import SandboxConfig, build_docker_run_command, build_sandbox_config

logger = logging.getLogger(__name__)

_DOCKER_DAEMON_ERROR = 125


class SandboxError(Exception):
    """Raised when the sandbox cannot run (docker missing or daemon error)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SandboxResult:
    """Outcome of one sandboxed command execution."""

    def __init__(
        self,
        return_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        timed_out: bool = False,
    ) -> None:
        self.return_code = return_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_seconds = duration_seconds
        self.timed_out = timed_out


def _unique_container_name() -> str:
    return f"quorum-sandbox-{uuid.uuid4().hex[:12]}"


def _cleanup_container(container_name: str) -> None:
    """Kill and remove ``container_name``, ignoring any cleanup failures."""
    for command in (["docker", "kill", container_name], ["docker", "rm", "-f", container_name]):
        try:
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            logger.warning("docker not found while cleaning up %s", container_name)


def run_in_sandbox(
    config: SandboxConfig | None,
    workspace_path: str | Path,
    command: str,
) -> SandboxResult:
    """Run ``command`` inside a fresh hardened Docker container.

    ``config`` defaults to the application settings. The workspace directory
    is mounted read-only and the command runs in the container's working
    directory. A hard timeout returns ``timed_out=True`` after the container
    is killed and removed. Raises :class:`SandboxError` when the docker binary
    is missing or the Docker daemon reports an error (exit code 125).
    """
    base = build_sandbox_config() if config is None else config
    resolved = replace(base, container_name=_unique_container_name())
    argv = build_docker_run_command(resolved, workspace_path, command)
    started = time.monotonic()
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=resolved.timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SandboxError("docker executable not found") from exc
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        _cleanup_container(resolved.container_name)
        logger.warning(
            "sandbox %s timed out after %ss; container removed",
            resolved.container_name,
            resolved.timeout_seconds,
        )
        return SandboxResult(
            return_code=-1,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + "\nsandbox execution timed out",
            duration_seconds=duration,
            timed_out=True,
        )

    duration = time.monotonic() - started
    if result.returncode == _DOCKER_DAEMON_ERROR:
        raise SandboxError(result.stderr.strip() or "docker daemon error")
    return SandboxResult(
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_seconds=duration,
    )