"""Deterministic context sizing: exact character counts and token estimates.

Phase 7 has no tokenizer dependency, so context size is measured as exact
characters (Python string length) plus an estimated token count computed as
``ceil(characters / chars_per_token)`` with a configurable divisor
(``CONTEXT_CHARS_PER_TOKEN``, default 4).

Sizing is content-only: only line content contributes characters. File and
hunk headers are excluded, and token estimates are computed once on a total
rather than summed per piece, so rounding is deterministic and consistent.
"""

from typing import Sequence

from quorum.analysis.diff import ChangedFile, DiffHunk, DiffLine
from quorum.config import settings


def count_characters(text: str) -> int:
    """Return the exact number of characters in ``text``."""
    return len(text)


def estimate_tokens(text: str, chars_per_token: int | None = None) -> int:
    """Estimate the token count for ``text`` as ceil(chars / chars_per_token)."""
    cpt = settings.context_chars_per_token if chars_per_token is None else chars_per_token
    return estimate_tokens_for_chars(len(text), cpt)


def estimate_tokens_for_chars(
    characters: int, chars_per_token: int | None = None
) -> int:
    """Estimate the token count for a character total."""
    cpt = settings.context_chars_per_token if chars_per_token is None else chars_per_token
    if cpt <= 0:
        raise ValueError("chars_per_token must be a positive integer")
    if characters <= 0:
        return 0
    return (characters + cpt - 1) // cpt


def size_lines(lines: Sequence[DiffLine]) -> int:
    """Return the number of content characters across ``lines``."""
    return sum(len(line.content) for line in lines)


def size_hunk(hunk: DiffHunk) -> int:
    """Return the number of content characters in a hunk."""
    return size_lines(hunk.lines)


def size_changed_file(file: ChangedFile) -> int:
    """Return the number of content characters across all hunks of a file."""
    return sum(size_hunk(hunk) for hunk in file.hunks)