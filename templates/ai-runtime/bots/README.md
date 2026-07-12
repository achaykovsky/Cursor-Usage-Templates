# Bot manifests

Runtime persona and channel config — **not** Cursor `@agent()` entries.

| Path | Purpose |
|------|---------|
| [manifest.schema.json](manifest.schema.json) | Required fields: id, channels, persona, tools, data retention |
| [examples/faq-bot.json](examples/faq-bot.json) | FAQ-style bot sample |
| [examples/support-bot.json](examples/support-bot.json) | Support bot with handoff sample |

## Validate

```bash
python templates/ai-runtime/validate_bot_runtime.py manifest <path.json>
```

**Authoring:**

- Skill: `design-customer-facing-agent` ([SKILLS.md](../../skills/SKILLS.md))
- Agent: `@agent(BOT_DESIGNER)`

**Policy:** [policy/default.bot.policy.json](../policy/default.bot.policy.json)

**System design review** (checklist dimensions 2, 4): [design-review/README.md](../design-review/README.md)
