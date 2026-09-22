"""Python AST extraction (Phase 6 completion).

Parses a changed Python file's source with the stdlib ``ast`` module and
extracts the functions, methods, and classes with their arguments, decorators,
source ranges, and surrounding source context. The parser is pure (no network,
no database) and deterministic. Modified-structure detection against the diff
is added in a later chunk of this phase.
"""

import ast
from dataclasses import dataclass, field

KIND_FUNCTION = "function"
KIND_ASYNC_FUNCTION = "async_function"
KIND_METHOD = "method"
KIND_ASYNC_METHOD = "async_method"


@dataclass
class FunctionInfo:
    """A function or method extracted from a Python file."""

    name: str
    kind: str
    class_name: str | None = None
    arguments: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    source: str = ""


@dataclass
class ClassInfo:
    """A class extracted from a Python file."""

    name: str
    decorators: list[str] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0


@dataclass
class AstFileInfo:
    """The structural summary of one changed Python file."""

    path: str
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)


def _arguments(node: ast.arguments) -> list[str]:
    names = [arg.arg for arg in node.posonlyargs]
    names += [arg.arg for arg in node.args]
    if node.vararg is not None:
        names.append(f"*{node.vararg.arg}")
    names += [arg.arg for arg in node.kwonlyargs]
    if node.kwarg is not None:
        names.append(f"**{node.kwarg.arg}")
    return names


def _decorators(node) -> list[str]:
    return [ast.unparse(decorator) for decorator in node.decorator_list]


def _function_kind(node, enclosing_class: str | None) -> str:
    is_async = isinstance(node, ast.AsyncFunctionDef)
    if enclosing_class is not None:
        return KIND_ASYNC_METHOD if is_async else KIND_METHOD
    return KIND_ASYNC_FUNCTION if is_async else KIND_FUNCTION


def _function_info(node, source: str, enclosing_class: str | None) -> FunctionInfo:
    return FunctionInfo(
        name=node.name,
        kind=_function_kind(node, enclosing_class),
        class_name=enclosing_class,
        arguments=_arguments(node.args),
        decorators=_decorators(node),
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        source=ast.get_source_segment(source, node) or "",
    )


def _class_info(node) -> ClassInfo:
    return ClassInfo(
        name=node.name,
        decorators=_decorators(node),
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
    )


def _walk(node, source: str, enclosing_class: str | None, info: AstFileInfo) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            info.classes.append(_class_info(child))
            _walk(child, source, child.name, info)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info.functions.append(_function_info(child, source, enclosing_class))
            _walk(child, source, None, info)
        else:
            _walk(child, source, enclosing_class, info)


def parse_python_ast(source: str, path: str) -> AstFileInfo:
    """Parse Python source and extract its functions, methods, and classes.

    Returns an empty :class:`AstFileInfo` when the source cannot be parsed
    (for example a changed file that introduces a syntax error).
    """
    info = AstFileInfo(path=path)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return info
    _walk(tree, source, None, info)
    return info