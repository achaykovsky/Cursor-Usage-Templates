"""Shared pytest fixtures for hook policy tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

POLICY_DIR = Path(__file__).resolve().parent.parent / "policy"
sys.path.insert(0, str(POLICY_DIR))

import hook_policy  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_policy_cache() -> None:
    hook_policy.clear_policy_cache()
    yield
    hook_policy.clear_policy_cache()
