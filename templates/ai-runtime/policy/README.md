# Bot Runtime Policy

Portable policy for customer-facing bots. Vocabulary mirrors Cursor hook policy (`deny`, `ask`, `allow`, `advisory`, `log`).

## Files

| File | Purpose |
|------|---------|
| `default.bot.policy.json` | Modes, injection limits, output blocks, handoff, audit defaults |
| `tool-risk-catalog.json` | Tool name → risk tier (`read`, `write`, `destructive`) |

## Enforcement

1. **Gateway middleware** loads policy JSON at startup; hot-reload via versioned config.
2. **Manifest tools** must declare `risk` aligned with catalog entry or explicit override in manifest.
3. **CI** — run `python templates/ai-runtime/validate_bot_runtime.py policy <file>`.

## Mapping to Cursor hooks

| Runtime mode | Hook analog |
|--------------|-------------|
| `tool_write` → `ask` | `validate-mcp-operations` write confirm |
| `tool_destructive` → `deny` | `block-destructive-shell` |
| `tool_unknown` → `ask` | `mcp_unknown` |

Sync tool names into app repos; extend `tool-risk-catalog.json` per product.

**System design review:** checklist dimensions 9 (tenant isolation), 10 (future tool calling), 8 (deterministic business logic) — [design-review/README.md](../design-review/README.md).
