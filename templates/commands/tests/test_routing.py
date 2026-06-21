"""Tests for routing.py.

Routing commands suggest agents, skills, models, rules, and session plans from
natural-language prompts. These tests lock in keyword heuristics so refactors
do not silently drop security or API-scoped rule recommendations.
"""

from __future__ import annotations

if __name__ == "__main__":
    from _commands_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import json

from _commands_bootstrap import ensure_paths, run_test_file

ensure_paths()

import routing as rt


def test_route_agent_security_task() -> None:
    """Security-related phrasing must route to the SECURITY subagent, not a generic reviewer."""
    # Act
    out = rt.route_agent("run security audit for OWASP issues")
    # Assert
    assert "SECURITY" in out


def test_route_skill_bug_sequence() -> None:
    """Debug phase should chain reproduce-then-fix skills — order matters for the session plan."""
    # Act
    out = rt.route_skill("fix bug in login", phase="debug")
    # Assert
    assert "reproduce-and-document-failure" in out
    assert "fix-bug-systematically" in out


def test_route_model_uses_catalog_slug() -> None:
    """Trivial edits should prefer lightweight catalog tiers to control cost."""
    # Act
    out = rt.route_model("simple typo fix in readme")
    # Assert — accept slug or tier label because output format may vary
    assert "composer-2.5-fast" in out or "lightweight" in out


def test_rules_for_python_path() -> None:
    """Python API paths must attach both language and contract rules — dual scope is intentional."""
    # Act
    scoped = rt.rules_for_paths(["src/api/router.py"])
    # Assert
    assert "python-backend.mdc" in scoped["src/api/router.py"]
    assert "api-contract.mdc" in scoped["src/api/router.py"]


def test_route_session_includes_table() -> None:
    """Full session routing emits a structured route table plus API workflow skill."""
    # Act
    out = rt.route_session("implement FastAPI endpoint", ["src/api/main.py"])
    # Assert
    assert "### 1. Route table" in out
    assert "implement-or-extend-api-surface" in out


def test_route_rules_always_applied() -> None:
    """security.mdc is always-applied even with an empty path list — fail-open would be unsafe."""
    # Act
    out = rt.route_rules([])
    # Assert
    assert "security.mdc" in out


def test_match_skills_cleanup_review_prompt() -> None:
    """Repo cleanup + code review prompts must match audit, review, and security skills."""
    prompt = (
        "go through all the python files to make code review and a clean-up. "
        "Validate duplications, dead code, redundancies, clean-code standards, security risks, vulns"
    )
    matched = rt.match_skills_from_prompt(prompt)
    assert "audit-codebase-cleanup" in matched
    assert "review-pull-request" in matched
    assert "security-scan-changes" in matched


def test_match_skills_comments_prompt() -> None:
    """Comment/documentation prompts must match add-comments-to-code."""
    matched = rt.match_skills_from_prompt("add comments and docstrings to explain this function")
    assert "add-comments-to-code" in matched


def test_match_skills_error_handling_prompt() -> None:
    """Error-handling prompts must match add-error-handling-to-code."""
    matched = rt.match_skills_from_prompt("add specific exception handling with custom domain errors")
    assert "add-error-handling-to-code" in matched


def test_skill_keywords_cover_catalog() -> None:
    """Every templates/skills/*/SKILL.md must have a SKILL_KEYWORDS entry."""
    from pathlib import Path

    from routing._keywords import SKILL_KEYWORDS

    root = Path(__file__).resolve().parents[2] / "skills"
    catalog = {p.parent.name for p in root.rglob("SKILL.md")}
    routed = {name for name, _ in SKILL_KEYWORDS}
    assert catalog == routed


def test_match_skills_release_keyword_split() -> None:
    """Release cut vs pre-deploy must route to distinct skills — bare 'release' is ambiguous."""
    changelog = rt.match_skills_from_prompt("changelog and version bump for the release")
    preflight = rt.match_skills_from_prompt("ready to deploy pre-flight check before production")
    assert "prepare-release" in changelog
    assert "validate-pre-deploy" not in changelog
    assert "validate-pre-deploy" in preflight
    assert "prepare-release" not in preflight


def test_match_skills_cleanup_vs_refactor_split() -> None:
    """Codebase cleanup audits must not collide with executable refactors."""
    cleanup = rt.match_skills_from_prompt("clean up dead code duplication and redundancies")
    refactor = rt.match_skills_from_prompt("refactor and rename extract function safely")
    assert "audit-codebase-cleanup" in cleanup
    assert "refactor-safely" not in cleanup
    assert "refactor-safely" in refactor
    assert "audit-codebase-cleanup" not in refactor


def test_match_rules_from_prompt_python_api() -> None:
    """Prompt-only inference must include always-applied rules plus keyword-scoped rules."""
    rules = rt.match_rules_from_prompt("implement FastAPI endpoint with pytest tests")
    assert "security.mdc" in rules
    assert "python-backend.mdc" in rules
    assert "api-contract.mdc" in rules
    assert "testing.mdc" in rules


def test_predict_prompt_context_json_shape() -> None:
    """predict subcommand shape is the contract for log-prompt-context hooks."""
    result = rt.predict_prompt_context("implement FastAPI endpoint with pytest tests")
    assert "predicted_skills" in result
    assert "predicted_rules" in result
    assert "implement-or-extend-api-surface" in result["predicted_skills"]
    assert "security.mdc" in result["predicted_rules"]


def test_predict_cli_emits_json() -> None:
    """CLI predict emits one JSON object on stdout."""
    import io
    import sys

    stdout = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = stdout
        assert rt.main(["predict", "--task", "security audit for OWASP"]) == 0
    finally:
        sys.stdout = old
    payload = json.loads(stdout.getvalue().strip())
    assert "security-scan-changes" in payload["predicted_skills"]
    assert "security.mdc" in payload["predicted_rules"]


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
