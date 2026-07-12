# Templates (source)

**Authoring root** for Cursor config. **Edit only here** — project `.cursor/` is generated output, not a source to publish from.

**Start:** [USAGE.md](USAGE.md) — routing hub (mirrors `.cursor/USAGE.md` after sync).

## Layout

| Path | Synced to |
|------|-----------|
| [USAGE.md](USAGE.md) | `.cursor/USAGE.md` |
| [agents/subagents/*.md](agents/subagents/AGENTS.md) | `.cursor/agents/` |
| [rules/*.mdc](rules/) + [rules/RULES.md](rules/RULES.md) | `.cursor/rules/` |
| [skills/**/SKILL.md](skills/) + [skills/SKILLS.md](skills/SKILLS.md) | `.cursor/skills/` |
| [hooks/README.md](hooks/README.md) + [hooks/HOOKS_USAGE.md](hooks/HOOKS_USAGE.md) | `.cursor/hooks/`, `.cursor/hooks.json`, `.cursor/hooks/policy/` |
| [ai-runtime/README.md](ai-runtime/README.md) (+ [design-review/](ai-runtime/design-review/README.md)) | **Synced:** No · **Use:** selective copy into app repos |
| [prompts/README.md](prompts/README.md) | *(repo-only — not synced)* |
| [commands/README.md](commands/README.md) | `~/.cursor/commands/` via `TemplatesToGlobal` only |

Base instruction panels (manual copy to Cursor settings): `workspace.md`, `project.md`, `user.md`.

## Three-hop workflow

```text
templates/  ──TemplatesToGlobal──►  ~/.cursor/  ──FromGlobal──►  project/.cursor/
     │
     └── TemplatesToLocal (+ afterFileEdit hook) ──► project/.cursor/
```

### 1. Templates → global (once, from this repo)

```bash
python templates/commands/sync-cursor.py --mode TemplatesToGlobal
```

Pushes agents, rules, hooks, skills, routing catalogs (`USAGE.md`, `RULES.md`, `SKILLS.md`, `HOOKS_USAGE.md`), and `commands/` to `%USERPROFILE%\.cursor\` (Windows) or `~/.cursor/`.

**Not synced:**

- `prompts/`
- `tests/`
- Logs
- Cache

### 2. Global → any project

```bash
python /path/to/Cursor-Usage-Templates/templates/commands/sync-cursor.py \
  --mode FromGlobal --project-root /path/to/your-project
```

Creates `your-project/.cursor/` including [`USAGE.md`](USAGE.md) — open that in the project after sync.

### 3. Templates → one project (this repo or direct refresh)

```bash
python templates/commands/sync-cursor.py
# default: TemplatesToLocal → project/.cursor/
```

In **this repo**, `afterFileEdit` runs `sync-templates-to-local` so template edits land in `.cursor/` immediately for trying.

See [commands/README.md](commands/README.md) for OS prerequisites and hook variants.
