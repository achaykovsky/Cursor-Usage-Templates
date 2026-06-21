# Cursor Prompt: Rules Audit

**Usage:** Paste with file paths or globs. Returns which rules apply — not rule text.

**Reference:** [RULES.md](../rules/RULES.md) | [USAGE.md](../USAGE.md) | CLI: `templates/commands/route-rules.ps1`

---

## Inputs

```
Files: <@paths or glob patterns>
Task: <optional — edit, review, document>
```

---

## Instructions for Cursor

Output **only**:

### 1. Always-applied rules

List from RULES.md always-applied section (short names only).

### 2. File-scoped rules

| File or glob | Matching rules |
|--------------|----------------|
| … | … |

### 3. Overlap summary

One paragraph: which rules stack for the primary file type (e.g. Python API → `python-backend` + `api-contract` + always-applied).

### 4. Authoring note

If editing `.cursor/skills/**/SKILL.md`, note `skills-consistency.mdc`.

Do **not** paste `.mdc` file contents. Do **not** invent globs — use RULES.md only.

If paths unknown, return always-applied + ask for one representative file.
