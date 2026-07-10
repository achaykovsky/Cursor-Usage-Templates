---
name: design-prompt-evals
description: Designs prompt eval suites — golden cases, property assertions, baselines, CI gates. Use when creating or extending LLM prompt regression tests, benchmark datasets, or eval coverage for system prompts.
---

# Design Prompt Evals

## Workflow

1. **Scope** — unit (prompt + fixed input), integration (retrieval/tools/policy), or adversarial. List target `prompt_id`(s).
2. **Coverage matrix** — categories × severity; minimum smoke counts: 2+ `happy_path`, 1+ `edge_case`, 1+ `refusal`, 1+ `adversarial` when customer-facing.
3. **Case authoring** — `input.messages` fixtures; assertions from [prompt-eval.schema.json](../../../ai-runtime/eval/prompt-eval.schema.json) allowlist.
4. **Grader order** — deterministic (`must_contain`, `regex`, `json_schema`) before LLM-judge. Justify each judge case in fixture `notes`.
5. **Baseline** — initial run; store pass rate and per-case results; set `pass_threshold` (e.g. 0.95 suite, 1.0 for `severity: critical` deterministic cases).
6. **CI policy** — PR smoke subset vs nightly full suite; document token/cost budget per run.
7. **Observability** — spans, metrics, and CI gates: [eval-metrics.md](../../../ai-runtime/observability/eval-metrics.md) (single catalog).

## Output Contract

- Suite path under `ai-runtime/eval/` (or `rag/eval/` for retrieval-only)
- Coverage matrix with category counts
- Pass thresholds and CI job sketch
- Version pins (`prompt_version`, `model`, `corpus_version` if RAG)
- Paired agents: `@agent(AI_OBSERVABILITY)` for metrics/runner; `@agent(AI_SAFETY)` for adversarial cases

## Notes

- RAG retrieval golden: [golden-questions.schema.json](../../../ai-runtime/rag/eval/golden-questions.schema.json) — compose with generation assertions when testing end-to-end.
- Adversarial cases: export from `add-prompt-injection-defenses` red-team list into `ai-runtime/eval/adversarial/`.
- Ongoing regression and drift: `monitor-ai-quality` after baseline exists.
- Runner implementation: `implement-prompt-eval-runner`.
- LLM-judge thresholds: `calibrate-llm-judge-eval`.
- Rule: [prompt-evals.mdc](../../../rules/prompt-evals.mdc).
