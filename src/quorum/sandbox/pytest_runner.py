"""pytest execution inside the Docker sandbox (Phase 11).

Runs ``pytest`` in a hardened container against a pre-assembled workspace,
returning the same :class:`SandboxResult` as :func:`run_in_sandbox`. Test
paths are shell-quoted so untrusted filenames cannot inject commands into the
container.
"""

import shlex
from pathlib import Path

from quorum.sandbox.runner import SandboxResult, run_in_sandbox
from quorum.sandbox.spec import SandboxConfig


def run_pytest_in_sandbox(
    workspace_dir: str | Path,
    test_paths: list[str] | None = None,
    config: SandboxConfig | None = None,
) -> SandboxResult:
    """Run ``pytest -q`` over ``test_paths`` inside the sandbox.

    With no ``test_paths`` the whole workspace is collected. ``config``
    defaults to the application settings. This is the interface the Test
    Writer agent (Phase 12) calls with generated test files.
    """
    parts = ["pytest", "-q", "-p", "no:cacheprovider"]
    if test_paths:
        parts.extend(shlex.quote(path) for path in test_paths)
    return run_in_sandbox(config, workspace_dir, " ".join(parts))