"""Phase 7 context window management: the bounded-context representation.

This module defines the data model for a prepared, size-bounded pull-request
context. Later phases (sizing, ranking, truncation, Context Builder, agents)
consume this representation instead of the raw diff so that the bounded
snapshot is explicit and the Phase 6 diff structures are never mutated.

The model is intentionally pure: no network, no database, no prompt building.
``render_text()`` exists only as a deterministic serialization for tests and
manual verification; the actual LLM prompt is built by a later phase.
"""

from dataclasses import dataclass, field

from quorum.analysis.diff import LINE_REMOVED


@dataclass
class ContextLine:
    """A single line of bounded context (a snapshot of DiffLine)."""

    kind: str
    old_line: int | None
    new_line: int | None
    content: str


@dataclass
class ContextHunk:
    """A contiguous change region within a file's prepared context."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[ContextLine] = field(default_factory=list)


@dataclass
class ContextFile:
    """A changed file's prepared context, preserving diff metadata."""

    path: str
    status: str
    old_path: str | None = None
    hunks: list[ContextHunk] = field(default_factory=list)


@dataclass
class PreparedContext:
    """The deterministic, budget-bounded context for one pull request."""

    files: list[ContextFile] = field(default_factory=list)
    truncated: bool = False
    truncated_files: list[str] = field(default_factory=list)
    total_estimated_tokens: int = 0
    total_characters: int = 0
    budget_estimated_tokens: int | None = None

    def render_text(self) -> str:
        """Serialize the prepared context deterministically for verification."""
        sections = []
        for file in self.files:
            lines = [f"=== {file.path} ({file.status}) ==="]
            for hunk in file.hunks:
                lines.append(
                    f"@@ -{hunk.old_start},{hunk.old_count} "
                    f"+{hunk.new_start},{hunk.new_count} @@"
                )
                for line in hunk.lines:
                    number = line.old_line if line.kind == LINE_REMOVED else line.new_line
                    lines.append(f"{line.kind}:{number}:{line.content}")
            sections.append("\n".join(lines))
        return "\n".join(sections)