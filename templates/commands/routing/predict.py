"""Prompt keyword skill matching and combined predict output."""

from __future__ import annotations

import logging

from routing._keywords import SKILL_KEYWORDS, score_keywords
from routing.rules import match_rules_from_prompt

logger = logging.getLogger(__name__)


def match_skills_from_prompt(task: str, min_score: int = 1) -> list[str]:
    """Return skill names whose keyword score meets min_score, highest score first."""
    logger.info("match_skills_from_prompt_enter", extra={"task_length": len(task), "min_score": min_score})
    scored: list[tuple[int, str]] = []
    for name, keywords in SKILL_KEYWORDS:
        score = score_keywords(task, keywords)
        if score >= min_score:
            scored.append((score, name))
    scored.sort(key=lambda item: (-item[0], item[1]))
    matched = [name for _, name in scored]
    logger.info("match_skills_from_prompt_exit", extra={"match_count": len(matched)})
    return matched


def predict_prompt_context(prompt: str, min_score: int = 1) -> dict[str, list[str]]:
    """Predict skills and rules from prompt keywords — SSOT for hook prompt-context logging."""
    logger.info("predict_prompt_context_enter", extra={"prompt_length": len(prompt), "min_score": min_score})
    result = {
        "predicted_skills": match_skills_from_prompt(prompt, min_score),
        "predicted_rules": match_rules_from_prompt(prompt, min_score),
    }
    logger.info(
        "predict_prompt_context_exit",
        extra={
            "skill_count": len(result["predicted_skills"]),
            "rule_count": len(result["predicted_rules"]),
        },
    )
    return result
