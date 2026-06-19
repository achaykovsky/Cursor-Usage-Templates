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

from pathlib import Path



from mcp_classify import classify_tool_name, load_mcp_heuristics





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



    policy_dir = Path(__file__).resolve().parent

    policy_file = args.policy_file or policy_dir / "mcp_tools.json"

    heuristics_path = args.heuristics_policy or policy_dir / "default.policy.json"



    heuristics_policy: dict = {}

    if heuristics_path.is_file():

        heuristics_policy = json.loads(heuristics_path.read_text(encoding="utf-8"))

    heuristics = load_mcp_heuristics(heuristics_policy)



    catalog: dict = {"version": 1, "servers": {}, "tool_arguments": {}}

    if policy_file.is_file():

        catalog = json.loads(policy_file.read_text(encoding="utf-8"))



    servers = catalog.setdefault("servers", {})

    for server_dir in sorted(args.mcps_dir.iterdir()):

        tools_dir = server_dir / "tools"

        if not tools_dir.is_dir():

            continue

        server_name = server_dir.name

        entry = servers.setdefault(server_name, {})

        tools_map = entry.setdefault("tools", {})

        for tool_file in sorted(tools_dir.glob("*.json")):

            data = json.loads(tool_file.read_text(encoding="utf-8"))

            name = data.get("name") or tool_file.stem

            if name not in tools_map:

                risk = classify_tool_name(name, heuristics)

                if risk != "unknown":

                    tools_map[name] = risk



    text = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"

    if args.write:

        policy_file.write_text(text, encoding="utf-8")

        print(f"Updated {policy_file}")

    else:

        print(text)

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

