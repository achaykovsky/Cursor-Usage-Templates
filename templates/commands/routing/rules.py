"""File-path and prompt-text rule matching."""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path, PurePosixPath

from routing._keywords import (
    ALWAYS_APPLIED_RULES,
    FILE_SCOPED_RULES,
    PROMPT_RULE_KEYWORDS,
    score_keywords,
)

logger = logging.getLogger(__name__)


def path_matches_glob(path: str, pattern: str) -> bool:
    posix = path.replace("\\", "/")
    if "**" in pattern:
        return PurePosixPath(posix).match(pattern)
    return fnmatch.fnmatch(posix, pattern)


def rules_for_paths(paths: list[str]) -> dict[str, list[str]]:
    logger.info("rules_for_paths_enter", extra={"path_count": len(paths)})
    result: dict[str, list[str]] = {}
    for path in paths:
        matches: list[str] = []
        for rule in FILE_SCOPED_RULES:
            if any(path_matches_glob(path, glob) for glob in rule.globs):
                matches.append(rule.name)
        result[path] = sorted(set(matches))
    logger.info("rules_for_paths_exit", extra={"matched_paths": len(result)})
    return result


def overlap_summary(paths: list[str], scoped: dict[str, list[str]]) -> str:
    if not paths:
        return "No file paths provided — only always-applied rules apply."
    primary = paths[0]
    ext = Path(primary).suffix.lower()
    rules = set(scoped.get(primary, []))
    if ext == ".py":
        return (
            f"Python file `{primary}` stacks always-applied rules with "
            f"{', '.join(rules) or 'no file-scoped matches'}."
        )
    if ext in {".tsx", ".jsx", ".vue"}:
        return (
            f"Frontend file `{primary}` stacks always-applied rules with "
            f"{', '.join(rules) or 'no file-scoped matches'}."
        )
    return f"`{primary}` matches: {', '.join(rules) or 'none'} plus always-applied rules."


def match_rules_from_prompt(prompt: str, min_score: int = 1) -> list[str]:
    """Return always-applied rules plus file-scoped rules whose keywords match the prompt."""
    logger.info("match_rules_from_prompt_enter", extra={"prompt_length": len(prompt), "min_score": min_score})
    rules: list[str] = list(ALWAYS_APPLIED_RULES)
    seen = set(rules)
    scored: list[tuple[int, str]] = []
    for name, keywords in PROMPT_RULE_KEYWORDS:
        if name in seen:
            continue
        score = score_keywords(prompt, keywords)
        if score >= min_score:
            scored.append((score, name))
    scored.sort(key=lambda item: (-item[0], item[1]))
    for _, name in scored:
        if name not in seen:
            rules.append(name)
            seen.add(name)
    logger.info("match_rules_from_prompt_exit", extra={"rule_count": len(rules)})
    return rules


def route_rules(paths: list[str]) -> str:
    logger.info("route_rules_enter", extra={"path_count": len(paths)})
    scoped = rules_for_paths(paths) if paths else {}
    lines = [
        "### 1. Always-applied rules",
        "",
        ", ".join(ALWAYS_APPLIED_RULES),
        "",
        "### 2. File-scoped rules",
        "",
        "| File or glob | Matching rules |",
        "|--------------|----------------|",
    ]
    if paths:
        for path in paths:
            rules = ", ".join(scoped.get(path, [])) or "—"
            lines.append(f"| `{path}` | {rules} |")
    else:
        lines.append("| (none) | Provide paths with `--files` |")

    lines.extend(
        [
            "",
            "### 3. Overlap summary",
            "",
            overlap_summary(paths, scoped),
            "",
            "### 4. Authoring note",
            "",
        ]
    )
    if any("SKILL.md" in p for p in paths):
        lines.append("Editing SKILL.md → also apply `skills-consistency.mdc`.")
    else:
        lines.append("If editing `.cursor/skills/**/SKILL.md`, note `skills-consistency.mdc`.")
    logger.info("route_rules_exit", extra={"path_count": len(paths)})
    return "\n".join(lines)
