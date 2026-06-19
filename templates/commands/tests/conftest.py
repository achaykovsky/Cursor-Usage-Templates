"""Shared pytest fixtures for sync command tests."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MINIMAL_TEMPLATES = FIXTURES / "minimal_templates"
SYNC_CURSOR_PATH = Path(__file__).resolve().parents[1] / "sync-cursor.py"

_spec = importlib.util.spec_from_file_location("sync_cursor", SYNC_CURSOR_PATH)
assert _spec and _spec.loader
sync_cursor = importlib.util.module_from_spec(_spec)
sys.modules["sync_cursor"] = sync_cursor
_spec.loader.exec_module(sync_cursor)


@pytest.fixture
def tmp_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(sync_cursor.Path, "home", lambda: home)
    templates = tmp_path / "templates"
    shutil.copytree(MINIMAL_TEMPLATES, templates)
    return tmp_path
