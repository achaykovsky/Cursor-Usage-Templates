"""Shared pytest fixtures for sync command tests."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest

from _sync_bootstrap import load_sync_cursor

logger = logging.getLogger(__name__)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MINIMAL_TEMPLATES = FIXTURES / "minimal_templates"

sync_cursor = load_sync_cursor()


@pytest.fixture(autouse=True)
def _reset_sync_options() -> None:
    """Isolate dry-run/verbose state between tests (ContextVar-backed)."""
    sync_cursor.set_sync_options(dry_run=False, verbose=False)
    yield  # type: ignore[misc]
    sync_cursor.set_sync_options(dry_run=False, verbose=False)


@pytest.fixture
def tmp_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated project tree with minimal templates and a fake HOME for global sync modes."""
    logger.info("tmp_project_setup", extra={"tmp_path": str(tmp_path)})
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(sync_cursor.Path, "home", lambda: home)
    templates = tmp_path / "templates"
    shutil.copytree(MINIMAL_TEMPLATES, templates)
    logger.info("tmp_project_ready", extra={"project_root": str(tmp_path)})
    return tmp_path
