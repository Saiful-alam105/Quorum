from quorum.analysis.context_selector import build_prepared_context
from quorum.analysis.diff import (
    LINE_ADDED,
    LINE_CONTEXT,
    LINE_REMOVED,
    ChangedFile,
    DiffHunk,
    DiffLine,
)


def _file(path: str, hunks: list[DiffHunk] | None = None) -> ChangedFile:
    return ChangedFile(path=path, status="modified", hunks=hunks or [])


def _hunk(start: int = 1, lines: list[DiffLine] | None = None) -> DiffHunk:
    lines = lines or []
    return DiffHunk(
        old_start=start,
        old_count=len(lines),
        new_start=start,
        new_count=len(lines),
        lines=lines,
    )


def _line(kind: str, content: str, old: int | None = None, new: int | None = None) -> DiffLine:
    return DiffLine(kind=kind, old_line=old, new_line=new, content=content)


class TestBuildPreparedContext:
    def test_small_pr_fits_completely(self) -> None:
        files = [
            _file(
                "a.py",
                [_hunk(lines=[_line(LINE_ADDED, "abc", new=1)])],
            ),
            _file(
                "b.py",
                [_hunk(lines=[_line(LINE_ADDED, "x", new=1)])],
            ),
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=100, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is False
        assert context.truncated_files == []
        assert [file.path for file in context.files] == ["a.py", "b.py"]
        assert context.total_characters == 4
        assert context.total_estimated_tokens == 1
        assert context.budget_estimated_tokens == 100

    def test_context_exactly_at_limit(self) -> None:
        files = [
            _file(
                "a.py",
                [_hunk(lines=[_line(LINE_ADDED, "abcd", new=1)])],
            )
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is False
        assert context.total_estimated_tokens == 1
        assert context.total_characters == 4
        assert len(context.files) == 1

    def test_over_limit_drops_lowest_priority_file(self) -> None:
        files = [
            _file(
                "small.py",
                [_hunk(lines=[_line(LINE_ADDED, "a", new=1)])],
            ),
            _file(
                "big.py",
                [_hunk(lines=[_line(LINE_ADDED, "bbbb", new=1)])],
            ),
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        assert [file.path for file in context.files] == ["big.py"]
        assert context.truncated_files == ["small.py"]

    def test_multiple_files_compete_for_budget(self) -> None:
        files = [
            _file(
                "tiny.py",
                [_hunk(lines=[_line(LINE_ADDED, "a", new=1)])],
            ),
            _file(
                "med.py",
                [_hunk(lines=[_line(LINE_ADDED, "bb", new=1)])],
            ),
            _file(
                "large.py",
                [_hunk(lines=[_line(LINE_ADDED, "cccc", new=1)])],
            ),
        ]
        context = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        assert [file.path for file in context.files] == ["large.py"]
        assert context.truncated_files == ["med.py", "tiny.py"]

    def test_trims_context_lines_before_added_lines(self) -> None:
        lines = [
            _line(LINE_CONTEXT, "c" * 3, old=1, new=1),
            _line(LINE_CONTEXT, "c" * 3, old=2, new=2),
            _line(LINE_ADDED, "new", new=3),
            _line(LINE_CONTEXT, "c" * 3, old=3, new=4),
            _line(LINE_CONTEXT, "c" * 3, old=4, new=5),
        ]
        files = [_file("a.py", [_hunk(start=1, lines=lines)])]
        context = build_prepared_context(
            files, budget_estimated_tokens=3, chars_per_token=4, min_context_lines=1
        )
        assert context.truncated is True
        hunk = context.files[0].hunks[0]
        kinds = [line.kind for line in hunk.lines]
        added = [line for line in hunk.lines if line.kind == LINE_ADDED]
        assert len(added) == 1
        assert added[0].content == "new"
        assert kinds.count(LINE_CONTEXT) <= 2
        assert context.total_estimated_tokens <= 3

    def test_very_large_single_file_is_trimmed_to_budget(self) -> None:
        lines = [
            _line(LINE_ADDED, "x" * 10, new=i + 1) for i in range(50)
        ]
        files = [_file("huge.py", [_hunk(lines=lines)])]
        context = build_prepared_context(
            files, budget_estimated_tokens=5, chars_per_token=4, min_context_lines=2
        )
        assert context.truncated is True
        assert len(context.files) == 1
        assert context.total_characters == 20
        assert context.total_estimated_tokens <= 5
        assert len(context.files[0].hunks[0].lines) == 2

    def test_deterministic_output(self) -> None:
        files = [
            _file(
                "big.py",
                [_hunk(lines=[_line(LINE_ADDED, "bbbb", new=1)])],
            ),
            _file(
                "med.py",
                [_hunk(lines=[_line(LINE_ADDED, "bb", new=1)])],
            ),
            _file(
                "tiny.py",
                [_hunk(lines=[_line(LINE_ADDED, "a", new=1)])],
            ),
        ]
        first = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        second = build_prepared_context(
            files, budget_estimated_tokens=1, chars_per_token=4, min_context_lines=2
        )
        assert first.render_text() == second.render_text()
        assert first.truncated_files == second.truncated_files
        assert first.total_characters == second.total_characters

    def test_line_metadata_preserved(self) -> None:
        lines = [
            _line(LINE_CONTEXT, "ctx", old=10, new=10),
            _line(LINE_ADDED, "add", new=11),
        ]
        files = [_file("a.py", [_hunk(start=10, lines=lines)])]
        context = build_prepared_context(
            files, budget_estimated_tokens=100, chars_per_token=4, min_context_lines=2
        )
        hunk = context.files[0].hunks[0]
        added = hunk.lines[1]
        assert added.kind == LINE_ADDED
        assert added.new_line == 11
        assert added.old_line is None
        assert context.files[0].path == "a.py"

    def test_empty_changed_files(self) -> None:
        context = build_prepared_context(
            [], budget_estimated_tokens=100, chars_per_token=4, min_context_lines=2
        )
        assert context.files == []
        assert context.truncated is False
        assert context.truncated_files == []
        assert context.budget_estimated_tokens == 100

    def test_uses_settings_budget_by_default(self) -> None:
        files = [
            _file(
                "a.py",
                [_hunk(lines=[_line(LINE_ADDED, "abc", new=1)])],
            )
        ]
        context = build_prepared_context(files)
        assert context.budget_estimated_tokens == 8000
        assert context.truncated is False