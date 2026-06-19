# Model routing reference

## Task category signals

### architectural → frontier

- Multi-file refactor with dependency graph
- New service boundary, ADR, or system design
- Deep debugging across layers (auth + DB + API)
- Security architecture or threat modeling
- Ambiguous requirements needing tradeoff analysis
- Migration with breaking semantics

### general → mid_tier

- Single-feature implementation with clear scope
- API endpoint add/extend (known patterns)
- Code review with structured feedback
- Incident triage with logs/metrics
- Performance investigation (profile-first)
- PM specs, acceptance criteria, sprint breakdown

### routine → lightweight

- Boilerplate scaffold (tests, CRUD stub, config)
- Docstring / README / comment-only edits
- Formatting, rename, import cleanup
- Repetitive logging or telemetry wiring
- Simple bug with localized fix and repro
- DevOps YAML tweaks with existing template

## Escalation overrides (bump one tier)

| Signal | From | To |
|--------|------|-----|
| Auth/crypto/secrets touch | mid_tier or lightweight | frontier |
| >5 files or unknown blast radius | lightweight | mid_tier or frontier |
| User said "production" / "incident" | lightweight | mid_tier |
| Explicit "think hard" / architecture | any | frontier |

## Agent tier hints (default; override by task signals)

See `agent_tier_hints` in [models-catalog.json](models-catalog.json). Opus-tier agents (`ARCHITECT`, `SECURITY`) should stay on frontier even for small diffs when the decision is architectural or security-critical.

## Slug selection within tier

1. Use `tiers[tier].primary`.
2. If user named a model family ("use Codex"), pick matching allowlisted slug in that tier's `alternates`.
3. If primary unavailable in Cursor UI, try `alternates` in order.

## Pairing with Task tool

```text
Task(subagent_type="BACKEND_PYTHON", model="composer-2.5-fast", ...)
Task(subagent_type="ARCHITECT", model="claude-opus-4-8-thinking-high", ...)
```

Model must be in `cursor_allowlist`. Subagent type handles domain; model handles reasoning/cost tier.
