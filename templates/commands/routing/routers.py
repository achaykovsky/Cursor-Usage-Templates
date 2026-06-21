"""Markdown formatters for agent, skill, and session routing."""

from __future__ import annotations

import logging

from routing._keywords import (
    AGENT_KEYWORDS,
    ALWAYS_APPLIED_RULES,
    GATE_HOOKS,
    SKILL_KEYWORDS,
    norm,
    pick_best,
    score_keywords,
)
from routing.model import classify_model_category
from routing.rules import rules_for_paths

logger = logging.getLogger(__name__)


def route_agent(task: str) -> str:
    logger.info("route_agent_enter", extra={"task_length": len(task)})
    primary, score = pick_best(task, AGENT_KEYWORDS, "REVIEWER")
    secondary = ""
    if primary.startswith("FE_") and score > 0:
        secondary = "FE_CODE_REVIEWER for review handoff"
    elif primary in {"BACKEND_PYTHON", "BACKEND_GO"}:
        secondary = "TESTER for test follow-up"
    elif primary == "INCIDENT":
        secondary = "TESTER after root cause fix"

    avoid: list[str] = []
    if primary.startswith("FE_"):
        avoid.append("TESTER (use FE_TEST_ENGINEER for UI tests)")
    if primary in {"SECURITY", "ARCHITECT"}:
        avoid.append("routine code edits — reserve for decisions/audits")

    lines = [
        "| Field | Content |",
        "|-------|---------|",
        f"| **Primary** | `@agent({primary})` — keyword match score {score} |",
        f"| **Optional secondary** | {secondary or '—'} |",
        "| **Escalation** | Switch if domain changes (FE → BE) or task needs audit/architecture |",
        f"| **Avoid** | {', '.join(avoid) if avoid else '—'} |",
    ]
    logger.info("route_agent_exit", extra={"primary": primary, "score": score})
    return "\n".join(lines)


def route_skill(task: str, phase: str = "") -> str:
    logger.info("route_skill_enter", extra={"task_length": len(task), "phase": phase or "(none)"})
    phase = norm(phase)
    if phase == "review":
        primary = "review-pull-request"
    elif phase == "release":
        primary = "validate-pre-deploy"
    elif phase == "debug":
        primary = "reproduce-and-document-failure"
    elif phase == "design":
        primary = "design-feature-from-requirements"
    else:
        primary, _ = pick_best(task, SKILL_KEYWORDS, "design-feature-from-requirements")

    sequence: list[str] = []
    t = norm(task)
    if "bug" in t or phase == "debug":
        sequence = ["reproduce-and-document-failure", "fix-bug-systematically", "add-tests-for-change"]
    elif any(k in t for k in ("api", "breaking", "version")):
        sequence = ["check-api-backward-compatibility", "implement-or-extend-api-surface"]
    elif any(k in t for k in ("frontend", "react", "ui")):
        sequence = ["orchestrate-frontend-delivery"]

    orchestrator = "orchestrate-frontend-delivery" if "orchestrate-frontend-delivery" in sequence else "—"
    escalation = "@agent(INCIDENT)" if "production" in t or "incident" in t else "—"

    lines = [
        "| Field | Content |",
        "|-------|---------|",
        f"| **Primary skill** | `{primary}` |",
        f"| **Sequence** | {' → '.join(sequence[:4]) if sequence else '—'} |",
        f"| **Orchestrator** | {orchestrator} |",
        f"| **Escalation agent** | {escalation} |",
        "| **Skip** | Near-duplicate skills not matched by keywords |",
    ]
    logger.info("route_skill_exit", extra={"primary_skill": primary, "sequence_length": len(sequence)})
    return "\n".join(lines)


def route_session(task: str, paths: list[str]) -> str:
    logger.info("route_session_enter", extra={"task_length": len(task), "path_count": len(paths)})
    primary_skill, _ = pick_best(task, SKILL_KEYWORDS, "design-feature-from-requirements")
    primary_agent, _ = pick_best(task, AGENT_KEYWORDS, "REVIEWER")
    model_cat = classify_model_category(task)

    rows = [
        ("1", "skill", primary_skill, "Best keyword match for task"),
        ("2", "@agent", primary_agent, "Domain owner if skill needs persona"),
        ("3", "model", model_cat, "Tier from models-catalog routing"),
    ]
    if paths:
        top_rules = rules_for_paths(paths[:1]).get(paths[0], [])
        if top_rules:
            rows.append(("4", "rules", ", ".join(top_rules[:3]), "File-scoped from RULES.md"))

    t = norm(task)
    hook_hits = [name for name, kws in GATE_HOOKS if score_keywords(t, kws) > 0]
    if not hook_hits and any(k in t for k in ("git", "shell", "push", "deploy")):
        hook_hits = ["validate-git-commands", "validate-pre-push", "block-destructive-shell"]

    lines = [
        "### 1. Route table",
        "",
        "| Step | Layer | Choice | Why (one line) |",
        "|------|-------|--------|----------------|",
    ]
    for step, layer, choice, why in rows[:6]:
        lines.append(f"| {step} | {layer} | {choice} | {why} |")

    lines.extend(["", "### 2. Rules note", ""])
    if paths:
        scoped = rules_for_paths(paths)
        for path in paths[:5]:
            rules = scoped.get(path, [])
            lines.append(f"- `{path}` → {', '.join(rules) if rules else 'always-applied only'}")
    else:
        lines.append("- " + ", ".join(ALWAYS_APPLIED_RULES))

    lines.extend(["", "### 3. Hooks note", ""])
    if hook_hits:
        for hook in hook_hits[:5]:
            lines.append(f"- `{hook}` may gate shell/MCP/read operations")
    else:
        lines.append("- Standard safety hooks apply on shell/MCP (see HOOKS_USAGE.md)")

    lines.extend(
        [
            "",
            "### 4. Token tips",
            "",
            "- `@` reference task files instead of pasting catalogs",
            "- Use one routing script output, not full SKILLS.md / RULES.md",
            "- Name `@agent(NAME)` or skill in the first message",
            "",
            "### 5. Do not use",
            "",
            "- Pasting full agent prompts or SKILL.md bodies",
            "- Listing every FE skill when `orchestrate-frontend-delivery` suffices",
        ]
    )
    logger.info(
        "route_session_exit",
        extra={
            "primary_skill": primary_skill,
            "primary_agent": primary_agent,
            "model_category": model_cat,
            "hook_hit_count": len(hook_hits),
        },
    )
    return "\n".join(lines)
