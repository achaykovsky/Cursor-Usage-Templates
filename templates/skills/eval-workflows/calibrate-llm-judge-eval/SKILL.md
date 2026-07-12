---
name: calibrate-llm-judge-eval
description: Calibrates LLM-as-judge evaluators — rubric design, human-labeled samples, agreement rate, threshold tuning. Use when faithfulness or quality scoring relies on an LLM judge and you need a defensible pass threshold.
---

# Calibrate LLM Judge Eval

## Workflow

1. **Rubric** — single paragraph, observable criteria (helpful, grounded, on-brand, no leakage). Avoid vague "good quality".
2. **Sample set** — 10+ labeled responses: pass/fail from human review; include borderline and failure modes.
3. **Judge runs** — record `judge_score` (0–1) per sample with pinned `judge_model` and temperature 0.
4. **Fixture** — [llm-judge-calibration.schema.json](../../../ai-runtime/eval/llm-judge-calibration.schema.json) under `ai-runtime/eval/calibration/`.
5. **Analyze** — `python templates/ai-runtime/eval/llm_judge_calibration.py analyze <fixture.json> --json`.
6. **Threshold** — use `recommended_threshold` in suite `llm_judge` assertions (`min_score`); never sole gate for safety-critical cases.
7. **Re-calibrate** — when rubric, judge model, or product tone changes.

## Output Contract

- Calibration fixture path
- Agreement rate, precision, recall at chosen threshold
- Recommended `min_score` for eval suites
- Known failure modes (false positives / false negatives)

## Notes

- Pair with `design-prompt-evals` for suite integration and `@agent(AI_OBSERVABILITY)` for CI.
- Safety/adversarial cases stay deterministic — judge policy in [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md).
- LangSmith (optional): [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md) LangSmith section.
