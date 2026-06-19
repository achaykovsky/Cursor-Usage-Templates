# Planning prompts index

**Validated:** 2026-06-19 | **Method:** PM acceptance-criteria review against repo ground truth (`templates/`, `pyproject.toml`, pytest)

Paste prompts from this folder when routing is unclear. Open [USAGE.md](../USAGE.md) for the full navigation hub.

## Status legend

| Status | Meaning |
|--------|---------|
| **Done** | Deliverable complete — prompt exists and/or implementation acceptance criteria met |
| **Partial** | Core work shipped; listed gaps remain |
| **Open** | Plan valid; implementation not started or minimal |
| **Prompt only** | No code deliverable — the markdown file *is* the product |

## Summary

| Plan | Type | Status | Priority |
|------|------|--------|----------|
| [plan-cursor-session-map.md](plan-cursor-session-map.md) | Routing | **Prompt only** | — |
| [plan-cursor-agents-routing.md](plan-cursor-agents-routing.md) | Routing | **Prompt only** | — |
| [plan-cursor-skills-routing.md](plan-cursor-skills-routing.md) | Routing | **Prompt only** | — |
| [plan-cursor-model-routing.md](plan-cursor-model-routing.md) | Routing | **Prompt only** | — |
| [plan-cursor-rules-audit.md](plan-cursor-rules-audit.md) | Routing | **Prompt only** | — |
| [plan-cursor-hooks.md](plan-cursor-hooks.md) | Hooks | **Partial** | P1–P2 |
| [plan-cursor-activity-logging.md](plan-cursor-activity-logging.md) | Hooks / observability | **Open** | P2 |
| [plan-python-remediation-overview.md](plan-python-remediation-overview.md) | Hub | **Done** | P0–P3 |
| [plan-python-remediation-foundation.md](plan-python-remediation-foundation.md) | Python / policy | **Done** | P0 |
| [plan-python-remediation-hook-policy.md](plan-python-remediation-hook-policy.md) | Python / policy | **Partial** | P1–P2 |
| [plan-python-remediation-sync-scripts.md](plan-python-remediation-sync-scripts.md) | Python / sync | **Done** | P2–P3 |

**Test signal:** `poetry run pytest templates/hooks/tests templates/commands/tests -q` → **173 passed** (2026-06-19).

---

## Routing prompts (prompt only)

These files are paste-into-Cursor templates. References they depend on exist in-repo.

| Plan | References verified | Notes |
|------|---------------------|-------|
| [plan-cursor-session-map.md](plan-cursor-session-map.md) | USAGE.md, SKILLS.md, RULES.md, HOOKS_USAGE.md, AGENTS_USAGE.md | Full route table for one task |
| [plan-cursor-agents-routing.md](plan-cursor-agents-routing.md) | agents/AGENTS.md, AGENTS_USAGE.md | `@agent(NAME)` picker |
| [plan-cursor-skills-routing.md](plan-cursor-skills-routing.md) | skills/SKILLS.md | Skill chain picker |
| [plan-cursor-model-routing.md](plan-cursor-model-routing.md) | route-task-to-model/SKILL.md, models-catalog.json | Model tier + slug |
| [plan-cursor-rules-audit.md](plan-cursor-rules-audit.md) | rules/RULES.md | Rules overlap for paths |

**Usage:** `@templates/prompts/plan-cursor-session-map.md` when stuck; use narrower prompts when you already know the layer (agent vs skill vs model).

---

## Hooks plans

### [plan-cursor-hooks.md](plan-cursor-hooks.md) — Partial

| Area | Status | Evidence |
|------|--------|----------|
| Core safety hooks (shell, read, edit, git, MCP, activity) | **Done** | `templates/hooks/windows/*.ps1`, `templates/hooks/hooks.json` |
| Policy engine hooks (DB, git, MCP classify) | **Done** | `validate-*-operations.ps1` → `hook_policy.py` |
| Resource / prompt logging hooks | **Done** | `log-resource-usage.ps1`, `log-prompt-context.ps1` |
| Template consistency validation | **Done** | `validate-template-consistency.ps1` |
| Planned log hooks (scan-logs-in-edit, block-log-edit-secrets, block-secret-in-write, audit-log-patterns) | **Open** | No matching scripts in `templates/hooks/` |
| `redact-logs-before-read` (*.log paths) | **Open** | `redact-sensitive-read.ps1` exists; `*.log` extension not confirmed |

### [plan-cursor-activity-logging.md](plan-cursor-activity-logging.md) — Open

| Acceptance item | Status | Evidence |
|-----------------|--------|----------|
| Normalize `event` (never null) | **Open** | `log-cursor-activity.ps1` sets `event` from payload only; no shape inference |
| Always log `conversation_id`, `generation_id` | **Partial** | Raw payload copy — present when Cursor sends them |
| `edit_count`, `edit_summary`, truncation policy | **Open** | Truncates at 50k chars; no structured `edit_summary` |
| Per-event normalized schema | **Open** | Still dumps raw payload + `ts` |
| Query script `query-cursor-logs.ps1` | **Open** | File does not exist |
| Session summary at `stop` | **Open** | Not implemented (plan recommends query script first) |

**Next:** Implement steps 1–5 from the plan in `templates/hooks/windows/log-cursor-activity.ps1`; add `templates/commands/query-cursor-logs.ps1`.

---

## Python remediation hub

### [plan-python-remediation-overview.md](plan-python-remediation-overview.md) — Done

Program-level acceptance (Python hooks + sync scope):

- [x] `requires-python = ">=3.10"` in `pyproject.toml`
- [x] `poetry run pytest templates/hooks/tests templates/commands/tests` passes
- [x] Policy stderr contract + MCP unification + sync dedup + sync tests
- [x] hook_policy tests cover main, force-push, overrides, heredoc, modes, Windows shlex

Does **not** cover [plan-cursor-activity-logging.md](plan-cursor-activity-logging.md) or planned log hooks in [plan-cursor-hooks.md](plan-cursor-hooks.md).

---

### [plan-python-remediation-foundation.md](plan-python-remediation-foundation.md) — Done

#### Item 1 — pyproject + pytest (P0)

| Criterion | Status |
|-----------|--------|
| `requires-python = ">=3.10"` | **Done** — `pyproject.toml` |
| pytest dev deps + `testpaths` / `pythonpath` | **Done** |
| README / HOOKS_USAGE / commands README → 3.10+ | **Done** |
| CI matrix (ubuntu + windows, 3.10–3.12) | **Done** — `.github/workflows/python-tests.yml` |

#### Item 2 — Fail-open policy + stderr (P0)

| Criterion | Status |
|-----------|--------|
| `_emit_log()` structured stderr | **Done** — `hook_policy.py` |
| Corrupt policy → allow + `policy_load_failed` | **Done** + tests |
| `policy_engine_error` / `policy_load_error` modes | **Done** — `default.policy.json`, `hook-policy.example.json` |
| Shell wrappers forward stderr | **Done** — `hook-common.ps1` (no `2>$null` on policy invoke) |
| Documented in policy README + HOOKS_USAGE | **Done** — `templates/hooks/policy/README.md` |

---

### [plan-python-remediation-hook-policy.md](plan-python-remediation-hook-policy.md) — Partial

#### Item 3 — MCP classification unify (P1) — Done

| Criterion | Status |
|-----------|--------|
| `mcp_classify.py` shared module | **Done** |
| `hook_policy.py` + `sync_mcp_policy.py` import it | **Done** |
| `global_write_name_pattern` in JSON | **Done** — `default.policy.json` |
| `test_mcp_classify.py` | **Done** |
| README documents single edit path | **Done** |

#### Item 4 — Expand hook_policy tests (P1) — Partial

| Criterion | Status |
|-----------|--------|
| `fixtures/` golden cases (8–12) | **Done** — 9 JSON fixtures |
| `FixtureFileTests` runs | **Done** |
| `test_hook_policy_main.py` (main, force-push, overrides, heredoc, modes) | **Done** |
| Windows shlex test | **Done** — `skipif` on non-NT |
| 40+ tests, 0 skips (except platform) | **Done** — 173 total suite; hook tests ~51 |
| `hook_policy.py` ≥ 85% line coverage | **Unverified** — `pytest-cov` not in dev deps |
| `fixtures/policies/` override JSON set | **Open** |
| `test_custom_deny_rule` | **Open** |
| Full pytest migration (drop unittest) | **Open** — dual runner retained |

#### Item 6 — `lru_cache` + real `log` mode (P2) — Done

| Criterion | Status |
|-----------|--------|
| `@lru_cache` on policy load + mtime key | **Done** |
| `clear_policy_cache()` for tests | **Done** — `conftest.py` |
| `log` mode emits `policy_would_ask` | **Done** + tests |

#### Security hardening — Partial

| Criterion | Status |
|-----------|--------|
| Corrupt JSON handling | **Done** (P0) |
| Narrow full-cmd SQL scan | **Done** — `_sql_carrier_segments` no longer appends full `cmd` |
| Tighten `delete_all_rows` regex (explicit WHERE exclusion) | **Open** — pattern unchanged; behavior correct via carrier rules + tests |
| Tiered exception handling | **Done** |

---

### [plan-python-remediation-sync-scripts.md](plan-python-remediation-sync-scripts.md) — Done

#### Item 5 — sync-cursor dedup (P2) — Done

| Criterion | Status |
|-----------|--------|
| `sync_templates_to_cursor` delegates to helpers | **Done** — `resolve_agents_source`, `sync_hooks_from_templates`, `sync_rules_dir`, etc. |
| Unified catalog sync | **Done** — `_sync_catalog_paths` (plan name: `_sync_docs_paths`) |
| `--dry-run`, `--verbose` | **Done** |
| Line-count reduction | **Done** — inline duplication removed |

**Note:** `sync-cursor.py` intentionally **does not** copy `templates/prompts/` to `.cursor/prompts/` (repo-only authoring). Tests assert `prompts/` absent after sync.

#### Item 7 — sync tests (P3) — Done

| Criterion | Status |
|-----------|--------|
| `test_sync_cursor.py` | **Done** |
| `test_sync_mcp_policy.py` | **Done** |
| `fixtures/minimal_templates/` | **Done** |
| Hermetic (mock home) | **Done** |
| dry-run / verbose tests | **Done** |

---

## Recommended next work (PM priority)

1. **P2 — Activity logging** — [plan-cursor-activity-logging.md](plan-cursor-activity-logging.md) steps 1–5
2. **P2 — Log hooks** — [plan-cursor-hooks.md](plan-cursor-hooks.md) planned log hooks table
3. **P3 — Test gaps** — `test_custom_deny_rule`, `fixtures/policies/`, add `pytest-cov` if 85% gate is required
4. **P3 — Policy regex** — align `delete_all_rows` pattern with plan spec (optional; behavior already tested)

---

## Validate locally

```powershell
poetry install --with dev
poetry run pytest templates/hooks/tests templates/commands/tests -q
poetry check
```

Re-run this index review after closing any plan above.
