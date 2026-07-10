# Cursor Prompt: Plan LLM System Design Review

**Usage:** Paste into Chat/Composer with your **system name** and scope. For retrospective review of existing bots/RAG — not greenfield build or code/PR review.

**Reference:** [design-review/README.md](../ai-runtime/design-review/README.md) | [USAGE.md](../USAGE.md) | skill `review-llm-system-design` | agent `@agent(AI_SYSTEM_REVIEWER)`

---

## Inputs (user provides)

```
System: <e.g. billing support bot + knowledge base>
Scope: <design | implementation | both>  (default: both)
Paths: <optional — @folders or files to review>
Constraints: <optional — multi-tenant, HIPAA, budget cap, p95 latency>
Time-box: <optional — prioritize dimensions if limited>
```

---

## Instructions for Cursor

Produce **only** the following (no full skill bodies, no implementation):

### 1. Route table (max 6 rows)

| Step | Layer | Choice | Why (one line) |
|------|-------|--------|----------------|
| 1 | skill | review-llm-system-design | … |
| 2 | agent | AI_SYSTEM_REVIEWER | … |

Canonical review sequence:

`review-llm-system-design` + `@agent(AI_SYSTEM_REVIEWER)` → read [system-review-checklist.md](../ai-runtime/design-review/system-review-checklist.md) → structured 12-dimension report → remediation skills per finding

### 2. Context to attach

List files/folders the reviewer should `@` reference:

- `ai-runtime/` manifests, policy, guardrails, observability, RAG fixtures, prompt eval suites (`eval/`)
- Gateway/retrieval code paths if implementation scope
- ADRs/specs if design scope

### 3. Dimension priority (if time-boxed)

Default order when cutting scope: hallucination → tenant isolation → deterministic business logic → retrieval quality → observability/eval → remaining dimensions.

### 4. Rules note

Cross-check: `llm-gateway`, `rag-pipeline`, `prompt-evals`, `ai-safety`, `ai-customer-facing`, `security` (OWASP LLM).

### 5. Escalation agents (implementation only — not for review turn)

| Finding area | Delegate to |
|--------------|-------------|
| Safety / injection / policy | `@agent(AI_SAFETY)` |
| RAG ingest/retrieve | `@agent(RAG_ENGINEER)` |
| Gateway / rate limits | `@agent(AI_PLATFORM)` |
| Traces / evals / SLOs | `@agent(AI_OBSERVABILITY)`; skills `design-prompt-evals`, `implement-prompt-eval-runner`, `monitor-ai-quality` |

### 6. Do not use

- `review-pull-request` — code/PR diff review, not system design
- `orchestrate-ai-bot-delivery` — greenfield build routing
- `ARCHITECT` alone — generic topology; use `AI_SYSTEM_REVIEWER` for LLM-specific checklist

---

## Constraints

- Review produces findings and remediation routes — not code changes unless user asks in a follow-up turn.
- No secrets in pasted manifests; redact per `redact-sensitive-in-output`.
- Customer personas are runtime manifests, not `@agent()` entries.

---

## Optional: parallel tracks

When scope includes both bot gateway and RAG:

- Run single 12-dimension review covering both; remediation may chain `implement-retrieval-pipeline` and `implement-bot-gateway`.
- Do not split into two separate review skills — one report, combined remediation map.
