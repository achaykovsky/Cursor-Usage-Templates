# Runtime guardrails

Customer-facing safety policies for deployed bots (gateway middleware + prompt templates).

| Doc | Purpose |
|-----|---------|
| [input-sanitization.md](input-sanitization.md) | Untrusted input, length limits, attachment allowlist |
| [output-policy.md](output-policy.md) | No secrets, stack traces, or internal IDs in channel copy |
| [human-handoff.md](human-handoff.md) | Escalation triggers and operator handoff contract |

**Rules:** [ai-customer-facing.mdc](../../rules/ai-customer-facing.mdc), [ai-safety.mdc](../../rules/ai-safety.mdc). **Skills:** [add-prompt-injection-defenses](../../skills/SKILLS.md), [implement-human-handoff](../../skills/SKILLS.md).

**System design review:** checklist dimensions 1 (hallucination), 4 (prompt coupling), 7 (confidence → handoff) — [design-review/README.md](../design-review/README.md).
