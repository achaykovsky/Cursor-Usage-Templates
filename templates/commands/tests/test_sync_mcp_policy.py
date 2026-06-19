"""Tests for sync_mcp_policy.py."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

POLICY_DIR = Path(__file__).resolve().parents[2] / "hooks" / "policy"
sys.path.insert(0, str(POLICY_DIR))

from mcp_classify import classify_tool_name, load_mcp_heuristics  # noqa: E402
import sync_mcp_policy  # noqa: E402


@pytest.fixture
def mcps_dir(tmp_path: Path) -> Path:
    root = tmp_path / "mcps" / "user-test" / "tools"
    root.mkdir(parents=True)
    (root / "get_item.json").write_text(json.dumps({"name": "get_item"}), encoding="utf-8")
    (root / "create_item.json").write_text(json.dumps({"name": "create_item"}), encoding="utf-8")
    (root / "opaque.json").write_text(json.dumps({"name": "opaque_xyz"}), encoding="utf-8")
    return tmp_path / "mcps"


def test_classify_via_shared_module() -> None:
    policy = json.loads((POLICY_DIR / "default.policy.json").read_text(encoding="utf-8"))
    heuristics = load_mcp_heuristics(policy)
    assert classify_tool_name("get_item", heuristics) == "read"
    assert classify_tool_name("create_item", heuristics) == "write"
    assert classify_tool_name("opaque_xyz", heuristics) == "unknown"


def test_dry_run_stdout_json(mcps_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old_argv = sys.argv
    sys.argv = [
        "sync_mcp_policy.py",
        "--mcps-dir",
        str(mcps_dir),
        "--policy-file",
        str(mcps_dir.parent / "out.json"),
    ]
    try:
        assert sync_mcp_policy.main() == 0
    finally:
        sys.argv = old_argv
    out = capsys.readouterr().out
    data = json.loads(out)
    tools = data["servers"]["user-test"]["tools"]
    assert tools["get_item"] == "read"
    assert tools["create_item"] == "write"
    assert "opaque_xyz" not in tools


def test_write_merges_unknown_tools(mcps_dir: Path, tmp_path: Path) -> None:
    policy_file = tmp_path / "mcp_tools.json"
    policy_file.write_text(
        json.dumps({"version": 1, "servers": {}, "tool_arguments": {}}), encoding="utf-8"
    )
    old_argv = sys.argv
    sys.argv = [
        "sync_mcp_policy.py",
        "--mcps-dir",
        str(mcps_dir),
        "--policy-file",
        str(policy_file),
        "--write",
    ]
    try:
        assert sync_mcp_policy.main() == 0
    finally:
        sys.argv = old_argv
    data = json.loads(policy_file.read_text(encoding="utf-8"))
    tools = data["servers"]["user-test"]["tools"]
    assert tools["get_item"] == "read"
    assert tools["create_item"] == "write"
    assert "opaque_xyz" not in tools


def test_existing_tools_not_overwritten(mcps_dir: Path, tmp_path: Path) -> None:
    policy_file = tmp_path / "mcp_tools.json"
    policy_file.write_text(
        json.dumps(
            {
                "version": 1,
                "servers": {"user-test": {"tools": {"get_item": "write"}}},
                "tool_arguments": {},
            }
        ),
        encoding="utf-8",
    )
    old_argv = sys.argv
    sys.argv = [
        "sync_mcp_policy.py",
        "--mcps-dir",
        str(mcps_dir),
        "--policy-file",
        str(policy_file),
        "--write",
    ]
    try:
        sync_mcp_policy.main()
    finally:
        sys.argv = old_argv
    data = json.loads(policy_file.read_text(encoding="utf-8"))
    assert data["servers"]["user-test"]["tools"]["get_item"] == "write"
