# Cursor Prompt: Session Route Map

**Usage:** Paste into Chat/Composer with your **task one-liner** and optional `@files`. Returns a minimal route — not full catalogs.

**Reference:** [USAGE.md](../USAGE.md) | [skills/SKILLS.md](../skills/SKILLS.md) | [rules/RULES.md](../rules/RULES.md) | [hooks/HOOKS_USAGE.md](../hooks/HOOKS_USAGE.md) | [agents/AGENTS_USAGE.md](../agents/AGENTS_USAGE.md) | CLI: `templates/commands/route-session.ps1`

---

## Inputs (user provides)

```
Task: <one sentence>
Files: <optional @paths>
Constraints: <optional — read-only, no deploy, FE-only, etc.>
```

---

## Instructions for Cursor

Produce **only** the following (no hook code, no skill body paste):

### 1. Route table (max 6 rows)

| Step | Layer | Choice | Why (one line) |
|------|-------|--------|----------------|
| 1 | skill or @agent | name | … |

Rules: **one primary skill OR agent per step**; rules/hooks as notes only.

### 2. Rules note

List **only** rules that apply to given files (from RULES.md globs + always-applied). If no files given, list always-applied only.

### 3. Hooks note

List hooks that may **block or gate** this work (shell, MCP, push) — one line each.

### 4. Token tips

2–3 bullets: what to `@` reference, what not to paste.

### 5. Do not use

Skills/agents that would duplicate the route (boundary enforcement).

---

## Constraints

- Do not paste SKILLS.md, RULES.md, or AGENTS.md contents.
- Prefer orchestration skills (`orchestrate-frontend-delivery`) over listing many FE skills.
- Apply policy precedence: security → rules → skills → agents.
- If task is trivial (single-file fix), return 1–2 row table max.
