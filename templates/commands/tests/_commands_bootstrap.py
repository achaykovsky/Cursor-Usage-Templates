"""Bootstrap templates/commands tests for direct script and pytest execution.

Ensures ``templates/commands`` (and optionally ``templates/hooks/policy``) are on
``sys.path`` before test modules import command or policy code. Re-exports
``run_test_file`` so each test file needs only one support import.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _pytest_entry import run_test_file, runtime_ok

COMMANDS_DIR = Path(__file__).resolve().parents[1]
POLICY_DIR = Path(__file__).resolve().parents[2] / "hooks" / "policy"


def ensure_commands_path() -> None:
    """Insert templates/commands on sys.path when pytest pythonpath is unavailable."""
    entry = str(COMMANDS_DIR)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def ensure_policy_path() -> None:
    """Insert templates/hooks/policy on sys.path for policy module imports."""
    entry = str(POLICY_DIR)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def ensure_paths(*, policy: bool = False) -> None:
    """Ensure command imports work; add policy path when tests import hook policy code."""
    ensure_commands_path()
    if policy:
        ensure_policy_path()


__all__ = [
    "COMMANDS_DIR",
    "POLICY_DIR",
    "ensure_commands_path",
    "ensure_paths",
    "ensure_policy_path",
    "run_test_file",
    "runtime_ok",
]
