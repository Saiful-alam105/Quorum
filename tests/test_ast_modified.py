from quorum.analysis.ast_parser import analyze_changed_python, modified_structures
from quorum.analysis.diff import LINE_ADDED, ChangedFile, DiffHunk, DiffLine

SOURCE = """import os


def first():
    return 1


def second():
    x = 1
    return x


def third():
    return 3


class Widget:
    def method(self):
        return 4
"""


def _changed_file(path: str = "app.py", hunk_new_start: int = 1, hunk_new_count: int = 1) -> ChangedFile:
    hunk = DiffHunk(
        old_start=1,
        old_count=hunk_new_count,
        new_start=hunk_new_start,
        new_count=hunk_new_count,
        lines=[
            DiffLine(kind=LINE_ADDED, old_line=None, new_line=hunk_new_start + i, content="x")
            for i in range(hunk_new_count)
        ],
    )
    return ChangedFile(path=path, status="modified", hunks=[hunk])


def _line_of(name: str) -> int:
    info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=1, hunk_new_count=0))
    for f in info.functions:
        if f.name == name:
            return f.start_line
    raise AssertionError(f"{name} not found")


def _range_of(name: str) -> tuple[int, int]:
    info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=1, hunk_new_count=0))
    for f in info.functions:
        if f.name == name:
            return f.start_line, f.end_line
    raise AssertionError(f"{name} not found")


class TestAnalyzeChangedPython:
    def test_added_line_at_function_start_marks_modified(self) -> None:
        start = _line_of("first")
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=start))
        first = next(f for f in info.functions if f.name == "first")
        assert first.modified is True

    def test_added_line_at_function_end_marks_modified(self) -> None:
        _, end = _range_of("second")
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=end))
        second = next(f for f in info.functions if f.name == "second")
        assert second.modified is True

    def test_added_line_at_function_middle_marks_modified(self) -> None:
        start, end = _range_of("second")
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=(start + end) // 2))
        second = next(f for f in info.functions if f.name == "second")
        assert second.modified is True

    def test_line_outside_functions_marks_none(self) -> None:
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=2))
        assert all(not f.modified for f in info.functions)
        assert all(not c.modified for c in info.classes)

    def test_only_touched_functions_modified(self) -> None:
        third_start = _line_of("third")
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=third_start))
        flags = {f.name: f.modified for f in info.functions}
        assert flags == {"first": False, "second": False, "third": True, "method": False}

    def test_class_modified_when_method_touched(self) -> None:
        method_start, _ = _range_of("method")
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=method_start))
        widget = next(c for c in info.classes if c.name == "Widget")
        method = next(f for f in info.functions if f.name == "method")
        assert widget.modified is True
        assert method.modified is True

    def test_added_file_marks_all_modified(self) -> None:
        total = len(SOURCE.splitlines())
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=1, hunk_new_count=total))
        assert all(f.modified for f in info.functions)
        assert all(c.modified for c in info.classes)

    def test_no_hunks_marks_none(self) -> None:
        info = analyze_changed_python(SOURCE, ChangedFile(path="app.py", status="renamed"))
        assert all(not f.modified for f in info.functions)
        assert all(not c.modified for c in info.classes)

    def test_deterministic(self) -> None:
        file = _changed_file(hunk_new_start=7)
        assert analyze_changed_python(SOURCE, file) == analyze_changed_python(SOURCE, file)


class TestModifiedStructures:
    def test_returns_only_modified(self) -> None:
        second_start, _ = _range_of("second")
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=second_start))
        filtered = modified_structures(info)
        assert [f.name for f in filtered.functions] == ["second"]
        assert filtered.classes == []
        assert filtered.path == "app.py"

    def test_empty_when_none_modified(self) -> None:
        info = analyze_changed_python(SOURCE, _changed_file(hunk_new_start=2))
        filtered = modified_structures(info)
        assert filtered.functions == []
        assert filtered.classes == []