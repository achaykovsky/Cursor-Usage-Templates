#!/usr/bin/env python3
"""Validate subagent model frontmatter against models-catalog.json."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[3]
CATALOG_PATH = SKILL_DIR / "models-catalog.json"
SUBAGENTS_DIR = REPO_ROOT / "templates" / "agents" / "subagents"
SKIP_FILES = {"AGENTS.md", "AGENTS_USAGE.md"}


def main() -> int:
    logger.info("main_enter", extra={"catalog": str(CATALOG_PATH), "subagents_dir": str(SUBAGENTS_DIR)})
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    allowlist = set(catalog["cursor_allowlist"])
    tiers = catalog["tiers"]
    hints: dict[str, str] = catalog["agent_tier_hints"]

    def tier_primary(tier_key: str) -> str:
        return tiers[tier_key]["primary"]

    results: list[tuple[str, str, str, str | None, str | None, list[str]]] = []
    missing: list[tuple[str, str]] = []

    for path in sorted(SUBAGENTS_DIR.glob("*.md")):
        if path.name in SKIP_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        m_name = re.search(r"^name:\s*(\S+)", text, re.M)
        m_model = re.search(r"^model:\s*(\S+)", text, re.M)
        if not m_name or not m_model:
            missing.append((path.name, "missing name or model frontmatter"))
            continue

        name, model = m_name.group(1), m_model.group(1)
        issues: list[str] = []

        if name not in hints:
            issues.append(f"name {name!r} not in agent_tier_hints")
        else:
            expected_tier = hints[name]
            expected_model = tier_primary(expected_tier)
            if model not in allowlist:
                issues.append(f"model {model!r} not in cursor_allowlist")
            if model != expected_model:
                issues.append(
                    f"expected {expected_model!r} (tier {expected_tier}), got {model!r}"
                )

        results.append(
            (
                path.name,
                name,
                model,
                hints.get(name),
                tier_primary(hints[name]) if name in hints else None,
                issues,
            )
        )

    print("=== SUBAGENT MODEL VALIDATION ===")
    print(f"Catalog: {CATALOG_PATH.relative_to(REPO_ROOT)}")
    print(f"Subagents dir: {SUBAGENTS_DIR.relative_to(REPO_ROOT)}")
    print()

    ok = [r for r in results if not r[5]]
    bad = [r for r in results if r[5]]
    print(f"Total subagents checked: {len(results)}")
    print(f"Valid: {len(ok)}")
    print(f"Invalid: {len(bad)}")
    if missing:
        print(f"Missing frontmatter: {len(missing)}")
        for item in missing:
            print(f"  - {item[0]}: {item[1]}")
    print()

    if bad:
        print("FAILURES:")
        for r in bad:
            print(f"  {r[0]} ({r[1]}): {'; '.join(r[5])}")
        print()

    print("DETAIL:")
    for r in results:
        status = "OK" if not r[5] else "FAIL"
        tier = r[3] or "?"
        print(f"  [{status}] {r[1]:28} model={r[2]:35} tier={tier}")

    catalog_agents = set(hints)
    file_agents = {r[1] for r in results}
    orphan_hints = sorted(catalog_agents - file_agents)
    orphan_files = sorted(file_agents - catalog_agents)

    if orphan_hints:
        print()
        print("agent_tier_hints without subagent file:")
        for name in orphan_hints:
            print(f"  - {name} -> {hints[name]} / {tier_primary(hints[name])}")

    if orphan_files:
        print()
        print("Subagent files without agent_tier_hints entry:")
        for name in orphan_files:
            print(f"  - {name}")

    exit_code = 1 if bad or missing or orphan_files else 0
    logger.info(
        "main_exit",
        extra={
            "total_checked": len(results),
            "valid": len(ok),
            "invalid": len(bad),
            "missing_frontmatter": len(missing),
            "orphan_files": len(orphan_files),
            "exit_code": exit_code,
        },
    )
    return exit_code


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
