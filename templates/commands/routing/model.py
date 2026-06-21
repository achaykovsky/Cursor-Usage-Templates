"""Model catalog loading and model-tier routing."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from routing._keywords import MODEL_CATEGORY_KEYWORDS, score_keywords
from routing._paths import TEMPLATES_ROOT

logger = logging.getLogger(__name__)


def load_models_catalog(root: Path | None = None) -> dict[str, Any]:
    path = (root or TEMPLATES_ROOT) / "skills/shared-practices/route-task-to-model/models-catalog.json"
    logger.info("load_models_catalog_enter", extra={"catalog_path": str(path)})
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(
            "load_models_catalog_failed",
            extra={"catalog_path": str(path), "error_type": type(exc).__name__},
        )
        raise
    logger.info("load_models_catalog_exit", extra={"tier_count": len(catalog.get("tiers", {}))})
    return catalog


def classify_model_category(task: str) -> str:
    logger.info("classify_model_category_enter", extra={"task_length": len(task)})
    for category, keywords in MODEL_CATEGORY_KEYWORDS:
        if score_keywords(task, keywords) > 0:
            logger.info("classify_model_category_exit", extra={"category": category})
            return category
    logger.info("classify_model_category_exit", extra={"category": "general"})
    return "general"


def route_model(task: str) -> str:
    logger.info("route_model_enter", extra={"task_length": len(task)})
    catalog = load_models_catalog()
    category = classify_model_category(task)
    tier_key = catalog.get("task_routing", {}).get(category, "mid_tier")
    tier = catalog.get("tiers", {}).get(tier_key, {})
    slug = tier.get("primary", catalog.get("cursor_allowlist", ["claude-4.6-sonnet-medium-thinking"])[0])
    tradeoffs = tier.get("tradeoffs", "Balanced default.")

    escalate = "Multi-file design, security architecture, or repeated failures" if category != "architectural" else "—"

    lines = [
        "| Field | Content |",
        "|-------|---------|",
        f"| **Category** | `{category}` |",
        f"| **Tier** | {tier_key} |",
        f"| **Slug** | `{slug}` |",
        f"| **Why** | {tradeoffs} |",
        "| **Execution** | Scope to task files; validate with tests or review skill |",
        f"| **Escalate when** | {escalate} |",
    ]
    logger.info("route_model_exit", extra={"category": category, "tier_key": tier_key, "slug": slug})
    return "\n".join(lines)
