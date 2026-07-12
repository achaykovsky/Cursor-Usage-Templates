# LLM system design review checklist

Canonical 12-dimension checklist for `review-llm-system-design` and `@agent(AI_SYSTEM_REVIEWER)`.

**Scope:** Design docs, ADRs, `ai-runtime/` artifacts, bot manifests, policy JSON, RAG corpus/golden fixtures, and gateway/RAG implementation code.

**Severity in reports:** CRITICAL (block launch), WARNING (address before scale), GOOD (optional improvement).

---

## 1. Hallucination risks

### Review questions

- Is every factual claim grounded in retrieved context, tool results, or explicit user-provided data?
- Does the system cite sources or abstain when evidence is insufficient (`min_score`, cite-or-abstain)?
- Are faithfulness metrics defined (offline golden set, LLM-judge or human rubric)?
- Is post-generation validation planned (structured output schema, chunk overlap check)?

### Pass criteria

- Cite-or-abstain policy documented and enforced in retrieval + prompt
- Golden eval includes faithfulness / groundedness cases
- Output policy forbids inventing product facts, policies, or IDs

### Common failure modes

- Prompt instructs "be helpful" without grounding rules
- RAG returns chunks but model answers beyond them
- No abstain path — model guesses when retrieval is empty

### Artifacts

- [guardrails/output-policy.md](../guardrails/output-policy.md)
- [rag/README.md](../rag/README.md) (golden eval)
- [observability/eval-metrics.md](../observability/eval-metrics.md)
- Rule: [rag-pipeline.mdc](../../rules/rag-pipeline.mdc)

### Remediation skills

`implement-retrieval-pipeline`, `design-prompt-evals`, `calibrate-llm-judge-eval`, `monitor-ai-quality`, `add-prompt-injection-defenses`

---

## 2. Context explosion

### Review questions

- What is the per-request token budget (system + history + retrieval + tools)?
- How is conversation history trimmed (sliding window, summarization, session cap)?
- How many RAG chunks and what max tokens per chunk enter the prompt?
- Are multi-agent handoffs passing minimal context, not full transcripts?

### Pass criteria

- Documented token budget per turn with hard caps before LLM call
- Retrieval pipeline enforces max chunks / max context tokens
- History strategy defined (not unbounded message list)

### Common failure modes

- Full chat history + large RAG dump on every turn
- Specialist bots receive parent transcript wholesale
- Tool results appended without truncation policy

### Artifacts

- Bot manifest `context` / `limits` fields ([bots/manifest.schema.json](../bots/manifest.schema.json))
- Skill cross-ref: `design-multi-agent-routing` (minimal handoff)

### Remediation skills

`design-multi-agent-routing`, `implement-retrieval-pipeline`

---

## 3. Retrieval quality

### Review questions

- Is corpus versioning and embedding model lock documented?
- Hybrid retrieval (dense + keyword) and rerank in place where needed?
- Are chunk size, overlap, and metadata (tenant, doc_type) appropriate?
- Golden set covers recall@k, MRR, and failure cases (typos, paraphrase)?

### Pass criteria

- Corpus manifest with version, embedding model id, index namespace
- `min_score` threshold and rerank step defined
- Offline eval fixtures exist and run in CI

### Common failure modes

- Single-vector search with no metadata filters
- Stale index after corpus update without re-embed
- Golden set only happy-path questions

### Artifacts

- [rag/README.md](../rag/README.md)
- [observability/eval-metrics.md](../observability/eval-metrics.md)
- Rule: [rag-pipeline.mdc](../../rules/rag-pipeline.mdc)

### Remediation skills

`design-rag-architecture`, `implement-rag-ingest-and-index`, `implement-retrieval-pipeline`, `monitor-ai-quality`

---

## 4. Prompt coupling

### Review questions

- Are system prompts and persona stored in versioned manifests, not hardcoded in gateway code?
- Can prompts change without redeploying application logic?
- Are prompt versions tied to eval baselines and rollback?
- Is user content clearly delimited from system instructions?

### Pass criteria

- Manifest-driven prompts (`bots/examples/`, schema fields)
- Separation: policy JSON / manifest vs gateway orchestration code
- Injection defenses assume fixed system boundary

### Common failure modes

- Prompt strings embedded in Python/Go handlers
- A/B prompt tests without version ids
- Business rules duplicated in prompt and code inconsistently

### Artifacts

- [bots/README.md](../bots/README.md)
- [guardrails/input-sanitization.md](../guardrails/input-sanitization.md)
- Rule: [ai-safety.mdc](../../rules/ai-safety.mdc)

### Remediation skills

`design-customer-facing-agent`, `add-prompt-injection-defenses`

---

## 5. Observability

### Review questions

- Are W3C `traceparent` and spans defined for `llm.completion`, `tool.call`, `retrieval`, `handoff.human`?
- Is compliance audit separate from debug logs?
- RED metrics with low-cardinality labels (channel, status class — not user_id)?
- Token/cost counters without logging full prompts in production?

### Pass criteria

- Span conventions documented ([observability/span-conventions.md](../observability/span-conventions.md))
- Audit schema validated ([conversation-audit.schema.json](../observability/conversation-audit.schema.json))
- SLO targets for latency and error rate

### Common failure modes

- Only application logs, no distributed traces
- PII in log fields or metric labels
- Debug and audit streams mixed

### Artifacts

- [observability/README.md](../observability/README.md)
- Rule: [observability.mdc](../../rules/observability.mdc), [llm-gateway.mdc](../../rules/llm-gateway.mdc)

### Remediation skills

`design-ai-observability`

---

## 6. Evaluation

### Review questions

- Offline golden set with pass/fail thresholds in CI?
- Online signals: thumbs, escalation rate, abstain rate?
- Eval covers safety, faithfulness, and task success — not only BLEU/ROUGE?
- Regression gate before prompt or model changes?

### Pass criteria

- Golden JSON validated (`validate_bot_runtime.py golden` for RAG; `prompt-eval` for generation/adversarial suites)
- Prompt eval baselines committed; CI regression via `implement-prompt-eval-runner`
- LLM-judge thresholds calibrated (`calibrate-llm-judge-eval`) when used
- Eval pipeline referenced in observability design
- Drift alerts on refusal/escalation spikes

### Common failure modes

- Manual spot-check only before launch
- No eval after retrieval, prompt, or model swap
- Metrics measure latency but not answer quality
- Adversarial cases missing from CI

### Artifacts

- [observability/eval-metrics.md](../observability/eval-metrics.md)
- [eval/README.md](../eval/README.md) (prompt suites, adversarial, calibration)
- [rag/eval/](../rag/) golden fixtures

### Remediation skills

`design-prompt-evals`, `implement-prompt-eval-runner`, `calibrate-llm-judge-eval`, `monitor-ai-quality`, `design-ai-observability`, `add-prompt-injection-defenses`

---

## 7. Confidence calculation

### Review questions

- How is intent or retrieval confidence scored (numeric threshold, not vibes)?
- What happens below threshold: abstain, clarify, route to specialist, or handoff?
- Are thresholds calibrated against golden set (precision/recall tradeoff)?
- Is confidence logged for post-hoc analysis?

### Pass criteria

- Documented confidence sources (retrieval score, classifier, logprobs if used)
- Explicit threshold → action mapping
- Low-confidence path tested in golden eval

### Common failure modes

- "Fallback when confidence low" with no score or threshold
- Router always picks a specialist even on ambiguous input
- No telemetry on confidence distribution

### Artifacts

- [guardrails/human-handoff.md](../guardrails/human-handoff.md)
- Skill cross-ref: `design-multi-agent-routing`

### Remediation skills

`design-multi-agent-routing`, `implement-human-handoff`

---

## 8. Deterministic business logic

### Review questions

- Which decisions are **code** (pricing, eligibility, auth, quotas) vs **LLM** (language, summarization)?
- Are structured outputs (JSON schema, Pydantic) used where downstream systems need reliability?
- Can the LLM override business rules? (It should not.)
- Are idempotent side effects enforced outside the model?

### Pass criteria

- Written boundary: deterministic layer owns money, permissions, and state changes
- LLM output parsed and validated before acting on tools
- Workflow/state machine for multi-step business processes where order matters

### Common failure modes

- "Calculate refund in the prompt"
- Tool calls triggered from unparsed free text
- Same rule stated in prompt and code with drift

### Artifacts

- [policy/tool-risk-catalog.json](../policy/tool-risk-catalog.json)
- Rule: [ai-safety.mdc](../../rules/ai-safety.mdc) (tool allowlist)

### Remediation skills

`implement-bot-gateway`, `evaluate-ai-safety-policy`; escalate `ARCHITECT` for workflow design

---

## 9. Tenant isolation

### Review questions

- Are sessions, corpora, and policies scoped by tenant/org id at every layer?
- Do retrieval queries always include tenant metadata filters?
- Can one tenant's data appear in another's context or audit export?
- Per-tenant rate limits and cost caps?

### Pass criteria

- Tenant id in session store, index metadata, and audit actor fields
- Integration tests or eval cases for cross-tenant leakage
- No shared cache keys without tenant namespace

### Common failure modes

- Global vector index without tenant filter
- `user_id` only, no org boundary
- Shared prompt cache across tenants

### Artifacts

- Rule: [rag-pipeline.mdc](../../rules/rag-pipeline.mdc) (metadata filters)
- [policy/default.bot.policy.json](../policy/default.bot.policy.json)

### Remediation skills

`design-rag-architecture`, `implement-bot-gateway`, `implement-ai-rate-limiting`

---

## 10. Future tool calling

### Review questions

- Is there a tool registry (name, schema, risk tier, owner) separate from ad-hoc functions?
- How are new tools added without gateway redeploy (config-driven allowlist)?
- Schema evolution and backward compatibility for tool args?
- MCP or external tools mapped to same risk tiers as first-party tools?

### Pass criteria

- [tool-risk-catalog.json](../policy/tool-risk-catalog.json) entries for each tool
- Write/destructive tools default `ask` or `deny`
- Versioned tool schemas; gateway validates args before execution

### Common failure modes

- Tools registered only in code
- Silent auto-execution of write tools
- No plan for adding tools post-launch

### Artifacts

- [policy/README.md](../policy/README.md)
- Rule: [ai-safety.mdc](../../rules/ai-safety.mdc), [ai-customer-facing.mdc](../../rules/ai-customer-facing.mdc)

### Remediation skills

`implement-bot-gateway`, `evaluate-ai-safety-policy`

---

## 11. Cost implications

### Review questions

- Cost model: router + specialist + rerank + embed per turn?
- Per-user, per-org, and global token budgets?
- Caching (embeddings, frequent queries) to reduce repeat spend?
- Alerts before budget exhaustion?

### Pass criteria

- Rate limits and cost caps in gateway ([implement-ai-rate-limiting](../../skills/ai-infra-workflows/implement-ai-rate-limiting/SKILL.md))
- Token counters in metrics (low-cardinality)
- Per-turn LLM call cap in multi-agent designs

### Common failure modes

- Unbounded agent loops or tool retry storms
- Large model for trivial classification
- No visibility into spend per channel/tenant

### Artifacts

- [observability/eval-metrics.md](../observability/eval-metrics.md)
- Skill cross-ref: `implement-ai-rate-limiting`, `design-multi-agent-routing`

### Remediation skills

`implement-ai-rate-limiting`, `design-ai-observability`, `design-multi-agent-routing`

---

## 12. Latency implications

### Review questions

- End-to-end p95 SLO defined (excl. human handoff)?
- Timeouts on LLM, retrieval, and each tool call; total request budget?
- Streaming to client where UX requires it?
- Parallel tool calls vs sequential chains?

### Pass criteria

- Timeouts in gateway per [llm-gateway.mdc](../../rules/llm-gateway.mdc)
- p95 target in eval-metrics (e.g. &lt; 5s)
- Circuit breaker or degrade path on provider failure

### Common failure modes

- Sequential LLM + rerank + LLM with no budget
- Blocking on slow tools without timeout
- No cancellation on client disconnect

### Artifacts

- [observability/eval-metrics.md](../observability/eval-metrics.md)
- [observability/span-conventions.md](../observability/span-conventions.md)
- Rule: [llm-gateway.mdc](../../rules/llm-gateway.mdc)

### Remediation skills

`implement-bot-gateway`, `design-ai-observability`
