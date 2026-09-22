from dataclasses import FrozenInstanceError

import pytest

from quorum.config import settings
from quorum.sandbox.spec import SandboxConfig, build_sandbox_config


class TestSandboxConfigDefaults:
    def test_defaults(self) -> None:
        config = SandboxConfig()
        assert config.image == "quorum-sandbox:latest"
        assert config.timeout_seconds == 60
        assert config.memory_limit == "256m"
        assert config.pids_limit == 256
        assert config.tmpfs_size == "64m"
        assert config.workdir == "/workspace"
        assert config.network == "none"
        assert config.user == "1000:1000"
        assert config.container_name is None

    def test_is_frozen(self) -> None:
        config = SandboxConfig()
        with pytest.raises(FrozenInstanceError):
            config.image = "other"


class TestBuildSandboxConfig:
    def test_maps_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "sandbox_image", "my-image:v1")
        monkeypatch.setattr(settings, "sandbox_timeout_seconds", 30)
        monkeypatch.setattr(settings, "sandbox_memory_limit", "128m")
        monkeypatch.setattr(settings, "sandbox_pids_limit", 64)
        monkeypatch.setattr(settings, "sandbox_tmpfs_size", "32m")
        monkeypatch.setattr(settings, "sandbox_workdir", "/src")

        config = build_sandbox_config()

        assert config.image == "my-image:v1"
        assert config.timeout_seconds == 30
        assert config.memory_limit == "128m"
        assert config.pids_limit == 64
        assert config.tmpfs_size == "32m"
        assert config.workdir == "/src"