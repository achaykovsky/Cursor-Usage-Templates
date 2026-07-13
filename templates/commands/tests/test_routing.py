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
    assert "git-github-workflow.mdc" in out


def test_rules_catalog_cover_routing() -> None:
    """Every templates/rules/*.mdc must appear in ALWAYS_APPLIED_RULES or FILE_SCOPED_RULES."""
    from pathlib import Path

    from routing._keywords import ALWAYS_APPLIED_RULES, FILE_SCOPED_RULES

    rules_dir = Path(__file__).resolve().parents[2] / "rules"
    always_applied: set[str] = set()
    file_scoped: set[str] = set()

    for path in sorted(rules_dir.glob("*.mdc")):
        text = path.read_text(encoding="utf-8")
        if "alwaysApply: true" in text:
            always_applied.add(path.name)
        elif "alwaysApply: false" in text:
            file_scoped.add(path.name)
        else:
            raise AssertionError(f"{path.name} missing alwaysApply frontmatter")

    routed_always = set(ALWAYS_APPLIED_RULES)
    routed_scoped = {entry.name for entry in FILE_SCOPED_RULES}

    assert always_applied == routed_always
    assert file_scoped == routed_scoped


def test_rules_for_paths_includes_clean_code_on_python() -> None:
    """Python paths must include clean-code.mdc via FILE_SCOPED_RULES."""
    scoped = rt.rules_for_paths(["src/service/handler.py"])
    assert "clean-code.mdc" in scoped["src/service/handler.py"]


def test_match_skills_discover_before_implement_prompt() -> None:
    """Implementation prompts must route to discover-before-implement before domain skills."""
    matched = rt.match_skills_from_prompt("implement new API endpoint for users")
    assert "discover-before-implement" in matched
    assert matched[0] == "discover-before-implement"


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


def test_match_skills_calibrate_judge_prompt() -> None:
    """LLM judge calibration prompts must route to calibrate-llm-judge-eval."""
    matched = rt.match_skills_from_prompt("calibrate llm judge threshold for faithfulness scorer rubric")
    assert "calibrate-llm-judge-eval" in matched


def test_match_skills_eval_regression_ci_routes_to_runner() -> None:
    """CI eval regression phrasing must route to implement-prompt-eval-runner."""
    matched = rt.match_skills_from_prompt("wire ci eval regression gate with pytest offline runner")
    assert "implement-prompt-eval-runner" in matched
    assert matched[0] == "implement-prompt-eval-runner"


def test_match_skills_prompt_eval_runner_prompt() -> None:
    """Eval runner implementation prompts must route to implement-prompt-eval-runner."""
    matched = rt.match_skills_from_prompt("implement eval runner for pytest prompt eval CI job")
    assert "implement-prompt-eval-runner" in matched


def test_match_skills_prompt_eval_prompt() -> None:
    """Prompt eval authoring must route to design-prompt-evals."""
    matched = rt.match_skills_from_prompt("create prompt eval suite with golden dataset for regression")
    assert "design-prompt-evals" in matched
    assert matched[0] == "design-prompt-evals"


def test_match_skills_llm_system_design_review_prompt() -> None:
    """LLM system design review prompts must rank review-llm-system-design first."""
    matched = rt.match_skills_from_prompt(
        "llm system design review hallucination risks and tenant isolation"
    )
    assert "review-llm-system-design" in matched
    assert matched[0] == "review-llm-system-design"


def test_route_agent_llm_system_reviewer() -> None:
    """Bot architecture review phrasing must route to AI_SYSTEM_REVIEWER."""
    out = rt.route_agent("review bot architecture tenant isolation")
    assert "AI_SYSTEM_REVIEWER" in out


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
