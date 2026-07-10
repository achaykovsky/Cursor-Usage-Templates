# LLM / Bot Span Conventions

Propagate W3C `traceparent` across gateway, LLM provider, and tool calls.

## Correlation IDs

| Field | Scope |
|-------|--------|
| `trace_id` | Full request trace |
| `conversation_id` | User thread across turns |
| `turn_id` | Single user message + bot response cycle |
| `bot_id` | Manifest `id` |

## Span names

| Span | Attributes (low cardinality) |
|------|------------------------------|
| `retrieval.query` | `corpus_id`, `top_k`, `hybrid`, `status` |
| `retrieval.rerank` | `model`, `input_count`, `output_count` |
| `embedding.batch` | `model`, `batch_size`, `status` |
| `llm.completion` | `model`, `provider`, `status`, `input_tokens`, `output_tokens` |
| `tool.call` | `tool_name`, `risk`, `policy_decision`, `status` |
| `policy.block` | `rule_id`, `mode` |
| `handoff.human` | `channel`, `outcome` |
| `rate_limit.block` | `reason` |
| `eval.run` | `suite_id`, `prompt_id`, `prompt_version`, `model`, `pass_rate`, `status` |
| `eval.case` | `case_id`, `category`, `grader_type`, `passed`, `suite_id` |

Span catalog and CI gates: [eval-metrics.md](eval-metrics.md).

## Redaction

Do not put user message bodies, emails, or secrets in span attributes. Use hashed `user_id` only.
