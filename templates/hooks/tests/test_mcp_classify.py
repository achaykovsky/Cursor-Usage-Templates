"""Tests for shared MCP tool name classification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

POLICY_DIR = Path(__file__).resolve().parent.parent / "policy"
sys.path.insert(0, str(POLICY_DIR))

from mcp_classify import classify_tool_name, load_mcp_heuristics  # noqa: E402


@pytest.fixture
def default_heuristics():
    policy = json.loads((POLICY_DIR / "default.policy.json").read_text(encoding="utf-8"))
    return load_mcp_heuristics(policy)


def test_mcp_auth_is_read(default_heuristics) -> None:
    assert classify_tool_name("mcp_auth", default_heuristics) == "read"


def test_list_releases_is_read(default_heuristics) -> None:
    assert classify_tool_name("list_releases", default_heuristics) == "read"


def test_create_foo_is_write(default_heuristics) -> None:
    assert classify_tool_name("create_foo", default_heuristics) == "write"


def test_opaque_is_unknown(default_heuristics) -> None:
    assert classify_tool_name("opaque_xyz", default_heuristics) == "unknown"


def test_write_name_pattern(default_heuristics) -> None:
    assert classify_tool_name("pull_request_merge", default_heuristics) == "write"


def test_all_read_prefixes_smoke(default_heuristics) -> None:
    for prefix in default_heuristics.read_prefixes:
        assert classify_tool_name(f"{prefix}item", default_heuristics) == "read"


def test_all_write_prefixes_smoke(default_heuristics) -> None:
    for prefix in default_heuristics.write_prefixes:
        assert classify_tool_name(f"{prefix}item", default_heuristics) == "write"
