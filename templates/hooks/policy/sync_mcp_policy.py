#!/usr/bin/env python3
"""Generate MCP tool risk entries from Cursor mcps/*/tools/*.json descriptors.

Usage:
  python sync_mcp_policy.py --mcps-dir <path-to-mcps> [--write]

Without --write, prints JSON patch to stdout. With --write, merges unknown tools into mcp_tools.json.
Heuristic prefixes are loaded from default.policy.json (or --policy-file) via mcp_classify.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from mcp_classify import classify_tool_name, load_mcp_heuristics

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed mcp_tools.json from MCP tool descriptors using policy heuristics."
    )
    parser.add_argument("--mcps-dir", required=True, type=Path)
    parser.add_argument(
        "--policy-file",
        type=Path,
        default=None,
        help="mcp_tools.json output path (default: sibling mcp_tools.json)",
    )
    parser.add_argument(
        "--heuristics-policy",
        type=Path,
        default=None,
        help="default.policy.json for MCP heuristics (default: sibling default.policy.json)",
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    logger.info(
        "main_enter",
        extra={"mcps_dir": str(args.mcps_dir), "write": args.write},
    )

    policy_dir = Path(__file__).resolve().parent
    policy_file = args.policy_file or policy_dir / "mcp_tools.json"
    heuristics_path = args.heuristics_policy or policy_dir / "default.policy.json"

    heuristics_policy: dict[str, object] = {}
    if heuristics_path.is_file():
        try:
            heuristics_policy = json.loads(heuristics_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error(
                "heuristics_policy_load_failed",
                extra={"path": str(heuristics_path), "error_type": type(exc).__name__},
            )
            raise
    else:
        logger.info(
            "heuristics_policy_missing",
            extra={"path": str(heuristics_path), "using_defaults": True},
        )
    heuristics = load_mcp_heuristics(heuristics_policy)

    catalog: dict[str, object] = {"version": 1, "servers": {}, "tool_arguments": {}}
    if policy_file.is_file():
        try:
            catalog = json.loads(policy_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error(
                "policy_file_load_failed",
                extra={"path": str(policy_file), "error_type": type(exc).__name__},
            )
            raise

    servers = catalog.setdefault("servers", {})
    if not isinstance(servers, dict):
        servers = {}
        catalog["servers"] = servers

    new_tools = 0
    for server_dir in sorted(args.mcps_dir.iterdir()):
        tools_dir = server_dir / "tools"
        if not tools_dir.is_dir():
            continue
        server_name = server_dir.name
        entry = servers.setdefault(server_name, {})
        if not isinstance(entry, dict):
            entry = {}
            servers[server_name] = entry
        tools_map = entry.setdefault("tools", {})
        if not isinstance(tools_map, dict):
            tools_map = {}
            entry["tools"] = tools_map
        for tool_file in sorted(tools_dir.glob("*.json")):
            try:
                data = json.loads(tool_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.error(
                    "tool_descriptor_load_failed",
                    extra={"path": str(tool_file), "error_type": type(exc).__name__},
                )
                continue
            name = data.get("name") or tool_file.stem
            if name not in tools_map:
                risk = classify_tool_name(str(name), heuristics)
                if risk != "unknown":
                    tools_map[name] = risk
                    new_tools += 1
                    logger.info(
                        "tool_classified",
                        extra={"server": server_name, "tool": name, "risk": risk},
                    )

    text = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        policy_file.write_text(text, encoding="utf-8")
        print(f"Updated {policy_file}")
        logger.info("main_exit", extra={"write": True, "new_tools": new_tools, "policy_file": str(policy_file)})
    else:
        print(text)
        logger.info("main_exit", extra={"write": False, "new_tools": new_tools})
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
