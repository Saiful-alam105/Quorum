import pytest

from quorum.analysis.context_sizer import (
    count_characters,
    estimate_tokens,
    estimate_tokens_for_chars,
    size_changed_file,
    size_hunk,
    size_lines,
)
from quorum.analysis.diff import (
    LINE_ADDED,
    LINE_CONTEXT,
    LINE_REMOVED,
    ChangedFile,
    DiffHunk,
    DiffLine,
)


class TestCountCharacters:
    def test_empty(self) -> None:
        assert count_characters("") == 0

    def test_plain_text(self) -> None:
        assert count_characters("hello") == 5

    def test_unicode_counts_code_points(self) -> None:
        assert count_characters("héllo") == 5
        assert count_characters("😀") == 1


class TestEstimateTokens:
    def test_empty_is_zero(self) -> None:
        assert estimate_tokens("") == 0

    def test_exactly_at_divisor_boundary(self) -> None:
        assert estimate_tokens("abcd") == 1

    def test_one_over_divisor_boundary(self) -> None:
        assert estimate_tokens("abcde") == 2

    def test_single_character(self) -> None:
        assert estimate_tokens("a") == 1

    def test_custom_chars_per_token(self) -> None:
        assert estimate_tokens("abc", chars_per_token=1) == 3

    def test_invalid_chars_per_token_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            estimate_tokens("abcd", chars_per_token=0)

    def test_deterministic(self) -> None:
        assert estimate_tokens("repeat me") == estimate_tokens("repeat me")


class TestEstimateTokensForChars:
    def test_zero_is_zero(self) -> None:
        assert estimate_tokens_for_chars(0) == 0

    def test_boundary(self) -> None:
        assert estimate_tokens_for_chars(4) == 1
        assert estimate_tokens_for_chars(5) == 2

    def test_negative_is_zero(self) -> None:
        assert estimate_tokens_for_chars(-3) == 0

    def test_custom_chars_per_token(self) -> None:
        assert estimate_tokens_for_chars(9, chars_per_token=3) == 3

    def test_invalid_chars_per_token_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            estimate_tokens_for_chars(8, chars_per_token=0)


class TestSizeLines:
    def test_all_line_kinds_counted(self) -> None:
        lines = [
            DiffLine(kind=LINE_ADDED, old_line=None, new_line=1, content="add"),
            DiffLine(kind=LINE_REMOVED, old_line=1, new_line=None, content="remove"),
            DiffLine(kind=LINE_CONTEXT, old_line=2, new_line=2, content="context"),
        ]
        assert size_lines(lines) == len("add") + len("remove") + len("context")

    def test_empty_lines(self) -> None:
        assert size_lines([]) == 0

    def test_empty_content_lines_still_count_zero(self) -> None:
        lines = [DiffLine(kind=LINE_ADDED, old_line=None, new_line=1, content="")]
        assert size_lines(lines) == 0


class TestSizeHunk:
    def test_sums_line_content(self) -> None:
        hunk = DiffHunk(
            old_start=1,
            old_count=2,
            new_start=1,
            new_count=2,
            lines=[
                DiffLine(kind=LINE_REMOVED, old_line=1, new_line=None, content="old"),
                DiffLine(kind=LINE_ADDED, old_line=None, new_line=1, content="new"),
            ],
        )
        assert size_hunk(hunk) == len("old") + len("new")

    def test_no_lines_is_zero(self) -> None:
        assert size_hunk(DiffHunk(old_start=1, old_count=0, new_start=1, new_count=0)) == 0


class TestSizeChangedFile:
    def test_sums_all_hunks(self) -> None:
        file = ChangedFile(
            path="app.py",
            status="modified",
            hunks=[
                DiffHunk(
                    old_start=1,
                    old_count=1,
                    new_start=1,
                    new_count=1,
                    lines=[
                        DiffLine(kind=LINE_ADDED, old_line=None, new_line=1, content="abc")
                    ],
                ),
                DiffHunk(
                    old_start=5,
                    old_count=1,
                    new_start=5,
                    new_count=1,
                    lines=[
                        DiffLine(kind=LINE_ADDED, old_line=None, new_line=5, content="def")
                    ],
                ),
            ],
        )
        assert size_changed_file(file) == len("abc") + len("def")

    def test_file_without_hunks_is_zero(self) -> None:
        file = ChangedFile(path="logo.png", status="binary")
        assert size_changed_file(file) == 0