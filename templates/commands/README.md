# sync-cursor (cross-platform)

Syncs Cursor config (agents, rules, hooks, skills, commands, routing catalogs) between **`templates/`**, the project **`.cursor/`**, and the **user Cursor directory** (`%USERPROFILE%\.cursor\` on Windows, `~/.cursor/` on macOS and Linux).

Start at [`USAGE.md`](../USAGE.md) for routing (syncs to `.cursor/USAGE.md`). Does **not** sync `prompts/`, tests, logs, CI, or cache.

## Source of truth

**`templates/` is the only authoring source.** Nothing is ever copied *from* project `.cursor/`.

| Layer | Authoritative path | Consumed by |
|-------|-------------------|-------------|
| **Templates** | `templates/` in Cursor-Usage-Templates | All sync modes except `FromGlobal` |
| **Global** | `~/.cursor/` | `FromGlobal` into any project |
| **Project** | `project/.cursor/` | Cursor runtime in that project |

**Recommended flow (single template → many projects):**

```text
templates/  ──TemplatesToGlobal──►  ~/.cursor/  ──FromGlobal──►  project/.cursor/
```

1. Edit under `templates/` in this repo.
2. Run `--mode TemplatesToGlobal` to publish to `~/.cursor/`.
3. In other projects, run `--mode FromGlobal --project-root <project>`.

**This repo (try immediately):** edits under `templates/` auto-sync to `.cursor/` via the `sync-templates-to-local` hook (`afterFileEdit`). Run `python templates/commands/sync-cursor.py` manually when hooks are not installed yet.

`sync-cursor.ps1` delegates to `sync-cursor.py` — not a second implementation.

**Entry points:**

| Platform | Command |
|----------|---------|
| Any (recommended) | `python templates/commands/sync-cursor.py` |
| Windows PowerShell | `.\templates\commands\sync-cursor.ps1` (delegates to the Python script; requires Python on `PATH`. Defaults `-ProjectRoot` to the current working directory.) |

## Prerequisites by OS

### Windows

- **Python 3.10+** on `PATH` as `python` or `python3` (required for sync).
- **Hooks (PowerShell scripts):** [PowerShell 7+](https://github.com/PowerShell/PowerShell) (`pwsh`) so `.cursor/hooks.json` commands can run. Windows PowerShell 5.1 is not used by the bundled hooks.
- **Hook policy engine:** Python 3.10+ on `PATH` for `validate-db-shell-operations`, `validate-git-commands`, and `validate-mcp-operations` (delegates to `.cursor/hooks/policy/hook_policy.py`).

### macOS

- **Python 3.10+** (e.g. `brew install python` or Xcode CLT).
- **Sync / optional:** same Python for `sync-cursor.py`.
- **Hooks (bash scripts):** `bash` (preinstalled), **`jq`** (`brew install jq`) for JSON hooks; **`python3`** for `redact-sensitive-read.sh` and **hook policy** (`validate-db-shell-operations`, `validate-git-commands`, `validate-mcp-operations`). After sync with the default **`--hooks-variant auto`**, the active config is **`unix/hooks.json` → `.cursor/hooks.json`** (bash commands).
- Make scripts executable if needed: `chmod +x .cursor/hooks/scripts/*.sh` (usually not required when invoking via `bash script.sh`).

### Linux

- **Python 3.10+** (`python3` from distro packages).
- **Hooks:** `bash`, **`jq`** (e.g. `apt install jq` / `dnf install jq`), **`python3`**. Default **`auto`** installs Unix/bash hook commands the same way as macOS.

## Modes (`--mode` / `-Mode`)

| Mode | Direction | Use case |
|------|-----------|----------|
| **`TemplatesToLocal`** (default) | `templates/` → project `.cursor/` | Refresh one project from repo templates. |
| **`TemplatesToGlobal`** | `templates/` → user `~/.cursor/` | Publish repo templates as your global default. |
| **`FromGlobal`** | User `~/.cursor/` → project `.cursor/` | Initialize any project from global. |

```bash
python templates/commands/sync-cursor.py
python templates/commands/sync-cursor.py --mode TemplatesToGlobal
python templates/commands/sync-cursor.py --mode FromGlobal
python templates/commands/sync-cursor.py --dry-run --verbose
```

**Flags:** `--dry-run` prints `DRY` lines and does not write files; `--verbose` emits structured JSON logs to stderr.

```powershell
.\templates\commands\sync-cursor.ps1
.\templates\commands\sync-cursor.ps1 -Mode TemplatesToGlobal
.\templates\commands\sync-cursor.ps1 -Mode FromGlobal
```

## Hooks variant (`--hooks-variant` / `-HooksVariant`)

Controls which **OS hook set** is used (`windows` → `*.ps1`, `unix` → `*.sh`):

| Value | Behavior |
|-------|----------|
| **`auto`** (default) | **Windows:** `windows/hooks.json` + `windows/*.ps1`. **macOS/Linux:** `unix/hooks.json` + `unix/*.sh`. |
| **`windows`** | `windows/hooks.json` + `windows/*.ps1`. |
| **`unix`** | `unix/hooks.json` + `unix/*.sh`. |

## Components (`--components`)

Limit what `TemplatesToLocal` / `TemplatesToGlobal` syncs:

| Value | Copies |
|-------|--------|
| *(default)* | `agents`, `rules`, `hooks`, `skills`, `catalogs` |
| `hooks` | `hooks.json`, `hooks/scripts/*`, `hooks/policy/` only |
| `hooks,rules` | hooks bundle + `rules/*.mdc` |

```bash
python templates/commands/sync-cursor.py --components hooks
python templates/commands/sync-cursor.py --components hooks,rules
```

**`FromGlobal`:** Scripts are filtered by this variant (only `*.ps1` or `*.sh` from `hooks/scripts/`). If global has no scripts for the current OS, the sync copies **`hooks.json` from `templates/hooks/`** (when missing on the source) and **`hooks/scripts` from `templates/hooks/windows/` or `unix/`** so the destination still works. Run from a project that contains `templates/` when using that fallback.

## What Each Mode Syncs

### `TemplatesToLocal` (default)

| Source | Destination |
|--------|-------------|
| `templates/agents/subagents/*.md` | `.cursor/agents/` |
| `templates/rules/*.mdc` | `.cursor/rules/` |
| `templates/hooks/windows/hooks.json` or `unix/hooks.json` (see `--hooks-variant`) | `.cursor/hooks.json` |
| `templates/hooks/windows/*.ps1` or `templates/hooks/unix/*.sh` | `.cursor/hooks/scripts/` (flat; OS only) |
| `templates/hooks/policy/` | `.cursor/hooks/policy/` |
| `templates/skills/**/SKILL.md` | `.cursor/skills/**/` |
| Routing catalogs ([`USAGE.md`](../USAGE.md), [`rules/RULES.md`](../rules/RULES.md), [`skills/SKILLS.md`](../skills/SKILLS.md), [`hooks/HOOKS_USAGE.md`](../hooks/HOOKS_USAGE.md), [`hooks/README.md`](../hooks/README.md)) | `.cursor/` (mirrored paths) |

**Not synced:** `prompts/`, `tests/`, logs, CI, cache (`__pycache__`, `.pytest_cache`). Commands stay under `templates/commands/` locally (not copied into `.cursor/`).

### `TemplatesToGlobal`

Same sources as **`TemplatesToLocal`**, but destination is **`~/.cursor/`** instead of project `.cursor/`. Also copies top-level `templates/commands/*.{py,ps1,sh}` and `README.md` to **`~/.cursor/commands/`** (never `tests/`). Includes **`USAGE.md`** and other routing catalogs. Installs **`windows/hooks.global.json`** (Windows) or **`unix/hooks.global.json`** (macOS/Linux) with absolute hook script paths.

### `FromGlobal`

Copies from **`~/.cursor/`** into project **`.cursor/`** only (global must have been filled via `TemplatesToGlobal`):

| Category | Paths (relative to each Cursor root) |
|----------|----------------------------------------|
| Agents | `agents/*.md` |
| Rules | `rules/*.mdc` |
| Hooks | `hooks.json` at the Cursor root, plus `hooks/scripts/*.{ps1,sh}` |
| Skills | `skills/**/SKILL.md` (tree preserved) |
| Routing catalogs | [`USAGE.md`](../USAGE.md), [`rules/RULES.md`](../rules/RULES.md), [`skills/SKILLS.md`](../skills/SKILLS.md), [`hooks/HOOKS_USAGE.md`](../hooks/HOOKS_USAGE.md), [`hooks/README.md`](../hooks/README.md) |

For **`TemplatesToLocal`:** Existing `*.md` in `agents/`, `*.mdc` in `rules/`, stale `SKILL.md` trees under `skills/`, and hook scripts at the destination are cleared or pruned before copy.

For **`FromGlobal`**, existing `*.md` in `agents/`, `*.mdc` in `rules/`, and **all** `*.ps1` and `*.sh` in `hooks/scripts/` at the **destination** are cleared, then only scripts matching **`--hooks-variant`** (`*.ps1` or `*.sh`) are copied from global. If none match, the sync falls back to **`templates/hooks/windows/`** or **`templates/hooks/unix/`** when the command is run from a project that contains `templates/` (see **Hooks variant** above). **`hooks.json`** is copied from global when present; otherwise from `templates/hooks/` for the variant. **`FromGlobal`** also prunes stale skills under `skills/`.

## Safety: Empty Sources

If a category has **no files** on the source side (missing folder, or folder with no matching files), that category is **skipped**. The script does **not** clear the destination from an empty source—so you cannot accidentally wipe global or project config by running with missing inputs.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--project-root` / `-ProjectRoot` | Current working directory in `sync-cursor.ps1`; parent of `templates/` in `sync-cursor.py` | Root of the project whose `.cursor/` is read or written. |
| `--mode` / `-Mode` | `TemplatesToLocal` | `TemplatesToLocal`, `TemplatesToGlobal`, or `FromGlobal`. |
| `--hooks-variant` / `-HooksVariant` | `auto` | `auto`, `windows`, or `unix` — selects which script extension and hooks JSON to use. |
| `--components` | *(all)* | Comma-separated: `agents`, `rules`, `hooks`, `skills`, `catalogs`. Example: `--components hooks`. |
| `--trigger-file` | *(empty)* | Edited path under `templates/` (used by `sync-templates-to-local` hook). Infers `--components`; no-op for `templates/commands/` and `templates/prompts/`. |

**`-ProjectRoot`:** When you pass it explicitly, use the full project path you intend (the script does not resolve relative paths with `Resolve-Path`).

## Auto-sync on template edits (this repo)

The `sync-templates-to-local` hook runs on `afterFileEdit` when the edited file is under `templates/`:

| Edited path | Synced component |
|-------------|------------------|
| `templates/agents/**` | `agents` |
| `templates/rules/**` | `rules` |
| `templates/hooks/**` | `hooks` |
| `templates/skills/**` | `skills` |
| Routing catalogs (`USAGE.md`, `rules/RULES.md`, etc.) | `catalogs` |
| `templates/commands/**`, `templates/prompts/**` | *(skipped — not installed into `.cursor/`)* |

Requires Python on `PATH` and `templates/commands/sync-cursor.py`. Run a full `TemplatesToLocal` once after cloning or when hooks are disabled.

## Usage

**From a project that contains `templates/` (e.g. this repo or a submodule/symlink):**

```bash
python templates/commands/sync-cursor.py
```

```powershell
.\templates\commands\sync-cursor.ps1
```

`sync-cursor.py` infers project root as the parent of `templates/` (`templates/commands/` → two levels up). `sync-cursor.ps1` now defaults to the current working directory unless `-ProjectRoot` is provided.

**Pull global Cursor config into the project:**

```bash
python templates/commands/sync-cursor.py --mode FromGlobal
```

## Global Use Across Cursor Projects

Use this script from a central templates repo so any project can sync Cursor config without embedding everything by hand.

### Option A: Clone Once, Symlink or Copy

1. Clone this repo to a fixed location, e.g. `~/cursor/Cursor-Usage-Templates` (macOS/Linux) or `%USERPROFILE%\cursor\Cursor-Usage-Templates` (Windows).
2. In each project, either:
   - **Symlink** the `templates` folder, or
   - Add the repo as a submodule: `git submodule add <repo-url> templates`
3. Run `python templates/commands/sync-cursor.py` from the project root (or pass `--project-root`)

### Option B: Global Script with `--project-root`

1. Clone this repo to e.g. `%USERPROFILE%\cursor\Cursor-Usage-Templates` (Windows) or `~/cursor/Cursor-Usage-Templates` (macOS/Linux).
2. From any project directory:

   ```bash
   python ~/cursor/Cursor-Usage-Templates/templates/commands/sync-cursor.py --project-root "$(pwd)"
   ```

3. Add `--mode FromGlobal` when initializing a project from `~/.cursor/`.

### Option C: Explicit Project Root

Pass `--project-root` when the script is not under that project’s `templates/commands/` layout.

**Recommended:** Option A with a submodule or symlink so each project opts in and the default `--project-root` inference stays correct.

## After Sync

- **Start here:** [`USAGE.md`](../USAGE.md) (syncs to `.cursor/USAGE.md` after sync or `FromGlobal`)
- **Agents** appear in Cursor Settings → Subagents
- **Rules** apply via globs when editing matching files
- **Hooks** run at lifecycle events
- **Skills** are available to the agent when relevant workflows are triggered
- **Commands** (`sync-cursor.py`, routing scripts, etc.) live under `templates/commands/` in this repo, or `~/.cursor/commands/` after `TemplatesToGlobal`

---

## Activity log query

Summarize `cursor-activity-*.jsonl` by `generation_id` (prompt → files → commands → status).

| Platform | Command |
|----------|---------|
| Python | `python templates/commands/cursor_activity.py query --date 2026-02-25 --project-root .` |
| Windows | `.\templates\commands\query-cursor-logs.ps1 -Date 2026-02-25` |

**Flags:** `-Date yyyy-MM-dd`, `-GenerationId <id>`, `-ProjectRoot <path>` (PowerShell) / `--date`, `--generation-id`, `--project-root` (Python).

Requires activity logs from `log-cursor-activity` hook (sync hooks first).

---

## Routing CLI (deterministic)

Keyword/heuristic routing — same structured output as planning prompts, without pasting into chat.

| Script | Python equivalent | Purpose |
|--------|-------------------|---------|
| `route-session.ps1` | `python routing.py session --task "..." --files a.py` | Session route table (max 6 rows) |
| `route-agent.ps1` | `python routing.py agent --task "..."` | Primary/secondary `@agent` |
| `route-skill.ps1` | `python routing.py skill --task "..." --phase implement` | Skill chain |
| `route-model.ps1` | `python routing.py model --task "..."` | Category, tier, slug from `models-catalog.json` |
| `route-rules.ps1` | `python routing.py rules --files src/a.py` | Always-applied + file-scoped rules |

```powershell
.\templates\commands\route-session.ps1 -Task "fix auth bug" -Files src/auth.py
.\templates\commands\route-agent.ps1 -Task "review PR for security"
.\templates\commands\route-skill.ps1 -Task "deploy to staging" -Phase release
.\templates\commands\route-model.ps1 -Task "refactor service boundaries"
.\templates\commands\route-rules.ps1 -Files src/api/router.py
```

All scripts support `--help`. Shared logic: `routing.py`, `cursor_activity.py`.

---

## Contributors (this repo)

- **Python 3.10+** required (`requires-python` in `pyproject.toml`).
- Install dev deps: `poetry install --with dev` (or `pip install -e ".[dev]"`).
- Run tests: `poetry run pytest templates/hooks/tests templates/commands/tests -q`.
