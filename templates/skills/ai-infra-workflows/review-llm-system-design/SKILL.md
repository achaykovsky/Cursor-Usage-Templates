---
name: review-llm-system-design
description: Performs LLM system design review (not code review) across hallucination risks, context explosion, retrieval quality, prompt coupling, observability, evaluation, confidence calculation, deterministic business logic, tenant isolation, future tool calling, cost, and latency. Use for bot/RAG architecture review, pre-launch design audit, or reviewing specs plus ai-runtime implementation.
---

# Review LLM System Design

## Routing: system review vs code review

- **This skill** — LLM platform architecture: grounding, context, retrieval, observability, tenant isolation, cost/latency, tool registry.
- **Code/PR review** — route to `review-pull-request` + `@agent(REVIEWER)`.
- **Safety-only pre-launch** — `evaluate-ai-safety-policy` (subset; may run in parallel).
- **Greenfield build** — `orchestrate-ai-bot-delivery`.

Pair with `@agent(AI_SYSTEM_REVIEWER)` for review tone and 12-dimension structure.

## Workflow

1. **Scope**
   - Confirm: design docs only, implementation only, or **both** (default both).
   - Note constraints (HIPAA, budget cap, multi-tenant, channels).

2. **Gather context**
   - Design: ADRs, specs, architecture diagrams, bot conversation specs.
   - Implementation: `ai-runtime/**` (manifests, policy, guardrails, observability, RAG fixtures), gateway and retrieval code if present.
   - Use `@path` references — do not invent missing artifacts; list gaps as findings.

3. **Apply checklist**
   - Evaluate all **12 dimensions** (see Remediation map below for dimension names and follow-up skills).
   - Cite evidence per dimension.

4. **Cross-check rules**
   - `llm-gateway.mdc`, `rag-pipeline.mdc`, `ai-safety.mdc`, `ai-customer-facing.mdc`, `security.mdc` (OWASP LLM section).

5. **Structured report**
   - Per dimension: status (Pass / Partial / Fail), findings by CRITICAL / WARNING / GOOD, evidence pointers.

6. **Remediation map**
   - Link each CRITICAL/WARNING to an existing skill (see table below).
   - Do not implement fixes in the review turn unless the user asks.

## Remediation map

| Dimension | Primary remediation skills |
|-----------|---------------------------|
| Hallucination risks | `implement-retrieval-pipeline`, `design-prompt-evals`, `calibrate-llm-judge-eval`, `monitor-ai-quality`, `add-prompt-injection-defenses` |
| Context explosion | `design-multi-agent-routing`, `implement-retrieval-pipeline` |
| Retrieval quality | `design-rag-architecture`, `implement-rag-ingest-and-index`, `implement-retrieval-pipeline`, `monitor-ai-quality` |
| Prompt coupling | `design-customer-facing-agent`, `add-prompt-injection-defenses` |
| Observability | `design-ai-observability` |
| Evaluation | `design-prompt-evals`, `implement-prompt-eval-runner`, `calibrate-llm-judge-eval`, `monitor-ai-quality`, `design-ai-observability`, `add-prompt-injection-defenses` |
| Confidence calculation | `design-multi-agent-routing`, `implement-human-handoff` |
| Deterministic business logic | `implement-bot-gateway`, `evaluate-ai-safety-policy`; escalate `@agent(ARCHITECT)` |
| Tenant isolation | `design-rag-architecture`, `implement-bot-gateway`, `implement-ai-rate-limiting` |
| Future tool calling | `implement-bot-gateway`, `evaluate-ai-safety-policy` |
| Cost implications | `implement-ai-rate-limiting`, `design-ai-observability`, `design-multi-agent-routing` |
| Latency implications | `implement-bot-gateway`, `design-ai-observability` |

## Output Contract

- Executive summary (1–2 sentences) and top 1–3 blockers
- Twelve sections (one per checklist dimension): status, severity-grouped findings, evidence citations
- Ordered follow-up skill chain for fixes
- Optional: recommend `write-or-update-adr` when architectural decisions need recording

## Notes

- Pair with `@agent(AI_SYSTEM_REVIEWER)`; spawn `@agent(RAG_ENGINEER)`, `@agent(AI_SAFETY)`, `@agent(AI_PLATFORM)`, or `@agent(AI_OBSERVABILITY)` only when user requests implementation of fixes.
- When routing is unclear, start from [USAGE.md](../../../USAGE.md) or run `~/.cursor/commands/route-session.ps1`.
