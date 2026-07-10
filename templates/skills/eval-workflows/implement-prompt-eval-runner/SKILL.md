---
name: implement-prompt-eval-runner
description: Implements prompt eval runners and CI gates — deterministic graders, baseline comparison, pytest integration. Use when wiring offline prompt regression tests or CI jobs for eval suites.
---

# Implement Prompt Eval Runner

## Workflow

1. **Validate fixtures** — `python templates/ai-runtime/validate_bot_runtime.py prompt-eval <suite.json>` (hook: `validate-prompt-eval-artifacts`).
2. **Grader module** — use [prompt_eval_runner.py](../../../ai-runtime/eval/prompt_eval_runner.py) for deterministic assertions (`must_contain`, `refusal`, `regex`, etc.).
3. **Responses map** — JSON object `{ "case_id": "model output text" }` for offline/CI runs; live gateway jobs populate this after inference.
4. **Grade** — `python templates/ai-runtime/eval/prompt_eval_runner.py grade --suite <suite.json> --responses <responses.json> --json`.
5. **Baseline** — commit `eval/baselines/<suite>-baseline.json`; compare with `--baseline` and `--regression-tolerance` (default 0).
6. **CI** — PR smoke + nightly full suite per [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md) CI gates.
7. **LLM-judge** — live judge integration only; offline runner skips `llm_judge`. Thresholds: `calibrate-llm-judge-eval`.

## Output Contract

- Runner command(s) and pytest module path
- CI job snippet (validate + grade + baseline)
- Baseline file location and pass/regression thresholds
- Report format (JSON stdout from `--json`)

## Notes

- Design suites first: `design-prompt-evals`.
- Schema: [prompt-eval.schema.json](../../../ai-runtime/eval/prompt-eval.schema.json), [eval-baseline.schema.json](../../../ai-runtime/eval/eval-baseline.schema.json).
- Pair with `@agent(BACKEND_PYTHON)` or `@agent(AI_OBSERVABILITY)` for CI wiring.
- Metrics and spans: [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md).
