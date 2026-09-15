"""PR diff parsing: convert raw unified diff text into structured changed files.

Consumes GitHub's ``application/vnd.github.diff`` output (a unified diff) and
produces a list of :class:`ChangedFile` records with per-file hunks and
added/removed lines. The module is intentionally pure (no network, no database)
so later phases (AST extraction, context building, agents) can consume the same
structure.
"""

import re
from dataclasses import dataclass, field

LINE_CONTEXT = "context"
LINE_ADDED = "add"
LINE_REMOVED = "remove"

STATUS_ADDED = "added"
STATUS_MODIFIED = "modified"
STATUS_DELETED = "deleted"
STATUS_RENAMED = "renamed"
STATUS_BINARY = "binary"

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class DiffLine:
    """A single line inside a hunk."""

    kind: str
    old_line: int | None
    new_line: int | None
    content: str


@dataclass
class DiffHunk:
    """A contiguous change region with its line ranges."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[DiffLine] = field(default_factory=list)


@dataclass
class ChangedFile:
    """A file changed by the pull request."""

    path: str
    status: str
    hunks: list[DiffHunk] = field(default_factory=list)
    old_path: str | None = None

    @property
    def added_lines(self) -> int:
        return sum(
            1 for hunk in self.hunks for line in hunk.lines if line.kind == LINE_ADDED
        )

    @property
    def removed_lines(self) -> int:
        return sum(
            1 for hunk in self.hunks for line in hunk.lines if line.kind == LINE_REMOVED
        )


def _split_paths(header: str) -> list[str]:
    """Split a diff header into path tokens, honoring double-quoted segments."""
    parts: list[str] = []
    buffer: list[str] = []
    in_quotes = False
    for char in header:
        if char == '"':
            in_quotes = not in_quotes
        elif char.isspace() and not in_quotes:
            if buffer:
                parts.append("".join(buffer))
                buffer = []
        else:
            buffer.append(char)
    if buffer:
        parts.append("".join(buffer))
    return parts


def _strip_quotes(value: str) -> str:
    return value.strip('"')


def _parse_diff_git_path(line: str) -> str:
    parts = _split_paths(line[len("diff --git ") :])
    path = parts[-1] if len(parts) > 1 else (parts[0] if parts else "")
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path


def _parse_side_path(prefix_and_path: str) -> str:
    path = _strip_quotes(prefix_and_path.strip())
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path


def _parse_hunk_header(line: str) -> DiffHunk | None:
    match = _HUNK_HEADER_RE.match(line)
    if match is None:
        return None
    return DiffHunk(
        old_start=int(match.group(1)),
        old_count=int(match.group(2) or 1),
        new_start=int(match.group(3)),
        new_count=int(match.group(4) or 1),
    )


def _make_diff_line(
    marker: str, content: str, old_line: int, new_line: int
) -> DiffLine:
    if marker == "+":
        return DiffLine(kind=LINE_ADDED, old_line=None, new_line=new_line, content=content)
    if marker == "-":
        return DiffLine(kind=LINE_REMOVED, old_line=old_line, new_line=None, content=content)
    return DiffLine(kind=LINE_CONTEXT, old_line=old_line, new_line=new_line, content=content)


def parse_unified_diff(diff_text: str) -> list[ChangedFile]:
    """Parse a GitHub unified diff into structured changed files."""
    if not diff_text:
        return []

    files: list[ChangedFile] = []
    current: ChangedFile | None = None
    hunk: DiffHunk | None = None
    in_hunk = False
    old_line = 0
    new_line = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current is not None:
                files.append(current)
            current = ChangedFile(path=_parse_diff_git_path(line), status=STATUS_MODIFIED)
            hunk = None
            in_hunk = False
            continue

        if current is None:
            continue

        if in_hunk:
            if line.startswith("@@"):
                hunk = _parse_hunk_header(line)
                if hunk is not None:
                    current.hunks.append(hunk)
                    old_line = hunk.old_start
                    new_line = hunk.new_start
                continue

            marker = line[0] if line else " "
            if marker in (" ", "+", "-"):
                hunk.lines.append(
                    _make_diff_line(marker, line[1:], old_line, new_line)
                )
                if marker == "-":
                    old_line += 1
                elif marker == "+":
                    new_line += 1
                else:
                    old_line += 1
                    new_line += 1
                continue
            if marker == "\\":
                continue

            in_hunk = False
            hunk = None

        if line.startswith("--- "):
            side_path = _parse_side_path(line[4:])
            if side_path == "/dev/null":
                current.status = STATUS_ADDED
            else:
                current.old_path = side_path
            continue
        if line.startswith("+++ "):
            if _parse_side_path(line[4:]) == "/dev/null":
                current.status = STATUS_DELETED
            continue
        if line.startswith("rename from "):
            current.old_path = _strip_quotes(line[len("rename from ") :])
            continue
        if line.startswith("rename to "):
            current.status = STATUS_RENAMED
            current.path = _strip_quotes(line[len("rename to ") :])
            continue
        if line.startswith("Binary files "):
            current.status = STATUS_BINARY
            continue
        if line.startswith("@@"):
            hunk = _parse_hunk_header(line)
            if hunk is not None:
                current.hunks.append(hunk)
                old_line = hunk.old_start
                new_line = hunk.new_start
                in_hunk = True
            continue

    if current is not None:
        files.append(current)

    return files