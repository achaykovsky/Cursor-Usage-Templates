"""Deterministic routing helpers for Cursor templates (session, agent, skill, model, rules)."""

from __future__ import annotations

import logging

from routing._keywords import (
    AGENT_KEYWORDS,
    ALWAYS_APPLIED_RULES,
    FILE_SCOPED_RULES,
    GATE_HOOKS,
    MODEL_CATEGORY_KEYWORDS,
    PROMPT_RULE_KEYWORDS,
    SKILL_KEYWORDS,
    RuleEntry,
    pick_best,
)
from routing._paths import COMMANDS_DIR, TEMPLATES_ROOT
from routing.cli import build_parser, main, run_cli
from routing.model import classify_model_category, load_models_catalog, route_model
from routing.predict import match_skills_from_prompt, predict_prompt_context
from routing.routers import route_agent, route_session, route_skill
from routing.rules import match_rules_from_prompt, overlap_summary, path_matches_glob, route_rules, rules_for_paths

logger = logging.getLogger(__name__)

__all__ = [
    "AGENT_KEYWORDS",
    "ALWAYS_APPLIED_RULES",
    "COMMANDS_DIR",
    "FILE_SCOPED_RULES",
    "GATE_HOOKS",
    "MODEL_CATEGORY_KEYWORDS",
    "PROMPT_RULE_KEYWORDS",
    "RuleEntry",
    "SKILL_KEYWORDS",
    "TEMPLATES_ROOT",
    "build_parser",
    "classify_model_category",
    "load_models_catalog",
    "logger",
    "main",
    "match_rules_from_prompt",
    "match_skills_from_prompt",
    "overlap_summary",
    "path_matches_glob",
    "pick_best",
    "predict_prompt_context",
    "route_agent",
    "route_model",
    "route_rules",
    "route_session",
    "route_skill",
    "rules_for_paths",
    "run_cli",
]
