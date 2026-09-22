"""Docker sandbox package (Phase 11): hardened execution of generated tests
and untrusted repository code inside a temporary container."""

from quorum.sandbox.runner import SandboxError, SandboxResult, run_in_sandbox
from quorum.sandbox.spec import (
    SandboxConfig,
    build_docker_run_command,
    build_sandbox_config,
)

__all__ = [
    "SandboxConfig",
    "SandboxError",
    "SandboxResult",
    "build_docker_run_command",
    "build_sandbox_config",
    "run_in_sandbox",
]