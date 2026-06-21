# Cursor Prompt: Skills Routing

**Usage:** Paste with task one-liner. Pick skill(s) only — not `@agent` unless escalation needed.

**Reference:** [SKILLS.md](../skills/SKILLS.md) | [USAGE.md](../USAGE.md) | CLI: `templates/commands/route-skill.ps1`

---

## Inputs

```
Task: <one sentence>
Phase: <optional — design | implement | review | release | debug>
```

---

## Instructions for Cursor

Output **only**:

| Field | Content |
|-------|---------|
| **Primary skill** | `skill-name` + trigger match (one line) |
| **Sequence** | Ordered follow-ups (max 4), if multi-step |
| **Orchestrator** | If multi-FE → `orchestrate-frontend-delivery` first |
| **Escalation agent** | Optional `@agent` when skill ends (one line) |
| **Skip** | Near-duplicate skills not needed |

### Routing rules

- One **primary** skill per phase; chain only when output of step N feeds step N+1.
- API evolution: `check-api-backward-compatibility` before `handle-breaking-change`.
- Bug: `reproduce-and-document-failure` → `fix-bug-systematically` → `add-tests-for-change`.
- Release: `validate-pre-deploy` before `prepare-release` unless only versioning.
- Large FE scope: `orchestrate-frontend-delivery` instead of listing 8 FE skills.

Do not paste SKILL.md bodies. Do not list all 64 skills — only matches.

If no skill fits, say so and suggest `@agent` via `plan-cursor-agents-routing.md`.
