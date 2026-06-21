# sync-cursor (cross-platform)

Syncs Cursor config (agents, rules, hooks, skills, commands, routing catalogs) between **`templates/`**, the project **`.cursor/`**, and the **user Cursor directory** (`%USERPROFILE%\.cursor\` on Windows, `~/.cursor/` on macOS and Linux).

Start at [`USAGE.md`](../USAGE.md) for routing (syncs to `.cursor/USAGE.md`). Does **not** sync `prompts/`, tests, logs, CI, or cache.

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
- **Hooks (bash scripts):** `bash` (preinstalled), **`jq`** (`brew install jq`) for JSON hooks; **`python3`** for `redact-sensitive-read.sh` and **hook policy** (`validate-db-shell-operations`, `validate-git-commands`, `validate-mcp-operations`). After sync with the default **`--hooks-variant auto`**, the active config is **`hooks.unix.json` → `.cursor/hooks.json`** (bash commands).
- Make scripts executable if needed: `chmod +x .cursor/hooks/scripts/*.sh` (usually not required when invoking via `bash script.sh`).

### Linux

- **Python 3.10+** (`python3` from distro packages).
- **Hooks:** `bash`, **`jq`** (e.g. `apt install jq` / `dnf install jq`), **`python3`**. Default **`auto`** installs Unix/bash hook commands the same way as macOS.

## Modes (`--mode` / `-Mode`)

| Mode | Direction | Use case |
|------|-----------|----------|
| **`TemplatesToLocal`** (default) | `templates/` → project `.cursor/` | Refresh one project from repo templates. |
| **`TemplatesToGlobal`** | `templates/` → user `~/.cursor/` | Publish repo templates as your global default. |
| **`ToGlobal`** | Project `.cursor/` + `templates/commands/` → user `~/.cursor/` | Publish a customized project setup globally. |
| **`FromGlobal`** | User `~/.cursor/` → project `.cursor/` + `templates/commands/` | Initialize any project from global. |

```bash
python templates/commands/sync-cursor.py
python templates/commands/sync-cursor.py --mode TemplatesToGlobal
python templates/commands/sync-cursor.py --mode ToGlobal
python templates/commands/sync-cursor.py --mode FromGlobal
python templates/commands/sync-cursor.py --dry-run --verbose
```

**Flags:** `--dry-run` prints `DRY` lines and does not write files; `--verbose` emits structured JSON logs to stderr.

```powershell
.\templates\commands\sync-cursor.ps1
.\templates\commands\sync-cursor.ps1 -Mode TemplatesToGlobal
.\templates\commands\sync-cursor.ps1 -Mode ToGlobal
.\templates\commands\sync-cursor.ps1 -Mode FromGlobal
```

## Hooks variant (`--hooks-variant` / `-HooksVariant`)

Controls which **OS hook set** is used (`windows` → `*.ps1`, `unix` → `*.sh`):

| Value | Behavior |
|-------|----------|
| **`auto`** (default) | **Windows:** `templates/hooks/hooks.json` + `templates/hooks/windows/*.ps1`. **macOS/Linux:** `hooks.unix.json` + `templates/hooks/unix/*.sh`. |
| **`windows`** | `templates/hooks/hooks.json` + `templates/hooks/windows/*.ps1`. |
| **`unix`** | `hooks.unix.json` (if present) + `templates/hooks/unix/*.sh`. |

**`ToGlobal` / `FromGlobal`:** Scripts are filtered by this variant (only `*.ps1` or `*.sh` from `hooks/scripts/`). If the source has no scripts for the current OS (e.g. global was filled on another OS), the sync copies **`hooks.json` from `templates/hooks/`** (when missing on the source) and **`hooks/scripts` from `templates/hooks/windows/` or `unix/`** so the destination still works. Run from the repo root so `templates/` is found.

## What Each Mode Syncs

### `TemplatesToLocal` (default)

| Source | Destination |
|--------|-------------|
| `templates/agents/subagents/*.md` or (fallback) `~/.cursor/agents/*.md` | `.cursor/agents/` |
| `templates/rules/*.mdc` | `.cursor/rules/` |
| `templates/hooks/hooks.json` or `hooks.unix.json` (see variant above) | `.cursor/hooks.json` |
| `templates/hooks/windows/*.ps1` or `templates/hooks/unix/*.sh` | `.cursor/hooks/scripts/` (flat; OS only) |
| `templates/skills/**/SKILL.md` | `.cursor/skills/**/` |
| Routing catalogs ([`USAGE.md`](../USAGE.md), [`rules/RULES.md`](../rules/RULES.md), [`skills/SKILLS.md`](../skills/SKILLS.md), [`hooks/HOOKS_USAGE.md`](../hooks/HOOKS_USAGE.md), [`hooks/README.md`](../hooks/README.md)) | `.cursor/` (mirrored paths) |

**Not synced:** `prompts/`, `tests/`, logs, CI, cache. Commands are not re-copied locally when `templates/commands/` already exists in the project.

**Agent fallback:** If `templates/agents/subagents/` is missing or empty, agents are taken from `~/.cursor/agents/` when that folder has `*.md` files.

### `TemplatesToGlobal`

Same sources as **`TemplatesToLocal`**, but destination is **`~/.cursor/`** instead of project `.cursor/`. Also copies top-level `templates/commands/*.{py,ps1,sh}` and `README.md` to **`~/.cursor/commands/`** (never `tests/`). Includes **`USAGE.md`** and other routing catalogs. Installs **`hooks.global.windows.json`** (Windows) or **`hooks.global.unix.json`** (macOS/Linux) with absolute hook script paths.

### `ToGlobal` / `FromGlobal`

Copies between project **`.cursor/`** and **`~/.cursor/`**, plus **`templates/commands/`** ↔ **`~/.cursor/commands/`**:

| Category | Paths (relative to each Cursor root) |
|----------|----------------------------------------|
| Agents | `agents/*.md` |
| Rules | `rules/*.mdc` |
| Hooks | `hooks.json` at the Cursor root, plus `hooks/scripts/*.{ps1,sh}` |
| Skills | `skills/**/SKILL.md` (tree preserved) |
| Routing catalogs | [`USAGE.md`](../USAGE.md), [`rules/RULES.md`](../rules/RULES.md), [`skills/SKILLS.md`](../skills/SKILLS.md), [`hooks/HOOKS_USAGE.md`](../hooks/HOOKS_USAGE.md), [`hooks/README.md`](../hooks/README.md) |
| Commands | Top-level `*.{py,ps1,sh}` and `README.md` under `templates/commands/` or `~/.cursor/commands/` (never `tests/`) |

For **`TemplatesToLocal`:** Existing `*.md` in `agents/`, `*.mdc` in `rules/`, stale `SKILL.md` trees under `skills/`, and hook scripts at the destination are cleared or pruned before copy.

For **`ToGlobal`** and **`FromGlobal`**, existing `*.md` in `agents/`, `*.mdc` in `rules/`, and **all** `*.ps1` and `*.sh` in `hooks/scripts/` at the **destination** are cleared, then only scripts matching **`--hooks-variant`** (`*.ps1` or `*.sh`) are copied from the source. If none match, the sync falls back to **`templates/hooks/windows/`** or **`templates/hooks/unix/`** when the command is run from a project that contains `templates/` (see **Hooks variant** above). **`hooks.json`** is copied from the source when present; otherwise from `templates/hooks/` for the variant. **`FromGlobal` / `ToGlobal`** also prune stale skills under `skills/`.

## Safety: Empty Sources

If a category has **no files** on the source side (missing folder, or folder with no matching files), that category is **skipped**. The script does **not** clear the destination from an empty source—so you cannot accidentally wipe global or project config by running with missing inputs.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--project-root` / `-ProjectRoot` | Current working directory in `sync-cursor.ps1`; parent of `templates/` in `sync-cursor.py` | Root of the project whose `.cursor/` is read or written. |
| `--mode` / `-Mode` | `TemplatesToLocal` | One of `TemplatesToLocal`, `ToGlobal`, `FromGlobal`. |
| `--hooks-variant` / `-HooksVariant` | `auto` | `auto`, `windows`, or `unix` — selects which script extension and hooks JSON to use (`TemplatesToLocal` and `ToGlobal` / `FromGlobal`). |

**`-ProjectRoot`:** When you pass it explicitly, use the full project path you intend (the script does not resolve relative paths with `Resolve-Path`).

## Usage

**From a project that contains `templates/` (e.g. this repo or a submodule/symlink):**

```bash
python templates/commands/sync-cursor.py
```

```powershell
.\templates\commands\sync-cursor.ps1
```

`sync-cursor.py` infers project root as the parent of `templates/` (`templates/commands/` → two levels up). `sync-cursor.ps1` now defaults to the current working directory unless `-ProjectRoot` is provided.

**Push project Cursor config to global:**

```bash
python templates/commands/sync-cursor.py --mode ToGlobal
```

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

3. Add `--mode ToGlobal` or `--mode FromGlobal` when syncing with `~/.cursor/` instead of templates.

### Option C: Explicit Project Root

Pass `--project-root` when the script is not under that project’s `templates/commands/` layout.

**Recommended:** Option A with a submodule or symlink so each project opts in and the default `--project-root` inference stays correct.

## After Sync

- **Start here:** [`USAGE.md`](../USAGE.md) (syncs to `.cursor/USAGE.md` after sync or `FromGlobal`)
- **Agents** appear in Cursor Settings → Subagents
- **Rules** apply via globs when editing matching files
- **Hooks** run at lifecycle events
- **Skills** are available to the agent when relevant workflows are triggered
- **Commands** (`sync-cursor.py`, routing scripts, etc.) live under `templates/commands/` after `FromGlobal`, or `~/.cursor/commands/` after `TemplatesToGlobal`

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
