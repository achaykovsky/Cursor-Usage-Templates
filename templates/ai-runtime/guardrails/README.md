# Runtime guardrails

Customer-facing safety policies for deployed bots (gateway middleware + prompt templates).

| Doc | Purpose |
|-----|---------|
| [input-sanitization.md](input-sanitization.md) | Untrusted input, length limits, attachment allowlist |
| [output-policy.md](output-policy.md) | No secrets, stack traces, or internal IDs in channel copy |
| [human-handoff.md](human-handoff.md) | Escalation triggers and operator handoff contract |

**Rules:**

- [ai-customer-facing.mdc](../../rules/ai-customer-facing.mdc)
- [ai-safety.mdc](../../rules/ai-safety.mdc)

**Skills:**

- `add-prompt-injection-defenses` ([SKILLS.md](../../skills/SKILLS.md))
- `implement-human-handoff` ([SKILLS.md](../../skills/SKILLS.md))

**System design review** (dimensions 1, 4, 7): [design-review/README.md](../design-review/README.md)
