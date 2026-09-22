import subprocess
from unittest.mock import patch

import pytest

from quorum.config import settings
from quorum.sandbox.image import SandboxImageError, _dockerfile_path, build_image


def _completed(returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        ["docker", "build"], returncode, stdout="", stderr=stderr
    )


class TestBuildImage:
    def test_uses_settings_tag_and_checked_in_dockerfile(self) -> None:
        with patch(
            "quorum.sandbox.image.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            build_image()

        command = mock_run.call_args.args[0]
        assert command[:2] == ["docker", "build"]
        assert command[command.index("-t") + 1] == settings.sandbox_image
        dockerfile = str(_dockerfile_path()).replace("\\", "/")
        assert command[command.index("-f") + 1].replace("\\", "/") == dockerfile
        assert command[-1].replace("\\", "/") == dockerfile.rsplit("/", 1)[0]

    def test_custom_tag_overrides_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "sandbox_image", "default-tag")
        with patch(
            "quorum.sandbox.image.subprocess.run",
            return_value=_completed(),
        ) as mock_run:
            build_image(tag="custom:v2")

        command = mock_run.call_args.args[0]
        assert command[command.index("-t") + 1] == "custom:v2"

    def test_failed_build_raises_with_stderr(self) -> None:
        with patch(
            "quorum.sandbox.image.subprocess.run",
            return_value=_completed(returncode=1, stderr="build failed"),
        ):
            with pytest.raises(SandboxImageError, match="build failed"):
                build_image()

    def test_missing_docker_raises(self) -> None:
        with patch(
            "quorum.sandbox.image.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with pytest.raises(SandboxImageError, match="not found"):
                build_image()