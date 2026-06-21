"""Bootstrap templates/hooks tests for direct script and pytest execution."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parent.parent / "policy"
COMMANDS_DIR = Path(__file__).resolve().parents[2] / "commands"


def ensure_policy_path() -> None:
    """Insert templates/hooks/policy on sys.path when pytest pythonpath is unavailable."""
    entry = str(POLICY_DIR)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def ensure_commands_path() -> None:
    """Insert templates/commands when integration tests copy or invoke command scripts."""
    entry = str(COMMANDS_DIR)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def run_test_file(test_file: str) -> int:
    """Run *test_file* via shared pytest entry (delegates to py -3.13 when runtime is too old)."""
    runner_path = Path(__file__).resolve().parents[2] / "commands" / "tests" / "_pytest_entry.py"
    spec = importlib.util.spec_from_file_location("_pytest_entry", runner_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load pytest runner from {runner_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_test_file(test_file)


def runtime_ok() -> bool:
    """True when the active interpreter satisfies project test requirements."""
    runner_path = Path(__file__).resolve().parents[2] / "commands" / "tests" / "_pytest_entry.py"
    spec = importlib.util.spec_from_file_location("_pytest_entry", runner_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load pytest runner from {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.runtime_ok()


__all__ = [
    "COMMANDS_DIR",
    "POLICY_DIR",
    "ensure_commands_path",
    "ensure_policy_path",
    "run_test_file",
    "runtime_ok",
]
