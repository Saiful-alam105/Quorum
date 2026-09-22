"""Python AST extraction (Phase 6 completion).

Parses a changed Python file's source with the stdlib ``ast`` module and
extracts the functions, methods, and classes with their arguments, decorators,
source ranges, and surrounding source context. The parser is pure (no network,
no database) and deterministic. Modified-structure detection against the diff
is added in a later chunk of this phase.
"""

import ast
from dataclasses import dataclass, field

from quorum.analysis.diff import ChangedFile

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
    modified: bool = False


@dataclass
class ClassInfo:
    """A class extracted from a Python file."""

    name: str
    decorators: list[str] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0
    modified: bool = False


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


def _hunk_new_spans(changed_file: ChangedFile) -> list[tuple[int, int]]:
    """Inclusive new-side line spans covered by each hunk."""
    spans = []
    for hunk in changed_file.hunks:
        start = hunk.new_start
        end = hunk.new_start + hunk.new_count - 1
        spans.append((start, end))
    return spans


def _overlaps(start_line: int, end_line: int, spans: list[tuple[int, int]]) -> bool:
    for span_start, span_end in spans:
        if start_line <= span_end and end_line >= span_start:
            return True
    return False


def analyze_changed_python(source: str, changed_file: ChangedFile) -> AstFileInfo:
    """Parse ``source`` and mark structures whose range overlaps a hunk.

    A function or class is ``modified`` when its line range overlaps the
    new-side span of any hunk in ``changed_file`` (which covers added lines and
    the context around removals).
    """
    info = parse_python_ast(source, changed_file.path)
    spans = _hunk_new_spans(changed_file)
    for function in info.functions:
        function.modified = _overlaps(function.start_line, function.end_line, spans)
    for cls in info.classes:
        cls.modified = _overlaps(cls.start_line, cls.end_line, spans)
    return info


def modified_structures(info: AstFileInfo) -> AstFileInfo:
    """Return only the functions and classes flagged as modified."""
    return AstFileInfo(
        path=info.path,
        functions=[f for f in info.functions if f.modified],
        classes=[c for c in info.classes if c.modified],
    )