# Hooks — User Guide

Hooks run **automatically** at Cursor lifecycle events. You do not invoke them in chat. Sync: `python templates/commands/sync-cursor.py`.

Technical sync details: [README.md](README.md) in this folder. Planning new hooks: [plan-cursor-hooks.md](../prompts/plan-cursor-hooks.md).

---

## Lifecycle (order matters within each event)

```
beforeSubmitPrompt → … agent work … → beforeReadFile / preToolUse / beforeShellExecution / beforeMCPExecution
  → afterFileEdit → stop / subagentStart / subagentStop
```

---

## What runs when

| Event | Scripts | You may see |
|-------|---------|-------------|
| `beforeSubmitPrompt` | `log-prompt-context`, `log-resource-usage`, `validate-template-consistency` | Silent; logs under `.cursor/logs/` |
| `beforeReadFile` | `redact-sensitive-read` | `.env`, keys redacted before model |
| `preToolUse` (Read) | `log-resource-usage` | Silent ledger update |
| `beforeShellExecution` | `log-cursor-activity`, `validate-git-commands`, `validate-pre-push`, `block-destructive-shell`, `validate-db-shell-operations` | **Deny** on force-push main, destructive shell, bad commit msg; tests before push |
| `beforeMCPExecution` | `validate-mcp-operations` | **Confirm** on state-changing MCP tools |
| `afterFileEdit` | `log-cursor-activity`, `format-after-edit`, `validate-template-consistency` | Auto-format (black/prettier/gofmt) |
| `subagentStart` / `subagentStop` | `log-resource-usage` | Silent |
| `preCompact` / `afterAgentResponse` | `log-resource-usage` | Silent; context/token ledger updates |
| `stop` | `log-cursor-activity`, `log-resource-usage`, `suggest-commit-on-stop` | Commit suggestions in hooks channel |

Unix variant: same scripts as `.sh` via `hooks.unix.json` when sync `--hooks-variant auto` on macOS/Linux.

---

## User-visible blocks (what to do)

| Blocked / gated | Cause | Fix |
|-----------------|-------|-----|
| `git push --force` to main/master | `validate-git-commands` | Use `--force-with-lease` or branch policy |
| `rm -rf /`, `DROP TABLE`, hard reset | `block-destructive-shell` / `validate-db-shell-operations` | Narrow command; explicit approval for DB writes |
| MCP write/deploy | `validate-mcp-operations` | Confirm in UI or rephrase as read-only |
| Non-conventional commit | `validate-git-commands` | Fix message or `.cursor/allow-non-conventional-commit` |
| Push without tests | `validate-pre-push` | Run tests locally; install missing runner (poetry/npm/pytest) |
| Push with missing test runner | `validate-pre-push` | Install poetry/npm/pytest or set `modes.pre_push` to `advisory` |
| DB write without DB client | (fixed) | `grep update` / `terraform apply` no longer gated |
| MCP read tool misclassified | (fixed) | Catalog in `hooks/policy/mcp_tools.json` |

---

## Hook policy engine

DB shell, git, and MCP gates use a **shared policy engine** (not inline regex in each script):

| Path | Purpose |
|------|---------|
| `.cursor/hooks/policy/hook_policy.py` | Classifier (requires **Python 3.10+** on PATH) |
| `.cursor/hooks/policy/default.policy.json` | Default deny/ask/allow rules |
| `.cursor/hooks/policy/mcp_tools.json` | Per-server MCP tool risk catalog |
| `.cursor/hook-policy.json` | Optional project overrides (see `templates/hook-policy.example.json`) |

**Modes** (`modes` in policy JSON): `off` | `log` | `allow` | `ask` | `deny` | `advisory` per domain (`db_shell`, `mcp_write`, `mcp_unknown`, `git_commit_format`, `pre_push`, …).

**`pre_push` modes:** `deny` (default) blocks push when tests fail; missing runner → **ask** (not silent allow). `advisory` logs `pre_push_runner_missing` / `pre_push_tests_failed` to stderr and allows push. `off` / `allow` skip the gate entirely.

**Principles:**
- **Deny** irreversible ops (`DROP DATABASE`, force-push to main)
- **Ask** state-changing ops (DB migrations, MCP writes) and **uncataloged MCP tools** (`mcp_unknown: ask`)
- **Allow** cataloged reads (`SELECT`, `list_*`, `get_*` MCP tools)
- DB rules require a **DB client binary** — bare SQL keywords in `grep`/`echo` are ignored

**Tests:** `poetry install --with dev && poetry run pytest templates/hooks/tests -q`  
(Alternative: `pip install -e ".[dev]"` then `pytest templates/hooks/tests -q`; or `python -m unittest discover -s templates/hooks/tests -p "test_*.py"`.)

**Policy errors:** The engine **fails open** on stdout (`permission: allow`) when JSON is invalid or the engine errors, so hooks do not brick Cursor sessions. Structured audit events are written to **stderr** (JSON lines: `policy_load_failed`, `policy_engine_error`, `invalid_hook_payload`). Check Cursor hook debug output or redirect stderr when troubleshooting. Tighten behavior via `modes.policy_load_error` / `modes.policy_engine_error` in `.cursor/hook-policy.json` (`ask` | `deny`; default `allow`).

### Secure baseline (recommended for regulated / production repos)

Copy [`hook-policy.example.json`](../hook-policy.example.json) to `.cursor/hook-policy.json` and start from the **secure baseline** block (or merge these modes):

```json
{
  "modes": {
    "policy_load_error": "ask",
    "policy_engine_error": "deny",
    "mcp_unknown": "ask",
    "mcp_write": "ask",
    "db_shell": "ask",
    "shell_destructive": "deny",
    "pre_push": "deny"
  }
}
```

- **`policy_load_error: ask`** — corrupt policy JSON prompts before continuing (instead of silent allow).
- **`policy_engine_error: deny`** — classifier exceptions block gated shell/MCP/pre-push actions until fixed.
- Keep **`pre_push: deny`** unless CI owns test gates; use **`advisory`** only when the hook should warn without blocking.

Default `default.policy.json` stays fail-open on engine errors so personal/dev machines are not bricked; the secure baseline is opt-in via project override.

**Regenerate MCP catalog** (optional):  
`python templates/hooks/policy/sync_mcp_policy.py --mcps-dir <path-to-mcps> --write`

---

## Related skills (when hooks flag an issue)

| Hook context | Skill |
|--------------|-------|
| Destructive shell | `suggest-commands-dont-run-destructive` |
| Sensitive reads / output | `redact-sensitive-in-output`, `sensitive-data-handling` |
| Session end / commits | `prepare-atomic-commit` |
| Pre-push / deploy | `validate-pre-deploy` |
| Template edits | `skills-consistency` rule + `validate-template-consistency` hook |

Hooks enforce; skills guide agent reasoning. See [USAGE.md](../USAGE.md).

---

## Logs

- Activity: `.cursor/logs/cursor-activity-YYYY-MM-DD.jsonl`
- Resource ledger: `.cursor/logs/resource-ledger/active.json` (rules/`skills_matched`/`skills_read`/spawned subagents/hooks used this turn; archived summaries in `cursor-resources-*.jsonl`). Writes use an exclusive lock + atomic replace (`active.json.lock`, temp file) to avoid lost updates when multiple hook events fire in one generation.

Do not commit `.cursor/logs/` if they contain prompts or secrets.

---

## Global vs project hooks

- **Project:** `.cursor/hooks.json` — relative paths; open repo root as workspace.
- **Global:** `~/.cursor/hooks.json` — use `sync-cursor.py --mode ToGlobal` (absolute paths on Windows via `hooks.global.windows.json`).
