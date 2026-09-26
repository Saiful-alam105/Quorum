"""Load the manual Pull Request evaluation dataset (Phase 18).

Each dataset entry is a JSON file under ``evaluation/dataset/`` describing one
manually labeled Pull Request: the changed file contents (so the analysis can
run offline), the labeled security findings, and optional labeled test/coverage
expectations.
"""

from __future__ import annotations

import json
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent / "dataset"

REQUIRED_FIELDS = ("id", "repository", "pr_number", "files", "labeled_findings")


def _validate(entry: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in entry]
    if missing:
        raise ValueError(f"evaluation entry missing fields: {missing}")
    if not isinstance(entry["files"], dict) or not entry["files"]:
        raise ValueError(
            "evaluation entry 'files' must be a non-empty dict of path -> content"
        )
    if not isinstance(entry["labeled_findings"], list):
        raise ValueError("evaluation entry 'labeled_findings' must be a list")


def load_entry(path: Path) -> dict:
    """Load and validate a single dataset entry from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    _validate(data)
    return data


def load_dataset(directory: Path | None = None) -> list[dict]:
    """Load all dataset entries from a directory, sorted by id."""
    directory = Path(directory) if directory else DATASET_DIR
    entries = []
    for path in sorted(directory.glob("*.json")):
        if path.name.startswith("_"):
            continue
        entries.append(load_entry(path))
    return entries