"""Shared pytest fixtures for hook policy tests."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from _hooks_bootstrap import ensure_policy_path

logger = logging.getLogger(__name__)

ensure_policy_path()

import hook_policy  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_policy_cache() -> None:
    """Policy JSON is cached by mtime — reset between tests to avoid cross-test leakage."""
    logger.info("clear_policy_cache_fixture", extra={"phase": "setup"})
    hook_policy.clear_policy_cache()
    yield
    logger.info("clear_policy_cache_fixture", extra={"phase": "teardown"})
    hook_policy.clear_policy_cache()
