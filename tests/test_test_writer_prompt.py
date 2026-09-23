from quorum.agents.test_writer import build_test_writer_prompt
from quorum.analysis.ast_parser import AstFileInfo, ClassInfo, FunctionInfo
from quorum.analysis.context import PreparedContext


def _modified_function(**overrides) -> FunctionInfo:
    entry = {
        "name": "alpha",
        "kind": "function",
        "arguments": ["a", "b"],
        "source": "def alpha(a, b):\n    return a + b",
        "modified": True,
    }
    entry.update(overrides)
    return FunctionInfo(**entry)


def _unmodified_function() -> FunctionInfo:
    return FunctionInfo(
        name="untouched", kind="function", arguments=[], source="def untouched():\n    pass", modified=False
    )


class TestBuildTestWriterPrompt:
    def test_includes_modified_function_details(self) -> None:
        info = AstFileInfo(path="app.py", functions=[_modified_function()])
        prompt = build_test_writer_prompt([info], None, owner="octocat", repo="r", pr_number=1)
        assert "octocat/r#1" in prompt
        assert "app.py" in prompt
        assert "alpha" in prompt
        assert "a, b" in prompt
        assert "def alpha(a, b):" in prompt

    def test_excludes_unmodified_functions(self) -> None:
        info = AstFileInfo(
            path="app.py", functions=[_modified_function(), _unmodified_function()]
        )
        prompt = build_test_writer_prompt([info], None)
        assert "alpha" in prompt
        assert "untouched" not in prompt

    def test_method_shows_class(self) -> None:
        info = AstFileInfo(
            path="app.py",
            functions=[_modified_function(name="load", class_name="Config", kind="method")],
        )
        prompt = build_test_writer_prompt([info], None)
        assert "method of Config" in prompt

    def test_decorators_shown(self) -> None:
        info = AstFileInfo(
            path="app.py",
            functions=[_modified_function(decorators=["staticmethod"])],
        )
        prompt = build_test_writer_prompt([info], None)
        assert "staticmethod" in prompt

    def test_no_modified_functions_placeholder(self) -> None:
        info = AstFileInfo(path="app.py", functions=[_unmodified_function()])
        prompt = build_test_writer_prompt([info], None)
        assert "(none)" in prompt

    def test_empty_ast_files(self) -> None:
        prompt = build_test_writer_prompt([], None)
        assert "(none)" in prompt

    def test_instructions_present(self) -> None:
        prompt = build_test_writer_prompt([], None)
        assert "tests" in prompt
        assert "pytest" in prompt
        assert "test_<function>.py" in prompt

    def test_context_rendered_or_placeholder(self) -> None:
        prompt = build_test_writer_prompt([], None)
        assert "(no context)" in prompt

    def test_deterministic(self) -> None:
        info = AstFileInfo(path="app.py", functions=[_modified_function()])
        assert build_test_writer_prompt([info], None, "o", "r", 1) == build_test_writer_prompt(
            [info], None, "o", "r", 1
        )

    def test_returns_string(self) -> None:
        prompt = build_test_writer_prompt([], None)
        assert isinstance(prompt, str)
        assert len(prompt) > 0