# Planning prompts index

**Validated:** 2026-06-19 (analysis pass) | **Tests:** `211 passed` — `poetry run pytest templates/hooks/tests templates/commands/tests -q`

Paste prompts from this folder when routing is unclear. Open [USAGE.md](../USAGE.md) for the navigation hub.

**CLI alternatives:** `templates/commands/route-*.ps1`, `query-cursor-logs.ps1` (backed by `routing.py`, `cursor_activity.py`).

---

## Analysis summary

| Metric | Value |
|--------|-------|
| Plans tracked | **12** |
| **Done** | **9** (75%) |
| **Partial** | **3** (25%) |
| **Open** (within partial plans) | **8** acceptance items |

```
Done     ████████████████████████░░░  9/12 plans
Partial  ░░░░░░░░░░░░░░░░░░░░░░░███  3/12 plans
```

### At a glance

| Status | Plans |
|--------|-------|
| [x] **Done** | session-map, agents-routing, skills-routing, model-routing, rules-audit, python-remediation (overview, foundation, sync-scripts) |
| [~] **Partial** | cursor-hooks, cursor-activity-logging, python-remediation-hook-policy |
| [x] **Done** | plan-ai-infrastructure (templates shipped) |
| [ ] **Open** | *(no plan fully untouched)* |

---

## Status legend

| Mark | Meaning |
|------|---------|
| **[x] Done** | Acceptance criteria met; evidence in repo |
| **[~] Partial** | Core shipped; listed gaps remain |
| **[ ] Open** | Not started or not found in repo |
| **Prompt + CLI** | Markdown prompt plus deterministic CLI companion |

---

## Summary table

| Plan | Type | Status | Evidence |
|------|------|--------|----------|
| [plan-cursor-session-map.md](plan-cursor-session-map.md) | Routing | **[x] Done** | `route-session.ps1` → `routing.py session` |
| [plan-cursor-agents-routing.md](plan-cursor-agents-routing.md) | Routing | **[x] Done** | `route-agent.ps1` → `routing.py agent` |
| [plan-cursor-skills-routing.md](plan-cursor-skills-routing.md) | Routing | **[x] Done** | `route-skill.ps1` → `routing.py skill` |
| [plan-cursor-model-routing.md](plan-cursor-model-routing.md) | Routing | **[x] Done** | `route-model.ps1` → `models-catalog.json` |
| [plan-cursor-rules-audit.md](plan-cursor-rules-audit.md) | Routing | **[x] Done** | `route-rules.ps1` → `RULES.md` globs |
| [plan-cursor-hooks.md](plan-cursor-hooks.md) | Hooks | **[~] Partial** | 17 scripts; `audit-log-patterns` still open |
| [plan-cursor-activity-logging.md](plan-cursor-activity-logging.md) | Observability | **[~] Partial** | Steps 1–5 + prompt redaction done; stop summary optional |
| [plan-python-remediation-overview.md](plan-python-remediation-overview.md) | Hub | **[x] Done** | P0–P3 Python scope complete |
| [plan-python-remediation-foundation.md](plan-python-remediation-foundation.md) | Python | **[x] Done** | pyproject, CI, fail-open stderr |
| [plan-python-remediation-hook-policy.md](plan-python-remediation-hook-policy.md) | Python | **[~] Partial** | MCP/cache/log done; test/coverage gaps |
| [plan-python-remediation-sync-scripts.md](plan-python-remediation-sync-scripts.md) | Python | **[x] Done** | Dedup, dry-run, sync tests |
| [plan-ai-infrastructure.md](plan-ai-infrastructure.md) | AI platform | **[x] Done** | `ai-runtime/`, `ai-infra-workflows/`, `rag-workflows/`, `langchain-workflows/`, 5 subagents, AI validation hooks; RAG track complete |

---

## Routing — [x] Done (5/5)

Prompt + CLI deliverables complete. Tests: `test_routing.py` (6 cases).

| Plan | CLI | Python | Tests |
|------|-----|--------|-------|
| Session map | `route-session.ps1` | `routing.py session` | [x] |
| Agents | `route-agent.ps1` | `routing.py agent` | [x] |
| Skills | `route-skill.ps1` | `routing.py skill` | [x] |
| Model | `route-model.ps1` | `routing.py model` | [x] |
| Rules audit | `route-rules.ps1` | `routing.py rules` | [x] |

**Usage:** `.\templates\commands\route-session.ps1 -Task "fix auth bug"` — or paste the prompt when you need LLM judgment beyond keyword heuristics.

---

## Hooks — [~] Partial

### [plan-cursor-hooks.md](plan-cursor-hooks.md)

| Item | Status | Evidence |
|------|--------|----------|
| `block-destructive-shell` | [x] | `windows/block-destructive-shell.ps1`, `unix/*.sh` |
| `redact-sensitive-read` | [x] | `redact-sensitive-read.ps1` / `.sh` |
| `format-after-edit` | [x] | `format-after-edit.ps1` / `.sh` |
| `suggest-commit-on-stop` | [x] | `suggest-commit-on-stop.ps1` / `.sh` |
| `validate-git-commands` | [x] | `validate-git-commands.ps1` / `.sh` |
| `validate-pre-push` | [x] | `validate-pre-push.ps1` / `.sh` |
| `validate-db-shell-operations` | [x] | → `hook_policy.py` |
| `validate-mcp-operations` | [x] | → `hook_policy.py` |
| `log-cursor-activity` | [x] | → `cursor_activity.py normalize` |
| `log-resource-usage` / `log-prompt-context` | [x] | `log-resource-usage.ps1`, `log-prompt-context.ps1` |
| `validate-template-consistency` | [x] | `validate-template-consistency.ps1` / `.sh` |
| `scan-logs-in-edit` | [x] | `scan-logs-in-edit.ps1` / `.sh` |
| `block-log-edit-secrets` | [x] | Covered by `scan-logs-in-edit` (advisory) |
| `block-secret-in-write` (preToolUse) | [x] | `block-secret-in-write.ps1` / `.sh` |
| `validate-bot-manifest` | [x] | `validate-bot-manifest.ps1` / `.sh` |
| `validate-ai-policy-schema` | [x] | `validate-ai-policy-schema.ps1` / `.sh` |
| `validate-rag-artifacts` | [x] | `validate-rag-artifacts.ps1` / `.sh` |
| `audit-log-patterns` (stop) | [ ] | No script |
| `redact-logs-before-read` (*.log) | [x] | `redact_sensitive.py` `is_log_path` |

**Plan status:** core table **done**; planned log-hooks section **open** (5 items).

---

### [plan-cursor-activity-logging.md](plan-cursor-activity-logging.md)

| Step | Status | Evidence |
|------|--------|----------|
| 1. Normalize `event` (never null) | [x] | `cursor_activity.infer_event()` |
| 2. Log `conversation_id`, `generation_id` | [x] | `normalize_activity_entry()` |
| 3. `edit_count`, `edit_summary`, truncation | [x] | `build_edit_summary()`, 2KB `edits_full` cap |
| 4. Per-event schema (not raw dump) | [x] | `normalize_activity_entry()` per event type |
| 5. Query script | [x] | `query-cursor-logs.ps1` + `cursor_activity.py query` |
| 6. Session summary at `stop` | [ ] | Optional per plan; query covers grouping |
| Prompt secret redaction | [x] | `log-prompt-context` + `redact_sensitive.redact_text` |

**Tests:** `test_cursor_activity.py` (6 cases). **Hooks:** `log-cursor-activity.ps1` / `.sh` wired via `Get-CursorActivityScript`.

**Plan status:** steps 1–5 **[x] Done**; step 6 + prompt redaction **[ ] / [~]**.

---

## Python remediation

### [plan-python-remediation-overview.md](plan-python-remediation-overview.md) — [x] Done

- [x] `requires-python = ">=3.10"` (`pyproject.toml`)
- [x] `poetry run pytest templates/hooks/tests templates/commands/tests` — 211 passed
- [x] Policy stderr + MCP unify + sync dedup + sync tests
- [x] hook_policy: main, force-push, overrides, heredoc, modes, Windows shlex

*Scope excludes planned log hooks in [plan-cursor-hooks.md](plan-cursor-hooks.md).*

---

### [plan-python-remediation-foundation.md](plan-python-remediation-foundation.md) — [x] Done

| Item | Criterion | Status |
|------|-----------|--------|
| **P0-1** | pyproject + pytest + CI | [x] `.github/workflows/python-tests.yml` |
| **P0-1** | Docs → Python 3.10+ | [x] README, HOOKS_USAGE, commands README |
| **P0-2** | `_emit_log()` stderr | [x] `hook_policy.py` |
| **P0-2** | `policy_load_error` / `policy_engine_error` modes | [x] `hook-policy.example.json` |
| **P0-2** | Shell wrappers forward stderr | [x] `hook-common.ps1` (no `2>$null` on policy) |
| **P0-2** | Documented fail-open contract | [x] `hooks/policy/README.md` |

---

### [plan-python-remediation-hook-policy.md](plan-python-remediation-hook-policy.md) — [~] Partial

| Item | Criterion | Status |
|------|-----------|--------|
| **P1-3** MCP unify | `mcp_classify.py` shared | [x] |
| **P1-3** | Engine + sync import | [x] `hook_policy.py`, `sync_mcp_policy.py` |
| **P1-3** | `test_mcp_classify.py` | [x] 7 tests |
| **P1-4** Fixtures (8–12) | [x] 9 JSON in `hooks/tests/fixtures/` |
| **P1-4** `test_hook_policy_main.py` | [x] 23 tests |
| **P1-4** `test_hook_policy.py` | [x] 21 tests + FixtureFileTests |
| **P1-4** 40+ hook tests | [x] ~51 hook tests total |
| **P1-4** `hook_policy.py` ≥ 85% coverage | [ ] `pytest-cov` not in dev deps |
| **P1-4** `fixtures/policies/` | [ ] |
| **P1-4** `test_custom_deny_rule` | [ ] |
| **P1-4** Full pytest migration | [ ] unittest + pytest dual |
| **P2-6** `lru_cache` + `clear_policy_cache` | [x] |
| **P2-6** Real `log` mode (`policy_would_ask`) | [x] |
| **Security** corrupt JSON | [x] P0 |
| **Security** narrow SQL scan | [x] `_sql_carrier_segments` |
| **Security** `delete_all_rows` regex (WHERE) | [~] behavior correct; regex not plan-spec |
| **Security** tiered exceptions | [x] |

---

### [plan-python-remediation-sync-scripts.md](plan-python-remediation-sync-scripts.md) — [x] Done

| Item | Criterion | Status |
|------|-----------|--------|
| **P2-5** Dedup `sync_templates_to_cursor` | [x] helpers: `resolve_agents_source`, `sync_hooks_from_templates`, `_sync_catalog_paths` |
| **P2-5** `--dry-run`, `--verbose` | [x] |
| **P3-7** `test_sync_cursor.py` | [x] 17+ tests (incl. `FromGlobal`, `--trigger-file`, no global agent fallback) |
| **P3-7** `test_sync_mcp_policy.py` | [x] 4 tests |
| **P3-7** Hermetic fixtures | [x] `minimal_templates/` |

**Note:** `sync-cursor.py` does **not** copy `templates/prompts/` → `.cursor/prompts/` (repo-only authoring). **`templates/` is the only sync source** — nothing is copied from project `.cursor/`. Modes: `TemplatesToLocal`, `TemplatesToGlobal`, `FromGlobal` (no `ToGlobal`).

---

## Open work (prioritized)

| Priority | Plan | Open items |
|----------|------|------------|
| P3 | [plan-python-remediation-hook-policy.md](plan-python-remediation-hook-policy.md) | `fixtures/policies/`, `test_custom_deny_rule`, pytest-cov gate, unittest migration |
| P3 | hook-policy | Optional: align `delete_all_rows` regex with plan spec |
| P3 | [plan-cursor-hooks.md](plan-cursor-hooks.md) | `audit-log-patterns` stop hook (optional) |

---

## Validate locally

```powershell
poetry install --with dev
poetry run pytest templates/hooks/tests templates/commands/tests -q
poetry check
```

**Example routing:**

```powershell
.\templates\commands\route-session.ps1 -Task "Add API endpoint for users"
.\templates\commands\query-cursor-logs.ps1 -Date 2026-06-19
```

Re-run analysis and update this index after closing any `[ ]` item above.
