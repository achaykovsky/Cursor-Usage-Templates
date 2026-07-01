# AI Bot Eval Metrics

## Online (production)

| Metric | Type | Notes |
|--------|------|-------|
| `bot_requests_total` | counter | label: `channel`, `bot_id`, `status_class` |
| `bot_latency_seconds` | histogram | p50/p95/p99 per channel |
| `bot_escalation_total` | counter | human handoffs |
| `bot_thumbs_feedback` | counter | `positive` / `negative` |
| `bot_token_usage_total` | counter | aggregated tokens; no user labels |

## Offline (CI / regression)

- Golden questions with expected properties (contains, not-contains, max_length).
- Run on manifest or policy changes via `monitor-ai-quality` skill.

### RAG retrieval metrics

| Metric | Use |
|--------|-----|
| Recall@k | Expected doc in top-k retrieved chunks |
| MRR | Mean reciprocal rank of first relevant chunk |
| nDCG | Ranked relevance when graded labels exist |
| Faithfulness | Answer grounded in retrieved chunks (LLM-judge or rule-based) |

Golden fixtures: `templates/ai-runtime/rag/eval/*.json` — validate with `validate_bot_runtime.py golden`.

## SLO examples

| SLO | Target |
|-----|--------|
| p95 latency | < 5s (excl. human handoff) |
| Error rate | < 1% |
| Escalation rate | product-defined baseline ± drift alert |

## Alerts

- Error rate breach
- Escalation spike
- Token spend vs budget
- Policy block rate anomaly
