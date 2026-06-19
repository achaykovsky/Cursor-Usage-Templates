# Cursor Prompt: Model Routing

**Usage:** Paste with task one-liner. Pick model **tier + slug** only — not full skills or agent prompts.

**Reference:** [route-task-to-model/SKILL.md](../skills/shared-practices/route-task-to-model/SKILL.md) | [models-catalog.json](../skills/shared-practices/route-task-to-model/models-catalog.json)

---

## Inputs

```
Task: <one sentence>
Constraints: <optional — cost, speed, must use Codex, etc.>
```

---

## Instructions for Cursor

Output **only**:

| Field | Content |
|-------|---------|
| **Category** | `architectural` \| `general` \| `routine` |
| **Tier** | frontier \| mid_tier \| lightweight |
| **Slug** | From `cursor_allowlist` in models-catalog.json |
| **Why** | One line (trade-off matrix) |
| **Execution** | Context scope + validation step |
| **Escalate when** | Override signals |

### Routing rules

- Load `models-catalog.json` — never invent slugs.
- Frontier for multi-file design, deep deps, security architecture.
- Mid-tier for daily features, reviews, incidents.
- Lightweight for boilerplate, docs, simple localized edits.
- If `@agent(NAME)` is also needed, note tier; agent choice is separate (`plan-cursor-agents-routing.md`).

Do not paste SKILL.md bodies. Do not list all models — only the recommendation.

To refresh tier picks from the web: run `update-models-catalog.py --dry-run` first.
