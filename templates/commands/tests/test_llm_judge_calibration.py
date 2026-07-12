"""Tests for templates/ai-runtime/eval/llm_judge_calibration.py."""

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


cal_mod = _load_module("llm_judge_calibration", EVAL_DIR / "llm_judge_calibration.py")


def test_recommend_threshold_on_fixture() -> None:
    path = EVAL_DIR / "calibration" / "support-helpfulness-v1.json"
    data = cal_mod._load_json(path)
    threshold = cal_mod.recommend_threshold(data)
    assert 0.0 <= threshold <= 1.0


def test_analyze_calibration_agreement() -> None:
    path = EVAL_DIR / "calibration" / "support-helpfulness-v1.json"
    data = cal_mod._load_json(path)
    metrics = cal_mod.analyze_calibration(data, threshold=0.8)
    assert metrics.labeled_count >= 3
    assert metrics.agreement_rate >= 0.8


def test_validate_calibration_fixture() -> None:
    path = EVAL_DIR / "calibration" / "support-helpfulness-v1.json"
    data = cal_mod._load_json(path)
    assert cal_mod.validate_judge_calibration(data, path=str(path)) == []


if __name__ == "__main__":
    raise SystemExit(run_test_file(__file__))
