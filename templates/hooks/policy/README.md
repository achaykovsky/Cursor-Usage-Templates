# Hook policy engine

**Hub:** [USAGE.md](../../USAGE.md) | **Hooks mapping:** [README.md](../README.md) | **User guide:** [HOOKS_USAGE.md](../HOOKS_USAGE.md)

Classifies `beforeShellExecution` (DB/git) and `beforeMCPExecution` (MCP) payloads.

## Files

| File | Role |
|------|------|
| `hook_policy.py` | Engine CLI: `python hook_policy.py <shell-db\|shell-git\|mcp>` |
| `mcp_classify.py` | Shared MCP tool-name heuristics (used by engine + `sync_mcp_policy.py`) |
| `default.policy.json` | Default rules, modes, and `mcp.global_*` prefix lists |
| `mcp_tools.json` | MCP server tool risk catalog |
| `sync_mcp_policy.py` | Seed/update `mcp_tools.json` from MCP tool descriptors (reads heuristics from `default.policy.json`) |

Edit `default.policy.json` `mcp.global_*` keys once — both the live engine fallback and `sync_mcp_policy.py` use `mcp_classify.py`.

## Fail-open contract

**Decision:** Hooks must not brick Cursor sessions when Python is missing, policy JSON is corrupt, or the classifier raises. **Stdout** always emits a valid hook response JSON object; on infrastructure or engine errors the default is `permission: allow` (exit 0).

**Tradeoff:** Silent allow on failure can let destructive operations through when policy is misconfigured. Operators need **structured evidence** on stderr; regulated projects can opt into stricter modes via `.cursor/hook-policy.json`.

| Error class | Stdout (default) | Stderr | Override (`modes`) |
|-------------|------------------|--------|---------------------|
| Invalid hook payload JSON | `allow` | `WARN` — `invalid_hook_payload` | — |
| Corrupt / unreadable policy file | `allow` (partial merge continues) | `ERROR` — `policy_load_failed` | `policy_load_error`: `ask` \| `deny` |
| Classifier exception | `allow` | `ERROR` — `policy_engine_error` | `policy_engine_error`: `ask` \| `deny` |
| All policy sources empty after failures | `allow` | `ERROR` — `policy_empty` | — |

### Stderr schema (one JSON object per line)

```json
{"timestamp":"2026-06-19T12:00:00+00:00","level":"error","component":"hook_policy","event":"policy_load_failed","path":"/path/to/default.policy.json","error_type":"JSONDecodeError"}
```

Fields: `timestamp` (ISO8601 UTC), `level`, `component`, `event`, optional `path`, `domain`, `error_type`, `message`. No secrets or full command bodies.

Shell wrappers (`hook-common.ps1` / `hook-common.sh`) forward Python stderr to the host (not discarded).

## Project overrides

Copy [`hook-policy.example.json`](../../hook-policy.example.json) to `.cursor/hook-policy.json` and adjust `modes` or rule lists.

Example stricter error handling:

```json
"modes": {
  "policy_load_error": "ask",
  "policy_engine_error": "allow"
}
```

## Sync

Copied to `.cursor/hooks/policy/` by `sync-cursor.py` with hook scripts.

## Tests

From repo root: `poetry run pytest templates/hooks/tests templates/commands/tests -q`
