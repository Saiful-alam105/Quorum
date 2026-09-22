from pathlib import Path

from quorum.sandbox.spec import SandboxConfig, build_docker_run_command


def _value(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


class TestBuildDockerRunCommand:
    def test_enforces_all_security_flags(self) -> None:
        argv = build_docker_run_command(
            SandboxConfig(), "C:/tmp/workspace", "pytest -q"
        )

        assert argv[0] == "docker"
        assert argv[1] == "run"
        assert "--rm" in argv
        assert _value(argv, "--network") == "none"
        assert _value(argv, "--memory") == "256m"
        assert _value(argv, "--memory-swap") == "256m"
        assert _value(argv, "--pids-limit") == "256"
        assert _value(argv, "--cap-drop") == "ALL"
        assert _value(argv, "--security-opt") == "no-new-privileges"
        assert _value(argv, "--user") == "1000:1000"
        assert "--read-only" in argv
        assert _value(argv, "--tmpfs") == "/tmp:rw,size=64m"
        assert _value(argv, "--volume") == "C:/tmp/workspace:/workspace:ro"
        assert _value(argv, "--workdir") == "/workspace"
        assert argv[-4:] == ["quorum-sandbox:latest", "sh", "-c", "pytest -q"]

    def test_container_name_included_when_set(self) -> None:
        config = SandboxConfig(container_name="sandbox-abc123")
        argv = build_docker_run_command(config, "C:/ws", "true")
        assert argv[argv.index("--name") + 1] == "sandbox-abc123"

    def test_no_name_flag_when_unset(self) -> None:
        argv = build_docker_run_command(SandboxConfig(), "C:/ws", "true")
        assert "--name" not in argv

    def test_windows_backslash_path_normalized(self) -> None:
        argv = build_docker_run_command(
            SandboxConfig(), "C:\\Users\\me\\workspace", "true"
        )
        assert _value(argv, "--volume") == "C:/Users/me/workspace:/workspace:ro"

    def test_path_object_accepted(self) -> None:
        argv = build_docker_run_command(
            SandboxConfig(), Path("D:/data/scan"), "true"
        )
        assert _value(argv, "--volume") == "D:/data/scan:/workspace:ro"

    def test_custom_config_values_propagate(self) -> None:
        config = SandboxConfig(
            image="python:3.13-slim",
            memory_limit="512m",
            pids_limit=128,
            tmpfs_size="128m",
            workdir="/src",
            user="0:0",
        )
        argv = build_docker_run_command(config, "C:/ws", "true")
        assert _value(argv, "--memory") == "512m"
        assert _value(argv, "--memory-swap") == "512m"
        assert _value(argv, "--pids-limit") == "128"
        assert _value(argv, "--tmpfs") == "/tmp:rw,size=128m"
        assert _value(argv, "--workdir") == "/src"
        assert _value(argv, "--volume") == "C:/ws:/src:ro"
        assert _value(argv, "--user") == "0:0"
        assert argv[-4] == "python:3.13-slim"