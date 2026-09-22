from pathlib import Path
from unittest.mock import patch

import pytest

from quorum.analysis.diff import ChangedFile
from quorum.sandbox.workspace import build_sandbox_workspace, write_generated_test


class TestBuildSandboxWorkspace:
    @pytest.mark.asyncio
    async def test_delegates_to_scan_directory_assembly(self) -> None:
        changed = [ChangedFile(path="src/app.py", status="added")]
        async def fetch(path: str, ref: str) -> str:
            return "def f(): return 1\n"

        with patch(
            "quorum.sandbox.workspace.build_scan_directory",
            return_value=Path("C:/ws"),
        ) as mock_scan:
            result = await build_sandbox_workspace(changed, fetch, "abc123", "C:/ws")

        assert result == Path("C:/ws")
        mock_scan.assert_awaited_once_with(changed, fetch, "abc123", "C:/ws")


class TestWriteGeneratedTest:
    def test_writes_file_and_creates_parents(self, tmp_path: Path) -> None:
        target = write_generated_test(
            tmp_path, "tests/test_gen.py", "def test_x():\n    pass\n"
        )
        assert target == tmp_path / "tests" / "test_gen.py"
        assert target.read_text(encoding="utf-8") == "def test_x():\n    pass\n"

    def test_rejects_absolute_path(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            write_generated_test(tmp_path, "C:/evil.py", "x = 1")

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            write_generated_test(tmp_path, "../evil.py", "x = 1")

    def test_rejects_nested_traversal(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="unsafe"):
            write_generated_test(tmp_path, "tests/../../evil.py", "x = 1")