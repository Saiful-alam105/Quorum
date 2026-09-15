import pytest

from quorum.analysis.diff import (
    LINE_ADDED,
    LINE_CONTEXT,
    LINE_REMOVED,
    STATUS_ADDED,
    STATUS_BINARY,
    STATUS_DELETED,
    STATUS_MODIFIED,
    STATUS_RENAMED,
    parse_unified_diff,
)

MODIFIED_DIFF = r"""diff --git a/calculator.py b/calculator.py
index 1234567..89abcde 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,6 +1,7 @@
 def add(a, b):
     return a + b
 
+
 def subtract(a, b):
     return a - b
 
"""

MULTI_HUNK_DIFF = r"""diff --git a/app.py b/app.py
index abc1234..def5678 100644
--- a/app.py
+++ b/app.py
@@ -3,3 +3,4 @@
 line1
 line2
 line3
+line4
@@ -10,2 +11,2 @@
 old10
-old11
+new11
"""

NEW_FILE_DIFF = r"""diff --git a/greet.py b/greet.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/greet.py
@@ -0,0 +1,2 @@
+def greet(name):
+    return f"hi {name}"
"""

DELETED_FILE_DIFF = r"""diff --git a/old.py b/old.py
deleted file mode 100644
index 1111111..0000000
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def bye():
-    pass
"""

RENAMED_FILE_DIFF = r"""diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py
"""

BINARY_FILE_DIFF = r"""diff --git a/logo.png b/logo.png
index 1111111..2222222 100644
Binary files a/logo.png and b/logo.png differ
"""

QUOTED_PATH_DIFF = r'''diff --git "a/my file.py" "b/my file.py"
index 1234567..89abcde 100644
--- "a/my file.py"
+++ "b/my file.py"
@@ -1,1 +1,1 @@
-foo
+bar
'''

NO_NEWLINE_DIFF = r"""diff --git a/end.py b/end.py
index 1234567..89abcde 100644
--- a/end.py
+++ b/end.py
@@ -1,2 +1,2 @@
 line1
-line2
\ No newline at end of file
+line2
\ No newline at end of file
"""


class TestModifiedFile:
    def test_parses_file_metadata(self) -> None:
        files = parse_unified_diff(MODIFIED_DIFF)
        assert len(files) == 1
        assert files[0].path == "calculator.py"
        assert files[0].status == STATUS_MODIFIED
        assert files[0].old_path == "calculator.py"

    def test_parses_hunk_header(self) -> None:
        hunk = parse_unified_diff(MODIFIED_DIFF)[0].hunks[0]
        assert (hunk.old_start, hunk.old_count) == (1, 6)
        assert (hunk.new_start, hunk.new_count) == (1, 7)

    def test_line_kinds_and_numbering(self) -> None:
        hunk = parse_unified_diff(MODIFIED_DIFF)[0].hunks[0]
        assert [line.kind for line in hunk.lines] == [
            LINE_CONTEXT,
            LINE_CONTEXT,
            LINE_CONTEXT,
            LINE_ADDED,
            LINE_CONTEXT,
            LINE_CONTEXT,
            LINE_CONTEXT,
        ]

        added = hunk.lines[3]
        assert added.old_line is None
        assert added.new_line == 4
        assert added.content == ""

        assert hunk.lines[0].content == "def add(a, b):"
        assert hunk.lines[4].old_line == 4
        assert hunk.lines[4].new_line == 5

    def test_added_and_removed_counts(self) -> None:
        file = parse_unified_diff(MODIFIED_DIFF)[0]
        assert file.added_lines == 1
        assert file.removed_lines == 0


class TestMultipleHunks:
    def test_returns_each_hunk(self) -> None:
        file = parse_unified_diff(MULTI_HUNK_DIFF)[0]
        assert len(file.hunks) == 2
        assert file.added_lines == 2
        assert file.removed_lines == 1

    def test_second_hunk_numbering(self) -> None:
        hunk = parse_unified_diff(MULTI_HUNK_DIFF)[0].hunks[1]
        assert (hunk.old_start, hunk.old_count) == (10, 2)
        assert (hunk.new_start, hunk.new_count) == (11, 2)
        assert [line.kind for line in hunk.lines] == [
            LINE_CONTEXT,
            LINE_REMOVED,
            LINE_ADDED,
        ]
        removed = hunk.lines[1]
        assert removed.old_line == 11
        assert removed.new_line is None
        added = hunk.lines[2]
        assert added.old_line is None
        assert added.new_line == 12


class TestMultipleFiles:
    def test_returns_each_file_in_order(self) -> None:
        files = parse_unified_diff(MODIFIED_DIFF + "\n" + NEW_FILE_DIFF)
        assert [file.path for file in files] == ["calculator.py", "greet.py"]
        assert [file.status for file in files] == [STATUS_MODIFIED, STATUS_ADDED]


class TestNewFile:
    def test_status_and_path(self) -> None:
        file = parse_unified_diff(NEW_FILE_DIFF)[0]
        assert file.status == STATUS_ADDED
        assert file.path == "greet.py"
        assert file.old_path is None

    def test_hunk_starts_at_zero_on_old_side(self) -> None:
        hunk = parse_unified_diff(NEW_FILE_DIFF)[0].hunks[0]
        assert (hunk.old_start, hunk.old_count) == (0, 0)
        assert (hunk.new_start, hunk.new_count) == (1, 2)
        assert all(line.kind == LINE_ADDED for line in hunk.lines)
        assert [line.new_line for line in hunk.lines] == [1, 2]


class TestDeletedFile:
    def test_status_and_hunk(self) -> None:
        file = parse_unified_diff(DELETED_FILE_DIFF)[0]
        assert file.status == STATUS_DELETED
        assert file.path == "old.py"
        hunk = file.hunks[0]
        assert (hunk.old_start, hunk.old_count) == (1, 2)
        assert (hunk.new_start, hunk.new_count) == (0, 0)
        assert [line.kind for line in hunk.lines] == [LINE_REMOVED, LINE_REMOVED]
        assert [line.old_line for line in hunk.lines] == [1, 2]
        assert file.removed_lines == 2


class TestRenamedFile:
    def test_status_and_paths(self) -> None:
        file = parse_unified_diff(RENAMED_FILE_DIFF)[0]
        assert file.status == STATUS_RENAMED
        assert file.path == "new.py"
        assert file.old_path == "old.py"
        assert file.hunks == []


class TestBinaryFile:
    def test_status_and_no_hunks(self) -> None:
        file = parse_unified_diff(BINARY_FILE_DIFF)[0]
        assert file.status == STATUS_BINARY
        assert file.path == "logo.png"
        assert file.hunks == []


class TestQuotedPaths:
    def test_strips_quotes_and_prefix(self) -> None:
        file = parse_unified_diff(QUOTED_PATH_DIFF)[0]
        assert file.path == "my file.py"
        assert file.status == STATUS_MODIFIED
        hunk = file.hunks[0]
        assert hunk.lines[0].kind == LINE_REMOVED
        assert hunk.lines[0].old_line == 1
        assert hunk.lines[1].kind == LINE_ADDED
        assert hunk.lines[1].new_line == 1


class TestNoNewlineMarker:
    def test_marker_is_not_a_line(self) -> None:
        hunk = parse_unified_diff(NO_NEWLINE_DIFF)[0].hunks[0]
        assert [line.kind for line in hunk.lines] == [
            LINE_CONTEXT,
            LINE_REMOVED,
            LINE_ADDED,
        ]


class TestEmptyInput:
    @pytest.mark.parametrize("diff_text", ["", "   \n", "not a diff"])
    def test_returns_empty_list(self, diff_text: str) -> None:
        assert parse_unified_diff(diff_text) == []