# Cursor Prompt: Agent Routing

**Usage:** Paste with task one-liner. Pick `@agent(NAME)` only — not skills or full workflows.

**Reference:** [agents/AGENTS.md](../agents/AGENTS.md) | [agents/AGENTS_USAGE.md](../agents/AGENTS_USAGE.md) | [USAGE.md](../USAGE.md) | CLI: `templates/commands/route-agent.ps1`

---

## Inputs

```
Task: <one sentence>
Stack: <optional — Python, Go, React, etc.>
```

---

## Instructions for Cursor

Output **only**:

| Field | Content |
|-------|---------|
| **Primary** | `@agent(NAME)` + one-line why |
| **Optional secondary** | Second agent if handoff needed (sequence) |
| **Escalation** | When to switch agent mid-work |
| **Avoid** | Agents that overlap or wrong domain (e.g. `TESTER` vs `FE_TEST_ENGINEER`) |

### Routing rules

- FE UI/UX/a11y/CWV → `FE_*` prefix; cross-stack → `TESTER`, `PERFORMANCE`, `SECURITY`.
- Opus agents (`SECURITY`, `ARCHITECT`) only for security/architecture decisions — not routine code edits.
- Code-heavy implementation → `BACKEND_*`, `FE_UI_ENGINEER`, `DEVOPS` (Composer-tier).
- Planning/specs → `PM`; docs → `DOCS`; prod incidents → `INCIDENT`.

Max **2 agents** in recommendation unless user asked for full delivery chain.

Do not paste agent prompt files. Do not recommend skills unless user also needs workflow steps (then point to `plan-cursor-skills-routing.md`).
