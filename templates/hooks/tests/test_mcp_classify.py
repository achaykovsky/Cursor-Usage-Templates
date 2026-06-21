"""Tests for shared MCP tool name classification.

mcp_classify.py is imported by both hook_policy and sync_mcp_policy; prefix
heuristics here define read vs write vs unknown for the entire MCP gate.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _hooks_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json
import sys
from pathlib import Path

import pytest

from _hooks_bootstrap import POLICY_DIR, ensure_policy_path, run_test_file

ensure_policy_path()

from mcp_classify import classify_tool_name, load_mcp_heuristics


@pytest.fixture
def default_heuristics():
    """Load heuristics from the shipped default.policy.json — same as production hooks."""
    policy = json.loads((POLICY_DIR / "default.policy.json").read_text(encoding="utf-8"))
    return load_mcp_heuristics(policy)


def test_mcp_auth_is_read(default_heuristics) -> None:
    """Auth handshake tools are read-only — blocking them would break MCP setup."""
    assert classify_tool_name("mcp_auth", default_heuristics) == "read"


def test_list_releases_is_read(default_heuristics) -> None:
    """list_* prefix maps to read so GitHub metadata queries stay allow-by-default."""
    assert classify_tool_name("list_releases", default_heuristics) == "read"


def test_create_foo_is_write(default_heuristics) -> None:
    """create_* prefix triggers write classification and downstream ask/deny modes."""
    assert classify_tool_name("create_foo", default_heuristics) == "write"


def test_opaque_is_unknown(default_heuristics) -> None:
    """Unrecognized names return unknown so hooks can prompt before uncataloged tools run."""
    assert classify_tool_name("opaque_xyz", default_heuristics) == "unknown"


def test_write_name_pattern(default_heuristics) -> None:
    """Compound write verbs (merge, deploy, etc.) match write suffix/pattern rules."""
    assert classify_tool_name("pull_request_merge", default_heuristics) == "write"


def test_all_read_prefixes_smoke(default_heuristics) -> None:
    """Every configured read prefix must classify consistently — catches policy typos."""
    for prefix in default_heuristics.read_prefixes:
        assert classify_tool_name(f"{prefix}item", default_heuristics) == "read"


def test_all_write_prefixes_smoke(default_heuristics) -> None:
    """Every configured write prefix must classify consistently — catches policy typos."""
    for prefix in default_heuristics.write_prefixes:
        assert classify_tool_name(f"{prefix}item", default_heuristics) == "write"


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
