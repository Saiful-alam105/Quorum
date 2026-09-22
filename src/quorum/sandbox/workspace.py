"""Sandbox workspace assembly (Phase 11).

Builds the read-only workspace that gets mounted into the container: the
pull request's changed files (reusing the Semgrep scan-directory assembly so
both stages agree on which files are eligible) plus a safe writer for
generated test files that Phase 12 will use.
"""

from pathlib import Path, PurePath
from typing import Awaitable, Callable

from quorum.analysis.diff import ChangedFile
from quorum.analysis.semgrep import build_scan_directory


async def build_sandbox_workspace(
    changed_files: list[ChangedFile],
    fetch_content: Callable[[str, str], Awaitable[str]],
    head_sha: str,
    workspace_dir: str | Path,
) -> Path:
    """Write the changed files of the pull request into ``workspace_dir``.

    Deleted and binary files are skipped; paths that could escape the
    workspace (absolute or ``..`` segments) are skipped. The caller owns the
    directory lifecycle.
    """
    return await build_scan_directory(
        changed_files, fetch_content, head_sha, workspace_dir
    )


def write_generated_test(workspace_dir: str | Path, path: str, content: str) -> Path:
    """Write a generated test file into the workspace.

    Raises :class:`ValueError` for absolute paths or paths containing ``..``
    segments so untrusted generated test names cannot escape the workspace.
    """
    pure = PurePath(path)
    if pure.is_absolute() or any(segment == ".." for segment in pure.parts):
        raise ValueError(f"unsafe generated test path: {path}")
    root = Path(workspace_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target