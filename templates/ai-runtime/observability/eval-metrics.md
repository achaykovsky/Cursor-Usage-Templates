# AI Bot Eval Metrics

Single catalog for eval **metrics**, **trace spans**, **CI gates**, and optional **LangSmith** wiring. Skills reference this file — do not duplicate span names or metric lists elsewhere.

## Skill responsibilities

| Skill | Owns |
|-------|------|
| `design-prompt-evals` | Suite design, coverage matrix, assertions, pass thresholds |
| `implement-prompt-eval-runner` | Offline grader, CI commands, baseline compare |
| `calibrate-llm-judge-eval` | Judge rubric, human labels, threshold recommendation |
| `design-ai-observability` | Trace/audit wiring for eval runs |
| `monitor-ai-quality` | Online drift, thumbs, escalation, alert thresholds |

Rule: [prompt-evals.mdc](../../rules/prompt-evals.mdc). Fixtures: [eval/README.md](../eval/README.md).

---

## Eval trace spans

Emit during offline CI runs and live eval jobs:

| Span | Required attributes | When |
|------|---------------------|------|
| `eval.run` | `suite_id`, `prompt_id`, `prompt_version`, `model`, `pass_rate`, `trace_id` | Suite start/end |
| `eval.case` | `case_id`, `category`, `grader_type`, `passed`, `suite_id` | Per case |
| `retrieval.query` | `corpus_id`, `top_k`, `trace_id` | RAG eval only |
| `llm.completion` | `model`, `channel`, `trace_id` | Inference step |
| `llm.judge` | `judge_model`, `score`, `case_id` | LLM-judge assertions only |

Follow [span-conventions.md](span-conventions.md) and `observability.mdc` for correlation IDs and redaction.

---

## Online (production)

| Metric | Type | Notes |
|--------|------|-------|
| `bot_requests_total` | counter | label: `channel`, `bot_id`, `status_class` |
| `bot_latency_seconds` | histogram | p50/p95/p99 per channel |
| `bot_escalation_total` | counter | human handoffs |
| `bot_thumbs_feedback` | counter | `positive` / `negative` |
| `bot_token_usage_total` | counter | aggregated tokens; no user labels |

---

## Offline (CI / regression)

### Prompt eval metrics

| Metric | Type | Notes |
|--------|------|-------|
| `eval_cases_total` | counter | label: `suite_id`, `category`, `grader_type` |
| `eval_pass_rate` | gauge | per suite run; compare to baseline |
| `eval_regression_delta` | gauge | current pass rate minus committed baseline |
| `eval_judge_score` | histogram | LLM-judge scores when used |
| `eval_judge_agreement_rate` | gauge | human vs judge agreement from calibration fixtures |
| `eval_run_duration_seconds` | histogram | end-to-end suite latency |

Fixtures: `templates/ai-runtime/eval/generation/*.json`, `adversarial/*.json` — schema [prompt-eval.schema.json](../eval/prompt-eval.schema.json).

### RAG retrieval metrics

| Metric | Use |
|--------|-----|
| Recall@k | Expected doc in top-k retrieved chunks |
| MRR | Mean reciprocal rank of first relevant chunk |
| nDCG | Ranked relevance when graded labels exist |
| Faithfulness | Answer grounded in retrieved chunks (LLM-judge or rule-based) |

Golden fixtures: `templates/ai-runtime/rag/eval/*.json` — validate with `validate_bot_runtime.py golden`.

---

## CI regression gates

| Gate | Command / hook | Fail when |
|------|----------------|-----------|
| Schema | `validate_bot_runtime.py prompt-eval\|eval-baseline\|judge-calibration` | Invalid fixture shape |
| Edit hook | `validate-prompt-eval-artifacts` | Same; skips `fixtures/` response maps |
| Grade | `prompt_eval_runner.py grade --baseline` | Below `pass_threshold` or baseline regression |
| Judge calibration | `llm_judge_calibration.py analyze --min-agreement 0.8` | Agreement below threshold |

**Policy:** PR = smoke subset + schema; nightly = full suite + baseline compare. Pin `prompt_version`, `model`, `temperature: 0` in CI.

---

## LLM-judge policy

- Deterministic graders (`must_contain`, `refusal`, `regex`, etc.) before LLM-judge.
- Pin `judge_model`; temperature 0.
- Calibrate `min_score` via `calibrate-llm-judge-eval` — never sole gate for safety-critical or adversarial cases.
- Max one retry per judge-based case in CI.

---

## LangSmith (optional stack)

Use only when the project already depends on LangChain/LangSmith. Neutral path: `implement-prompt-eval-runner` + `prompt_eval_runner.py`.

| Dataset source | Path |
|----------------|------|
| RAG retrieval golden | `ai-runtime/rag/eval/*.json` |
| Prompt generation smoke | `ai-runtime/eval/generation/*.json` |
| Adversarial / injection | `ai-runtime/eval/adversarial/*.json` |

**Traces:** `retrieval.query`, `llm.completion`, `eval.case` (attributes above).

**Regression:** run on corpus manifest, `prompt_version`, or policy changes.

**LLM-judge evaluators:** calibrate with `calibrate-llm-judge-eval` before gating CI on judge scores.

**RAG stack entry:** `implement-rag-with-langchain-stack` wraps ingest/retrieve only — eval catalog lives here.

---

## SLO examples

| SLO | Target |
|-----|--------|
| p95 latency | < 5s (excl. human handoff) |
| Error rate | < 1% |
| Escalation rate | product-defined baseline ± drift alert |

---

## Alerts

- Error rate breach
- Escalation spike
- Token spend vs budget
- Policy block rate anomaly
- `eval_regression_delta` below tolerance
- `eval_judge_agreement_rate` drop after judge model change
