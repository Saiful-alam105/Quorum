"""Sandbox image build helper (Phase 11).

Builds the ``quorum-sandbox`` image (Python + pytest + pytest-cov, non-root
user) from the checked-in ``docker/quorum-sandbox.Dockerfile``. The image is
pre-built so the runtime container can run with ``--network none`` and
``--read-only`` without needing pip access.
"""

import logging
import subprocess
from pathlib import Path

from quorum.config import settings

logger = logging.getLogger(__name__)


class SandboxImageError(Exception):
    """Raised when the sandbox image cannot be built."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _dockerfile_path() -> Path:
    return Path(__file__).resolve().parents[3] / "docker" / "quorum-sandbox.Dockerfile"


def build_image(tag: str | None = None) -> None:
    """Build the sandbox image.

    ``tag`` defaults to ``settings.sandbox_image``. Raises
    :class:`SandboxImageError` if docker is missing or the build fails.
    """
    resolved_tag = settings.sandbox_image if tag is None else tag
    dockerfile = _dockerfile_path()
    command = [
        "docker",
        "build",
        "-t",
        resolved_tag,
        "-f",
        str(dockerfile),
        str(dockerfile.parent),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except FileNotFoundError as exc:
        raise SandboxImageError("docker executable not found") from exc
    if result.returncode != 0:
        raise SandboxImageError(
            result.stderr.strip()
            or f"docker build exited with code {result.returncode}"
        )
    logger.info("built sandbox image %s", resolved_tag)