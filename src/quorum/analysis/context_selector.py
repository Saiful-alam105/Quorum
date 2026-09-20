"""Context selection: deterministic importance ordering and budget allocation.

Changed content is ranked purely on evidence of change: files with more
changed lines are more important, then files with more added lines, then
alphabetically by path. Hunks follow the same change-volume rule with file
position as the tie-break. Ranking is deterministic so the same PR always
produces the same order.

``build_prepared_context`` allocates the configured budget: it fills files in
ranked order (skipping ones that do not fit), always represents the top file
even when it must be trimmed internally (context lines first, then hunks, then
lines as a last resort), and records every dropped file so truncation is never
silent.
"""

from quorum.analysis.context import (
    ContextFile,
    ContextHunk,
    ContextLine,
    PreparedContext,
)
from quorum.analysis.context_sizer import estimate_tokens_for_chars
from quorum.analysis.diff import (
    LINE_ADDED,
    LINE_CONTEXT,
    LINE_REMOVED,
    ChangedFile,
    DiffHunk,
    DiffLine,
)
from quorum.config import settings


def _file_rank_key(file: ChangedFile) -> tuple[int, int, str]:
    return (
        -(file.added_lines + file.removed_lines),
        -file.added_lines,
        file.path,
    )


def rank_changed_files(files: list[ChangedFile]) -> list[ChangedFile]:
    """Return files ordered from most important to least important."""
    return sorted(files, key=_file_rank_key)


def _hunk_change_count(hunk: DiffHunk) -> int:
    return sum(
        1 for line in hunk.lines if line.kind in (LINE_ADDED, LINE_REMOVED)
    )


def _hunk_rank_key(hunk: DiffHunk) -> tuple[int, int]:
    return (-_hunk_change_count(hunk), hunk.old_start)


def rank_hunks(hunks: list[DiffHunk]) -> list[DiffHunk]:
    """Return hunks ordered from most important to least important."""
    return sorted(hunks, key=_hunk_rank_key)


def _to_context_line(line: DiffLine) -> ContextLine:
    return ContextLine(
        kind=line.kind,
        old_line=line.old_line,
        new_line=line.new_line,
        content=line.content,
    )


def _to_context_hunk(hunk: DiffHunk) -> ContextHunk:
    return ContextHunk(
        old_start=hunk.old_start,
        old_count=hunk.old_count,
        new_start=hunk.new_start,
        new_count=hunk.new_count,
        lines=[_to_context_line(line) for line in hunk.lines],
    )


def _to_context_file(file: ChangedFile) -> ContextFile:
    return ContextFile(
        path=file.path,
        status=file.status,
        old_path=file.old_path,
        hunks=[_to_context_hunk(hunk) for hunk in file.hunks],
    )


def _hunk_chars(hunk) -> int:
    return sum(len(line.content) for line in hunk.lines)


def _file_chars(file) -> int:
    return sum(_hunk_chars(hunk) for hunk in file.hunks)


def _trim_context_runs(
    lines: list[ContextLine], min_context_lines: int
) -> list[ContextLine]:
    """Keep all changed lines and at most ``min_context_lines`` context lines
    immediately before each changed line."""
    result: list[ContextLine] = []
    pending: list[ContextLine] = []
    for line in lines:
        if line.kind == LINE_CONTEXT:
            pending.append(line)
            if len(pending) > min_context_lines:
                pending.pop(0)
        else:
            result.extend(pending)
            pending = []
            result.append(line)
    result.extend(pending)
    return result


def _fit_hunks(hunks: list[ContextHunk], max_characters: int) -> list[ContextHunk]:
    """Select hunks greedily by importance, always keeping the most changed."""
    ranked = rank_hunks(hunks)
    kept: list[ContextHunk] = []
    chars = 0
    for hunk in ranked:
        hchars = _hunk_chars(hunk)
        if chars + hchars <= max_characters:
            kept.append(hunk)
            chars += hchars
        elif not kept:
            kept.append(hunk)
            chars += hchars
    return kept


def _fit_lines(lines: list[ContextLine], max_characters: int) -> list[ContextLine]:
    """Last-resort line truncation: drop removed, then context, then added
    lines (from the end) until the content fits."""
    kept = list(lines)
    chars = sum(len(line.content) for line in kept)
    for kind in (LINE_REMOVED, LINE_CONTEXT, LINE_ADDED):
        if chars <= max_characters:
            break
        for index in range(len(kept) - 1, -1, -1):
            if chars <= max_characters:
                break
            line = kept[index]
            if line.kind == kind:
                chars -= len(line.content)
                kept.pop(index)
    return kept


def _trim_file_to_budget(
    file: ContextFile, max_characters: int, min_context_lines: int
) -> ContextFile:
    trimmed_hunks: list[ContextHunk] = []
    for hunk in file.hunks:
        lines = _trim_context_runs(hunk.lines, min_context_lines)
        trimmed_hunks.append(
            ContextHunk(
                old_start=hunk.old_start,
                old_count=hunk.old_count,
                new_start=hunk.new_start,
                new_count=hunk.new_count,
                lines=lines,
            )
        )
    kept_hunks = _fit_hunks(trimmed_hunks, max_characters)
    chars = sum(_hunk_chars(hunk) for hunk in kept_hunks)
    if chars > max_characters:
        fitted = []
        for hunk in kept_hunks:
            lines = _fit_lines(hunk.lines, max_characters)
            fitted.append(
                ContextHunk(
                    old_start=hunk.old_start,
                    old_count=hunk.old_count,
                    new_start=hunk.new_start,
                    new_count=hunk.new_count,
                    lines=lines,
                )
            )
        kept_hunks = fitted
    return ContextFile(
        path=file.path,
        status=file.status,
        old_path=file.old_path,
        hunks=kept_hunks,
    )


def build_prepared_context(
    changed_files: list[ChangedFile],
    budget_estimated_tokens: int | None = None,
    chars_per_token: int | None = None,
    min_context_lines: int | None = None,
) -> PreparedContext:
    """Build a deterministic, budget-bounded context from changed files.

    Everything fits: all files are included in ranked order with full hunks.
    Otherwise files are filled by rank (non-fitting files are dropped and
    recorded), the top file is represented even if it must be trimmed, and the
    result is marked ``truncated``.
    """
    budget = (
        settings.context_budget_estimated_tokens
        if budget_estimated_tokens is None
        else budget_estimated_tokens
    )
    cpt = (
        settings.context_chars_per_token if chars_per_token is None else chars_per_token
    )
    min_ctx = (
        settings.context_min_context_lines
        if min_context_lines is None
        else min_context_lines
    )
    if budget <= 0:
        raise ValueError("budget_estimated_tokens must be a positive integer")
    if cpt <= 0:
        raise ValueError("chars_per_token must be a positive integer")
    if min_ctx < 0:
        raise ValueError("min_context_lines must be non-negative")

    ranked = rank_changed_files(changed_files)
    context_files = [_to_context_file(file) for file in ranked]

    total_chars = sum(_file_chars(file) for file in context_files)
    total_tokens = estimate_tokens_for_chars(total_chars, cpt)
    if total_tokens <= budget:
        return PreparedContext(
            files=context_files,
            truncated=False,
            total_estimated_tokens=total_tokens,
            total_characters=total_chars,
            budget_estimated_tokens=budget,
        )

    budget_chars = budget * cpt
    included: list[ContextFile] = []
    dropped: list[str] = []
    acc = 0
    for file in context_files:
        chars = _file_chars(file)
        if acc + chars <= budget_chars:
            included.append(file)
            acc += chars
            continue
        if acc == 0:
            trimmed = _trim_file_to_budget(file, budget_chars, min_ctx)
            included.append(trimmed)
            acc += _file_chars(trimmed)
        else:
            dropped.append(file.path)

    return PreparedContext(
        files=included,
        truncated=True,
        truncated_files=dropped,
        total_estimated_tokens=estimate_tokens_for_chars(acc, cpt),
        total_characters=acc,
        budget_estimated_tokens=budget,
    )