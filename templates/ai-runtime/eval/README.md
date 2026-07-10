# Prompt Eval Fixtures

Offline regression suites for **prompt-level** quality, safety, and integration checks. Distinct from RAG retrieval golden sets in [rag/eval/](../rag/eval/) — compose both when testing end-to-end bots.

## Layout

| Path | Purpose |
|------|---------|
| [prompt-eval.schema.json](prompt-eval.schema.json) | Suite + case + assertion schema |
| [eval-baseline.schema.json](eval-baseline.schema.json) | Baseline pass-rate snapshot schema |
| [llm-judge-calibration.schema.json](llm-judge-calibration.schema.json) | Human-labeled judge calibration schema |
| [prompt_eval_runner.py](prompt_eval_runner.py) | Deterministic offline grader + CLI |
| [llm_judge_calibration.py](llm_judge_calibration.py) | Judge agreement metrics + threshold analysis |
| [generation/](generation/) | Non-RAG prompt evals (system/user message → output properties) |
| [adversarial/](adversarial/) | Injection, jailbreak, policy refusal cases |
| [baselines/](baselines/) | Committed pass-rate baselines for regression gates |
| [calibration/](calibration/) | LLM-judge human-labeled calibration sets |
| [fixtures/](fixtures/) | Canned model responses for offline CI |
| [examples/](examples/) | Reference fixtures (not CI gates) |

## Quick start

1. Copy [generation/support-bot-smoke.json](generation/support-bot-smoke.json) as a template.
2. Follow skill `design-prompt-evals` for coverage matrix and pass thresholds.
3. Export red-team cases to [adversarial/](adversarial/) via `add-prompt-injection-defenses`.
4. Wire CI with skill `implement-prompt-eval-runner`.
5. Calibrate LLM judge thresholds with `calibrate-llm-judge-eval` when using `llm_judge` assertions.
6. Rule [prompt-evals.mdc](../../rules/prompt-evals.mdc) applies when editing fixtures.

## Validate

```bash
python templates/ai-runtime/validate_bot_runtime.py prompt-eval <suite.json>
python templates/ai-runtime/validate_bot_runtime.py eval-baseline <baseline.json>
python templates/ai-runtime/validate_bot_runtime.py judge-calibration <calibration.json>
```

Hook `validate-prompt-eval-artifacts` runs on edits under `ai-runtime/eval/` (excludes `*.schema.json` and `fixtures/` response maps).

## Grade offline (CI)

```bash
# Generation smoke
python templates/ai-runtime/eval/prompt_eval_runner.py grade \
  --suite templates/ai-runtime/eval/generation/support-bot-smoke.json \
  --responses templates/ai-runtime/eval/fixtures/support-bot-smoke-responses.json \
  --baseline templates/ai-runtime/eval/baselines/support-bot-smoke-baseline.json \
  --json

# Adversarial smoke
python templates/ai-runtime/eval/prompt_eval_runner.py grade \
  --suite templates/ai-runtime/eval/adversarial/injection-smoke.json \
  --responses templates/ai-runtime/eval/fixtures/injection-smoke-responses.json \
  --baseline templates/ai-runtime/eval/baselines/injection-smoke-baseline.json \
  --json
```

## Calibrate LLM judge

```bash
python templates/ai-runtime/eval/llm_judge_calibration.py analyze \
  templates/ai-runtime/eval/calibration/support-helpfulness-v1.json \
  --json
```

## Metrics

Canonical catalog: [observability/eval-metrics.md](../observability/eval-metrics.md) (metrics, spans, CI gates, LangSmith).

## Related

| Artifact | Use |
|----------|-----|
| [rag/eval/golden-questions.schema.json](../rag/eval/golden-questions.schema.json) | Retrieval recall@k, cite-or-abstain |
| [observability/eval-metrics.md](../observability/eval-metrics.md) | Online + offline metric catalog |
| Skill `monitor-ai-quality` | Drift, thumbs, escalation after baseline |
| Skill `add-prompt-injection-defenses` | Export red-team cases to `adversarial/` |
| Skill `calibrate-llm-judge-eval` | Judge rubric and threshold tuning |
