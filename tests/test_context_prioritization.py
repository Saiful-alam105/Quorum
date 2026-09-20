from quorum.analysis.context_selector import rank_changed_files, rank_hunks
from quorum.analysis.diff import (
    LINE_ADDED,
    LINE_REMOVED,
    ChangedFile,
    DiffHunk,
    DiffLine,
)


def _file(path: str, added: int, removed: int) -> ChangedFile:
    lines = []
    for i in range(added):
        lines.append(
            DiffLine(kind=LINE_ADDED, old_line=None, new_line=i + 1, content="x")
        )
    for i in range(removed):
        lines.append(
            DiffLine(kind=LINE_REMOVED, old_line=i + 1, new_line=None, content="x")
        )
    return ChangedFile(
        path=path,
        status="modified",
        hunks=[
            DiffHunk(
                old_start=1,
                old_count=len(lines),
                new_start=1,
                new_count=len(lines),
                lines=lines,
            )
        ],
    )


def _hunk(start: int, added: int = 0, removed: int = 0) -> DiffHunk:
    lines = []
    for i in range(removed):
        lines.append(
            DiffLine(kind=LINE_REMOVED, old_line=start + i, new_line=None, content="x")
        )
    for i in range(added):
        lines.append(
            DiffLine(
                kind=LINE_ADDED,
                old_line=None,
                new_line=start + removed + i,
                content="x",
            )
        )
    return DiffHunk(
        old_start=start,
        old_count=len(lines),
        new_start=start,
        new_count=len(lines),
        lines=lines,
    )


class TestRankChangedFiles:
    def test_orders_by_change_volume_descending(self) -> None:
        small = _file("small.py", added=1, removed=0)
        large = _file("large.py", added=5, removed=2)
        ranked = rank_changed_files([small, large])
        assert ranked == [large, small]

    def test_orders_added_lines_over_removed_for_ties(self) -> None:
        more_added = _file("a.py", added=3, removed=0)
        more_removed = _file("b.py", added=2, removed=1)
        ranked = rank_changed_files([more_removed, more_added])
        assert ranked == [more_added, more_removed]

    def test_tie_break_by_path_ascending(self) -> None:
        a = _file("b.py", added=2, removed=0)
        b = _file("a.py", added=2, removed=0)
        ranked = rank_changed_files([a, b])
        assert [file.path for file in ranked] == ["a.py", "b.py"]

    def test_empty_input_returns_empty(self) -> None:
        assert rank_changed_files([]) == []

    def test_preserves_objects(self) -> None:
        files = [_file("a.py", added=1, removed=0)]
        assert rank_changed_files(files) == files

    def test_deterministic(self) -> None:
        files = [_file("b.py", added=2, removed=1), _file("a.py", added=1, removed=1)]
        assert rank_changed_files(files) == rank_changed_files(files)


class TestRankHunks:
    def test_orders_by_change_volume_descending(self) -> None:
        one_change = _hunk(start=1, added=1)
        three_changes = _hunk(start=10, added=2, removed=1)
        ranked = rank_hunks([one_change, three_changes])
        assert ranked == [three_changes, one_change]

    def test_tie_break_by_position_ascending(self) -> None:
        later = _hunk(start=20, added=1)
        earlier = _hunk(start=5, added=1)
        ranked = rank_hunks([later, earlier])
        assert ranked == [earlier, later]

    def test_empty_input_returns_empty(self) -> None:
        assert rank_hunks([]) == []

    def test_deterministic(self) -> None:
        hunks = [_hunk(start=3, added=2), _hunk(start=1, added=1, removed=1)]
        assert rank_hunks(hunks) == rank_hunks(hunks)