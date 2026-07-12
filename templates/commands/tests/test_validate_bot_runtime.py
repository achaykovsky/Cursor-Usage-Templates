"""Tests for templates/ai-runtime/validate_bot_runtime.py."""

from __future__ import annotations

if __name__ == "__main__":
    from _commands_bootstrap import run_test_file, runtime_ok

    if not runtime_ok():
        raise SystemExit(run_test_file(__file__))

import importlib.util
import sys
from pathlib import Path

import pytest

from _commands_bootstrap import ensure_paths, run_test_file

ensure_paths(policy=False)

AI_RUNTIME = Path(__file__).resolve().parents[2] / "ai-runtime"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


validate_mod = _load_module(
    "validate_bot_runtime", AI_RUNTIME / "validate_bot_runtime.py"
)


@pytest.fixture
def valid_manifest() -> dict:
    return {
        "schema_version": 1,
        "id": "test-bot",
        "channels": ["api"],
        "persona": {"tone": "neutral", "disclosure": "AI assistant"},
        "model": {"provider": "openai", "name": "gpt-test"},
        "tools": [{"name": "search_knowledge_base", "risk": "read"}],
        "escalation": {"enabled": True, "sla_minutes": 15},
    }


def test_validate_manifest_ok(valid_manifest: dict) -> None:
    assert validate_mod.validate_manifest(valid_manifest) == []


def test_validate_manifest_missing_id(valid_manifest: dict) -> None:
    del valid_manifest["id"]
    errors = validate_mod.validate_manifest(valid_manifest)
    assert any("missing required field 'id'" in e for e in errors)


def test_validate_example_support_bot() -> None:
    path = AI_RUNTIME / "bots" / "examples" / "support-bot.json"
    assert validate_mod.validate_manifest_file(path) == []


def test_validate_policy_default() -> None:
    path = AI_RUNTIME / "policy" / "default.bot.policy.json"
    assert validate_mod.validate_policy_file(path) == []


def test_validate_product_docs_corpus() -> None:
    path = AI_RUNTIME / "rag" / "examples" / "product-docs-corpus.json"
    assert validate_mod.validate_corpus_file(path) == []


def test_validate_product_docs_golden() -> None:
    path = AI_RUNTIME / "rag" / "eval" / "product-docs-golden.json"
    assert validate_mod.validate_golden_file(path) == []


def test_validate_corpus_missing_id() -> None:
    data = {
        "schema_version": 1,
        "sources": [{"source_id": "x", "type": "markdown"}],
        "chunking": {"strategy": "fixed", "max_tokens": 256},
        "embedding": {"provider": "openai", "model": "e", "dimensions": 1536},
        "retrieval": {"top_k": 5, "min_score": 0.5},
    }
    errors = validate_mod.validate_corpus(data)
    assert any("missing required field 'id'" in e for e in errors)


def test_validate_golden_empty_questions() -> None:
    data = {"schema_version": 1, "corpus_id": "product-docs", "questions": []}
    errors = validate_mod.validate_golden(data)
    assert any("questions must be non-empty" in e for e in errors)


def test_validate_support_bot_smoke_prompt_eval() -> None:
    path = AI_RUNTIME / "eval" / "generation" / "support-bot-smoke.json"
    assert validate_mod.validate_prompt_eval_file(path) == []


def test_validate_support_bot_smoke_baseline() -> None:
    path = AI_RUNTIME / "eval" / "baselines" / "support-bot-smoke-baseline.json"
    assert validate_mod.validate_eval_baseline_file(path) == []


def test_validate_injection_smoke_prompt_eval() -> None:
    path = AI_RUNTIME / "eval" / "adversarial" / "injection-smoke.json"
    assert validate_mod.validate_prompt_eval_file(path) == []


def test_validate_judge_calibration_fixture() -> None:
    path = AI_RUNTIME / "eval" / "calibration" / "support-helpfulness-v1.json"
    assert validate_mod.validate_judge_calibration_file(path) == []


def test_judge_calibration_validator_is_cached() -> None:
    validate_mod._judge_calibration_validator.cache_clear()
    validate_mod._judge_calibration_validator()
    validate_mod._judge_calibration_validator()
    info = validate_mod._judge_calibration_validator.cache_info()
    assert info.hits == 1
    assert info.misses == 1


def test_validate_prompt_eval_missing_cases() -> None:
    data = {
        "schema_version": 1,
        "suite_id": "test-suite",
        "prompt_id": "p1",
        "cases": [],
    }
    errors = validate_mod.validate_prompt_eval(data)
    assert any("cases must be non-empty" in e for e in errors)


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
