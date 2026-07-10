"""Tests for templates/ai-runtime/eval/prompt_eval_runner.py."""

from __future__ import annotations

if __name__ == "__main__":
    from _commands_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import importlib.util
import sys
from pathlib import Path

from _commands_bootstrap import ensure_paths, run_test_file

ensure_paths(policy=False)

EVAL_DIR = Path(__file__).resolve().parents[2] / "ai-runtime" / "eval"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


runner_mod = _load_module("prompt_eval_runner", EVAL_DIR / "prompt_eval_runner.py")


def test_must_contain_passes() -> None:
    result = runner_mod.grade_assertion(
        {"type": "must_contain", "values": ["refund"]},
        "You can request a refund from billing.",
    )
    assert result.passed is True


def test_must_not_contain_fails() -> None:
    result = runner_mod.grade_assertion(
        {"type": "must_not_contain", "values": ["api_key"]},
        "Here is your api_key: leaked",
    )
    assert result.passed is False


def test_refusal_expected_true() -> None:
    result = runner_mod.grade_assertion(
        {"type": "refusal", "expected": True},
        "I can't help with bypassing payment systems.",
    )
    assert result.passed is True


def test_grade_suite_support_bot_smoke() -> None:
    suite_path = EVAL_DIR / "generation" / "support-bot-smoke.json"
    responses_path = EVAL_DIR / "fixtures" / "support-bot-smoke-responses.json"
    suite = runner_mod._load_json(suite_path)
    responses = runner_mod._load_json(responses_path)

    suite_result = runner_mod.grade_suite(suite, responses)
    assert suite_result.pass_rate == 1.0
    assert runner_mod.suite_meets_threshold(suite, suite_result) is True


def test_compare_to_baseline_detects_regression() -> None:
    suite_path = EVAL_DIR / "generation" / "support-bot-smoke.json"
    baseline_path = EVAL_DIR / "baselines" / "support-bot-smoke-baseline.json"
    suite = runner_mod._load_json(suite_path)
    baseline = runner_mod._load_json(baseline_path)

    bad_responses = {
        "refund-happy": "no helpful answer",
        "password-edge": runner_mod._load_json(EVAL_DIR / "fixtures" / "support-bot-smoke-responses.json")[
            "password-edge"
        ],
        "harmful-refusal": runner_mod._load_json(EVAL_DIR / "fixtures" / "support-bot-smoke-responses.json")[
            "harmful-refusal"
        ],
    }
    suite_result = runner_mod.grade_suite(suite, bad_responses)
    errors = runner_mod.compare_to_baseline(suite_result, baseline)
    assert any("refund-happy" in err for err in errors)


def test_grade_suite_injection_smoke() -> None:
    suite_path = EVAL_DIR / "adversarial" / "injection-smoke.json"
    responses_path = EVAL_DIR / "fixtures" / "injection-smoke-responses.json"
    suite = runner_mod._load_json(suite_path)
    responses = runner_mod._load_json(responses_path)

    suite_result = runner_mod.grade_suite(suite, responses)
    assert suite_result.pass_rate == 1.0


def test_tool_call_passes_when_any_matching_call_has_required_args() -> None:
    """tool_call must pass if at least one matching invocation satisfies args_schema."""
    assertion = {
        "type": "tool_call",
        "name": "lookup_order",
        "args_schema": {"type": "object", "required": ["order_id"]},
    }
    tool_calls = [
        {"name": "lookup_order", "args": {}},
        {"name": "lookup_order", "args": {"order_id": "ORD-1001"}},
    ]
    result = runner_mod.grade_assertion(assertion, "", tool_calls=tool_calls)
    assert result.passed is True


def test_tool_call_fails_when_no_matching_call_has_required_args() -> None:
    assertion = {
        "type": "tool_call",
        "name": "lookup_order",
        "args_schema": {"type": "object", "required": ["order_id"]},
    }
    tool_calls = [
        {"name": "lookup_order", "args": {}},
        {"name": "lookup_order", "args": {"customer_id": "c1"}},
    ]
    result = runner_mod.grade_assertion(assertion, "", tool_calls=tool_calls)
    assert result.passed is False


def test_llm_judge_skipped_offline() -> None:
    result = runner_mod.grade_assertion(
        {"type": "llm_judge", "rubric": "helpful", "min_score": 0.8},
        "any response",
    )
    assert result.skipped is True


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
