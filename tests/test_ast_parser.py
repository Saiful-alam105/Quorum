from quorum.analysis.ast_parser import (
    KIND_ASYNC_FUNCTION,
    KIND_FUNCTION,
    KIND_METHOD,
    parse_python_ast,
)

SOURCE = '''"""module docstring"""

import os


@decorator("x")
def top_level(a, b=1, *args, c=2, **kwargs):
    return a + b


async def async_fn(x):
    return x


class MyClass:
    """class docstring"""

    def method(self, value):
        def inner(z):
            return z

        return inner(value)

    @staticmethod
    def static_method(p):
        return p


if os.name == "nt":
    def conditional_fn():
        return 1
'''


class TestParseFunctions:
    def test_extracts_functions_in_source_order(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        assert [f.name for f in info.functions] == [
            "top_level",
            "async_fn",
            "method",
            "inner",
            "static_method",
            "conditional_fn",
        ]

    def test_top_level_function_kind_and_arguments(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        top_level = info.functions[0]
        assert top_level.kind == KIND_FUNCTION
        assert top_level.class_name is None
        assert top_level.arguments == ["a", "b", "*args", "c", "**kwargs"]
        assert top_level.decorators == ["decorator('x')"]

    def test_async_function_kind(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        assert info.functions[1].kind == KIND_ASYNC_FUNCTION

    def test_nested_function_is_not_a_method(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        inner = info.functions[3]
        assert inner.name == "inner"
        assert inner.kind == KIND_FUNCTION
        assert inner.class_name is None

    def test_conditional_function_extracted(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        assert info.functions[-1].name == "conditional_fn"

    def test_source_range_and_body(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        top_level = info.functions[0]
        assert top_level.start_line >= 1
        assert top_level.end_line >= top_level.start_line
        assert "return a + b" in top_level.source


class TestParseClasses:
    def test_extracts_classes(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        assert [c.name for c in info.classes] == ["MyClass"]
        my_class = info.classes[0]
        assert my_class.start_line >= 1
        assert my_class.end_line >= my_class.start_line

    def test_methods_linked_to_class(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        method = next(f for f in info.functions if f.name == "method")
        assert method.kind == KIND_METHOD
        assert method.class_name == "MyClass"
        assert method.arguments == ["self", "value"]

    def test_static_method_decorator(self) -> None:
        info = parse_python_ast(SOURCE, "app.py")
        static = next(f for f in info.functions if f.name == "static_method")
        assert static.decorators == ["staticmethod"]
        assert static.class_name == "MyClass"


class TestEdgeCases:
    def test_empty_source(self) -> None:
        info = parse_python_ast("", "empty.py")
        assert info.path == "empty.py"
        assert info.functions == []
        assert info.classes == []

    def test_unparseable_source_returns_empty(self) -> None:
        info = parse_python_ast("def broken(:", "broken.py")
        assert info.path == "broken.py"
        assert info.functions == []
        assert info.classes == []

    def test_file_with_only_imports(self) -> None:
        info = parse_python_ast("import os\nfrom pathlib import Path\n", "imports.py")
        assert info.functions == []
        assert info.classes == []

    def test_deterministic(self) -> None:
        first = parse_python_ast(SOURCE, "app.py")
        second = parse_python_ast(SOURCE, "app.py")
        assert first == second