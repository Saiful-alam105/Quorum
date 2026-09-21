import tempfile
from pathlib import Path

import pytest

from quorum.analysis.diff import (
    STATUS_ADDED,
    STATUS_BINARY,
    STATUS_DELETED,
    STATUS_MODIFIED,
    STATUS_RENAMED,
    ChangedFile,
)
from quorum.analysis.semgrep import build_scan_directory


def _file(path: str, status: str = STATUS_MODIFIED) -> ChangedFile:
    return ChangedFile(path=path, status=status)


def _fake_fetch(contents: dict[str, str]):
    async def fetch(path: str, ref: str) -> str:
        return contents[path]

    return fetch


class TestBuildScanDirectory:
    @pytest.mark.asyncio
    async def test_writes_scannable_files(self) -> None:
        files = [
            _file("src/app.py", STATUS_ADDED),
            _file("src/util.py", STATUS_MODIFIED),
            _file("old.py", STATUS_RENAMED),
        ]
        contents = {
            "src/app.py": "def app(): pass",
            "src/util.py": "def util(): pass",
            "old.py": "def renamed(): pass",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = await build_scan_directory(
                files, _fake_fetch(contents), "abc123", tmp
            )
            assert (Path(tmp) / "src/app.py").read_text(encoding="utf-8") == contents["src/app.py"]
            assert (Path(tmp) / "src/util.py").read_text(encoding="utf-8") == contents["src/util.py"]
            assert (Path(tmp) / "old.py").read_text(encoding="utf-8") == contents["old.py"]
            assert root == Path(tmp)

    @pytest.mark.asyncio
    async def test_skips_deleted_and_binary_files(self) -> None:
        files = [
            _file("gone.py", STATUS_DELETED),
            _file("logo.png", STATUS_BINARY),
            _file("kept.py", STATUS_MODIFIED),
        ]
        fetched: list[str] = []

        async def fetch(path: str, ref: str) -> str:
            fetched.append(path)
            return "x"

        with tempfile.TemporaryDirectory() as tmp:
            await build_scan_directory(files, fetch, "abc123", tmp)
            assert fetched == ["kept.py"]
            assert not (Path(tmp) / "gone.py").exists()
            assert not (Path(tmp) / "logo.png").exists()
            assert (Path(tmp) / "kept.py").exists()

    @pytest.mark.asyncio
    async def test_empty_changed_files_no_fetch(self) -> None:
        fetched: list[str] = []

        async def fetch(path: str, ref: str) -> str:
            fetched.append(path)
            return "x"

        with tempfile.TemporaryDirectory() as tmp:
            root = await build_scan_directory([], fetch, "abc123", tmp)
            assert fetched == []
            assert list(Path(tmp).iterdir()) == []
            assert root == Path(tmp)

    @pytest.mark.asyncio
    async def test_skips_path_traversal(self) -> None:
        files = [_file("../escape.py", STATUS_ADDED)]
        fetched: list[str] = []

        async def fetch(path: str, ref: str) -> str:
            fetched.append(path)
            return "x"

        with tempfile.TemporaryDirectory() as tmp:
            await build_scan_directory(files, fetch, "abc123", tmp)
            assert fetched == []
            assert not (Path(tmp).parent / "escape.py").exists()

    @pytest.mark.asyncio
    async def test_skips_absolute_path(self) -> None:
        files = [_file("C:/evil.py", STATUS_ADDED)]
        fetched: list[str] = []

        async def fetch(path: str, ref: str) -> str:
            fetched.append(path)
            return "x"

        with tempfile.TemporaryDirectory() as tmp:
            await build_scan_directory(files, fetch, "abc123", tmp)
            assert fetched == []

    @pytest.mark.asyncio
    async def test_fetch_failure_propagates(self) -> None:
        files = [_file("src/app.py", STATUS_ADDED)]

        async def fetch(path: str, ref: str) -> str:
            raise RuntimeError("fetch exploded")

        with tempfile.TemporaryDirectory() as tmp:
            with pytest.raises(RuntimeError, match="fetch exploded"):
                await build_scan_directory(files, fetch, "abc123", tmp)