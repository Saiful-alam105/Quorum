"""Context selection: deterministic importance ordering for Phase 7.

Changed content is ranked purely on evidence of change: files with more
changed lines are more important, then files with more added lines, then
alphabetically by path. Hunks follow the same change-volume rule with file
position as the tie-break. Ranking is deterministic so the same PR always
produces the same order. Budget allocation and truncation build on these
rankings in a later chunk.
"""

from quorum.analysis.diff import LINE_ADDED, LINE_REMOVED, ChangedFile, DiffHunk


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