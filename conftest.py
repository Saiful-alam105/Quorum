"""Root conftest: make the project's top-level packages importable for pytest.

Running plain ``pytest`` (the .exe entry point) does not add the repository
root to ``sys.path``, so ``quorum`` and ``evaluation`` are not importable by
test modules. This conftest ensures both are always on the path, matching the
behaviour of ``python -m pytest`` (which adds the current directory).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for package_dir in ("src", "evaluation"):
    path = str(ROOT / package_dir)
    if path not in sys.path:
        sys.path.insert(0, path)