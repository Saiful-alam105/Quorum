"""Sandbox configuration and Docker run-command construction (Phase 11).

The command builder is intentionally pure: given a :class:`SandboxConfig` it
produces the exact ``docker run`` argument list that enforces the Phase 11
security requirements (no network, memory limit, process limit, temporary
filesystem, non-privileged execution, read-only root, container cleanup).
"""

from dataclasses import dataclass
from pathlib import Path

from quorum.config import settings


@dataclass(frozen=True)
class SandboxConfig:
    """Resource limits and runtime flags for one sandboxed execution."""

    image: str = "quorum-sandbox:latest"
    timeout_seconds: int = 60
    memory_limit: str = "256m"
    pids_limit: int = 256
    tmpfs_size: str = "64m"
    workdir: str = "/workspace"
    network: str = "none"
    user: str = "1000:1000"
    container_name: str | None = None


def build_sandbox_config() -> SandboxConfig:
    """Build a :class:`SandboxConfig` from the application settings."""
    return SandboxConfig(
        image=settings.sandbox_image,
        timeout_seconds=settings.sandbox_timeout_seconds,
        memory_limit=settings.sandbox_memory_limit,
        pids_limit=settings.sandbox_pids_limit,
        tmpfs_size=settings.sandbox_tmpfs_size,
        workdir=settings.sandbox_workdir,
    )


def _mount_source(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def build_docker_run_command(
    config: SandboxConfig,
    workspace_path: str | Path,
    command: str,
) -> list[str]:
    """Build the ``docker run`` argv enforcing every Phase 11 constraint.

    The workspace directory is mounted read-only at ``config.workdir`` and the
    container root filesystem is read-only, so all writes land in the tmpfs
    ``/tmp``. ``--rm`` guarantees the container is removed on exit.
    """
    argv = ["docker", "run", "--rm"]
    if config.container_name:
        argv += ["--name", config.container_name]
    argv += [
        "--network",
        config.network,
        "--memory",
        config.memory_limit,
        "--memory-swap",
        config.memory_limit,
        "--pids-limit",
        str(config.pids_limit),
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        config.user,
        "--read-only",
        "--tmpfs",
        f"/tmp:rw,size={config.tmpfs_size}",
        "--volume",
        f"{_mount_source(workspace_path)}:{config.workdir}:ro",
        "--workdir",
        config.workdir,
        config.image,
        "sh",
        "-c",
        command,
    ]
    return argv