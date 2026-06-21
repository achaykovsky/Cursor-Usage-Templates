"""Run a test module via pytest from Code Runner or direct script execution.

Code Runner often uses VS Code's bundled Python 3.7 + pytest 3.x, which lacks
``tmp_path`` and other fixtures this suite expects. When the active interpreter
is too old, re-exec via ``py -3.13 -m pytest`` from the repo root so
``pyproject.toml`` ``pythonpath`` and ``testpaths`` apply.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _pytest_version_ok() -> bool:
    import pytest

    parts = pytest.__version__.split(".")
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    return (major, minor) >= (8, 0)


def _runtime_ok() -> bool:
    return sys.version_info >= (3, 10) and _pytest_version_ok()


def runtime_ok() -> bool:
    """True when the active interpreter satisfies project test requirements."""
    return _runtime_ok()


def _repo_root(test_file: str | Path) -> Path:
    return Path(test_file).resolve().parents[3]


def run_test_file(test_file: str) -> int:
    """Run *test_file* with pytest; delegate when the active runtime is too old."""
    if _runtime_ok():
        import pytest

        return pytest.main([test_file, "-q"])

    py_launcher = shutil.which("py")
    if py_launcher is None:
        raise SystemExit(
            "Python >=3.10 and pytest >=8.0 required. "
            f"Current: Python {sys.version.split()[0]}. "
            "Install Python 3.10+ or run: py -3.13 -m pytest <file>"
        )

    root = _repo_root(test_file)
    completed = subprocess.run(
        [py_launcher, "-3.13", "-m", "pytest", str(Path(test_file).resolve()), "-q"],
        cwd=root,
    )
    return completed.returncode
