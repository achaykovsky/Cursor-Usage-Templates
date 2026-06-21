"""Load sync-cursor.py as sync_cursor for test imports.

Shared by conftest.py and test modules so bootstrap runs whether pytest loads
conftest first or a test file is executed directly (e.g. Code Runner).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SYNC_CURSOR_PATH = Path(__file__).resolve().parents[1] / "sync-cursor.py"


def load_sync_cursor() -> ModuleType:
    """Return the sync_cursor module, loading sync-cursor.py once if needed."""
    cached = sys.modules.get("sync_cursor")
    if cached is not None:
        return cached

    spec = importlib.util.spec_from_file_location("sync_cursor", SYNC_CURSOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load sync-cursor from {SYNC_CURSOR_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_cursor"] = module
    spec.loader.exec_module(module)
    return module
