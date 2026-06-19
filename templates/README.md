# Templates (source)

**Authoring root** for Cursor config. Everything here syncs into `.cursor/` on projects and into `~/.cursor/` for global use.

**Start:** [USAGE.md](USAGE.md) — routing hub (mirrors `.cursor/USAGE.md` after sync).

## Layout

| Path | Synced to |
|------|-----------|
| [USAGE.md](USAGE.md) | `.cursor/USAGE.md` |
| [agents/subagents/*.md](agents/subagents/) | `.cursor/agents/` |
| [rules/*.mdc](rules/) + [rules/RULES.md](rules/RULES.md) | `.cursor/rules/` |
| [skills/**/SKILL.md](skills/) + [skills/SKILLS.md](skills/SKILLS.md) | `.cursor/skills/` |
| [hooks/](hooks/) + [hooks/HOOKS_USAGE.md](hooks/HOOKS_USAGE.md) | `.cursor/hooks/`, `.cursor/hooks.json` |
| [prompts/*.md](prompts/) | `.cursor/prompts/` |
| [commands/sync-cursor.py](commands/sync-cursor.py) | *(runs sync; not copied)* |

Base instruction panels (manual copy to Cursor settings): `workspace.md`, `project.md`, `user.md`.

## Three-hop workflow

```text
templates/  ──TemplatesToGlobal──►  ~/.cursor/  ──FromGlobal──►  project/.cursor/
     │                                      ▲
     └── TemplatesToLocal ──► project/.cursor/ ──ToGlobal ──────┘
```

### 1. Templates → global (once, from this repo)

```bash
python templates/commands/sync-cursor.py --mode TemplatesToGlobal
```

Pushes agents, rules, hooks, skills, **USAGE.md**, catalogs, and prompts to `%USERPROFILE%\.cursor\` (Windows) or `~/.cursor/`.

### 2. Global → any project

```bash
python /path/to/Cursor-Usage-Templates/templates/commands/sync-cursor.py \
  --mode FromGlobal --project-root /path/to/your-project
```

Creates `your-project/.cursor/` including [`USAGE.md`](USAGE.md) — open that in the project after sync.

### 3. Templates → one project (skip global)

```bash
python templates/commands/sync-cursor.py
# default: TemplatesToLocal → project/.cursor/
```

### Publish project customizations to global

After editing `project/.cursor/`:

```bash
python templates/commands/sync-cursor.py --mode ToGlobal
```

See [commands/README.md](commands/README.md) for OS prerequisites and hook variants.
