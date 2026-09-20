import pytest

from quorum.analysis.context import (
    ContextFile,
    ContextHunk,
    ContextLine,
    PreparedContext,
)
from quorum.analysis.diff import LINE_ADDED, LINE_CONTEXT, LINE_REMOVED
from quorum.config import Settings

CONTEXT_ENV_KEYS = (
    "CONTEXT_BUDGET_ESTIMATED_TOKENS",
    "CONTEXT_CHARS_PER_TOKEN",
    "CONTEXT_MIN_CONTEXT_LINES",
)


def _clear_context_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in CONTEXT_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


class TestSettingsDefaults:
    def test_budget_defaults_to_8000(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_context_env(monkeypatch)
        assert Settings().context_budget_estimated_tokens == 8000

    def test_chars_per_token_defaults_to_4(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_context_env(monkeypatch)
        assert Settings().context_chars_per_token == 4

    def test_min_context_lines_defaults_to_2(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_context_env(monkeypatch)
        assert Settings().context_min_context_lines == 2


class TestSettingsOverride:
    def test_budget_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_BUDGET_ESTIMATED_TOKENS", "12000")
        assert Settings().context_budget_estimated_tokens == 12000

    def test_chars_per_token_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_CHARS_PER_TOKEN", "5")
        assert Settings().context_chars_per_token == 5

    def test_min_context_lines_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_MIN_CONTEXT_LINES", "0")
        assert Settings().context_min_context_lines == 0


class TestPreparedContext:
    def test_empty_defaults(self) -> None:
        context = PreparedContext()
        assert context.files == []
        assert context.truncated is False
        assert context.truncated_files == []
        assert context.total_estimated_tokens == 0
        assert context.total_characters == 0
        assert context.budget_estimated_tokens is None

    def test_render_empty_is_empty_string(self) -> None:
        assert PreparedContext().render_text() == ""

    def test_render_text_preserves_metadata(self) -> None:
        context = PreparedContext(
            files=[
                ContextFile(
                    path="app.py",
                    status="modified",
                    old_path="app.py",
                    hunks=[
                        ContextHunk(
                            old_start=1,
                            old_count=2,
                            new_start=1,
                            new_count=2,
                            lines=[
                                ContextLine(
                                    kind=LINE_REMOVED,
                                    old_line=1,
                                    new_line=None,
                                    content="old",
                                ),
                                ContextLine(
                                    kind=LINE_ADDED,
                                    old_line=None,
                                    new_line=1,
                                    content="new",
                                ),
                            ],
                        )
                    ],
                )
            ]
        )
        expected = (
            "=== app.py (modified) ===\n"
            "@@ -1,2 +1,2 @@\n"
            "remove:1:old\n"
            "add:1:new"
        )
        assert context.render_text() == expected

    def test_render_text_context_lines_and_empty_content(self) -> None:
        context = PreparedContext(
            files=[
                ContextFile(
                    path="calc.py",
                    status="modified",
                    hunks=[
                        ContextHunk(
                            old_start=1,
                            old_count=2,
                            new_start=1,
                            new_count=2,
                            lines=[
                                ContextLine(
                                    kind=LINE_CONTEXT,
                                    old_line=1,
                                    new_line=1,
                                    content="def add(a, b):",
                                ),
                                ContextLine(
                                    kind=LINE_ADDED,
                                    old_line=None,
                                    new_line=2,
                                    content="",
                                ),
                            ],
                        )
                    ],
                )
            ]
        )
        text = context.render_text()
        assert "context:1:def add(a, b):" in text
        assert "add:2:" in text

    def test_render_text_is_deterministic(self) -> None:
        file = ContextFile(
            path="z.py",
            status="modified",
            hunks=[
                ContextHunk(
                    old_start=1,
                    old_count=1,
                    new_start=1,
                    new_count=1,
                    lines=[
                        ContextLine(
                            kind=LINE_ADDED,
                            old_line=None,
                            new_line=1,
                            content="x",
                        )
                    ],
                )
            ],
        )
        first = PreparedContext(files=[file])
        second = PreparedContext(files=[file])
        assert first.render_text() == second.render_text()