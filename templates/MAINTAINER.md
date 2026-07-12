# Template repo maintenance

**Repo-only** — not synced to `~/.cursor/` or project `.cursor/`. For authors of **Cursor-Usage-Templates**.

**Consumer hub:** [USAGE.md](USAGE.md) (syncs to `.cursor/USAGE.md` in projects).

## Source of truth

Edit only under `templates/`. Project `.cursor/` is sync output — never publish from it.

## Publish workflow

1. `python templates/commands/sync-cursor.py --mode TemplatesToGlobal` — publish to `~/.cursor/`
2. `python templates/commands/sync-cursor.py` — refresh this repo's `.cursor/` (also automatic on `templates/` edits via `sync-templates-to-local` hook)
3. In other projects: `FromGlobal --project-root <project>` — pull global into `project/.cursor/`

See [README.md](README.md) and [commands/README.md](commands/README.md).

## Planning prompts (repo-only)

Paste prompts from [prompts/README.md](prompts/README.md) when routing is unclear during template authoring. They are **not** installed into global or consumer projects.

| Prompt | Use when |
|--------|----------|
| [plan-cursor-session-map.md](prompts/plan-cursor-session-map.md) | Full route for one task (chat) |
| [plan-cursor-agents-routing.md](prompts/plan-cursor-agents-routing.md) | `@agent` only (chat) |
| [plan-cursor-skills-routing.md](prompts/plan-cursor-skills-routing.md) | Skills only (chat) |
| [plan-cursor-model-routing.md](prompts/plan-cursor-model-routing.md) | Model tier + slug only (chat) |
| [plan-cursor-rules-audit.md](prompts/plan-cursor-rules-audit.md) | Rules for given files (chat) |
| [plan-cursor-hooks.md](prompts/plan-cursor-hooks.md) | Extend hooks |
| [plan-cursor-activity-logging.md](prompts/plan-cursor-activity-logging.md) | Activity logs |
| [plan-ai-infrastructure.md](prompts/plan-ai-infrastructure.md) | Customer-facing bot / AI platform (greenfield) |
| [plan-python-remediation-overview.md](prompts/plan-python-remediation-overview.md) | Python hooks/sync remediation (P0–P3) |

CLI alternatives (installed to `~/.cursor/commands/` after step 1): `route-session.ps1`, `route-agent.ps1`, `route-skill.ps1`, `route-model.ps1`, `route-rules.ps1`.
