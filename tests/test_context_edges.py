import pytest

from quorum.analysis.context import ContextFile
from quorum.analysis.context_selector import build_prepared_context
from quorum.analysis.diff import (
    LINE_ADDED,
    ChangedFile,
    DiffHunk,
    DiffLine,
)


def _file(path: str, hunks: list[DiffHunk] | None = None, status: str = "modified") -> ChangedFile:
    return ChangedFile(path=path, status=status, hunks=hunks or [])


def _hunk(start: int = 1, lines: list[DiffLine] | None = None) -> DiffHunk:
    lines = lines or []
    return DiffHunk(
        old_start=start,
        old_count=len(lines),
        new_start=start,
        new_count=len(lines),
        lines=lines,
    )


def _line(kind: str, content: str, new: int) -> DiffLine:
    return DiffLine(kind=kind, old_line=None, new_line=new, content=content)


class TestEmptyAndMissingContent:
    def test_empty_changed_files_returns_empty_context(self) -> None:
        context = build_prepared_context(
            [], budget_estimated_tokens=100, chars_per_token=4, min_context_lines=2
        )
        assert context.files == []
        assert context.truncated is False
        assert context.truncated_files == []
        assert context.total_characters == 0

    def test_binary_file_included_as_metadata_only(self) -> None:
        files = [_file("logo.png", status="binary")]
        context = build_prepared_context(
            files, budget_estimated_tokens=100, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is False
        assert len(context.files) == 1
        assert context.files[0].path == "logo.png"
        assert context.files[0].status == "binary"
        assert context.files[0].hunks == []
        assert context.total_characters == 0
        assert context.total_estimated_tokens == 0

    def test_renamed_file_included_as_metadata_only(self) -> None:
        files = [
            ChangedFile(path="new.py", status="renamed", old_path="old.py")
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=100, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is False
        assert len(context.files) == 1
        assert context.files[0].old_path == "old.py"
        assert context.total_estimated_tokens == 0

    def test_binary_metadata_preserved_when_over_budget(self) -> None:
        files = [
            _file("logo.png", status="binary"),
            _file("med.py", [_hunk(lines=[_line(LINE_ADDED, "bbbb", new=1)])]),
            _file("big.py", [_hunk(lines=[_line(LINE_ADDED, "cccc", new=1)])]),
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        assert [file.path for file in context.files] == ["big.py", "logo.png"]
        assert context.truncated_files == ["med.py"]


class TestInvalidConfiguration:
    def test_non_positive_budget_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            build_prepared_context(
                [], budget_estimated_tokens=0, chars_per_token=4, min_context_lines=2
            )

    def test_negative_budget_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            build_prepared_context(
                [], budget_estimated_tokens=-5, chars_per_token=4, min_context_lines=2
            )

    def test_non_positive_chars_per_token_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            build_prepared_context(
                [], budget_estimated_tokens=100, chars_per_token=0, min_context_lines=2
            )

    def test_negative_min_context_lines_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            build_prepared_context(
                [], budget_estimated_tokens=100, chars_per_token=4, min_context_lines=-1
            )


class TestLastResortTruncation:
    def test_added_lines_alone_over_budget_truncated(self) -> None:
        lines = [
            _line(LINE_ADDED, "abc", new=1),
            _line(LINE_ADDED, "def", new=2),
            _line(LINE_ADDED, "ghi", new=3),
        ]
        files = [_file("huge.py", [_hunk(lines=lines)])]
        context = build_prepared_context(
            files, budget_estimated_tokens=2, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        assert len(context.files) == 1
        assert context.total_characters == 6
        assert context.total_estimated_tokens <= 2
        assert len(context.files[0].hunks[0].lines) == 2


class TestTruncationIsRecorded:
    def test_all_dropped_files_are_recorded(self) -> None:
        files = [
            _file("a.py", [_hunk(lines=[_line(LINE_ADDED, "aaaa", new=1)])]),
            _file("b.py", [_hunk(lines=[_line(LINE_ADDED, "bbbb", new=1)])]),
            _file("c.py", [_hunk(lines=[_line(LINE_ADDED, "cccc", new=1)])]),
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        assert [file.path for file in context.files] == ["a.py"]
        assert context.truncated_files == ["b.py", "c.py"]
        assert all(
            path not in context.truncated_files for path in ("a.py",)
        )

    def test_truncated_hunks_counted_per_file(self) -> None:
        files = [
            _file(
                "multi.py",
                [
                    _hunk(start=1, lines=[_line(LINE_ADDED, "aaaa", new=1)]),
                    _hunk(start=10, lines=[_line(LINE_ADDED, "bb", new=10)]),
                ],
            )
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        kept = context.files[0]
        assert kept.truncated_hunks == 1
        assert len(kept.hunks) == 1
        assert kept.hunks[0].old_start == 1

    def test_truncated_hunks_defaults_to_zero(self) -> None:
        file = ContextFile(path="a.py", status="modified")
        assert file.truncated_hunks == 0