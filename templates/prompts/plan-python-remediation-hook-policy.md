# Python Remediation: Hook Policy Engine

**Hub:** [Overview](plan-python-remediation-overview.md) | **Priority:** P1–P2

Plans for MCP classification unification, expanded tests, caching, log mode, and security hardening in `hook_policy.py`. **No code in this document.**

---

## Item 3 — Unify MCP classification (eliminate drift)

### Goal

Single source of truth for MCP tool name heuristics so `sync_mcp_policy.classify_tool_name()` and `hook_policy._mcp_risk_from_catalog()` fallback prefixes cannot diverge from `default.policy.json` `mcp.global_*` keys.

### Current duplication

| Source | Location |
|--------|----------|
| `default.policy.json` | `mcp.global_read_prefixes`, `global_read_contains`, `global_write_prefixes`, `global_write_exact` |
| `sync_mcp_policy.py:18–32` | Hardcoded `classify_tool_name()` — mirrors prefixes + write regex |
| `hook_policy.py:393–405` | Reads JSON at runtime — correct for engine, not for sync script |

**Drift example:** Adding `archive_` as write prefix requires editing JSON + Python sync script; engine picks up JSON only.

### Files to touch

| File | Change |
|------|--------|
| `templates/hooks/policy/mcp_classify.py` | **New** — `classify_tool_name(name: str, rules: McpHeuristics) -> str` |
| `templates/hooks/policy/mcp_heuristics.py` or inline in above | Load heuristics from dict (policy fragment) |
| `templates/hooks/policy/hook_policy.py` | Import heuristics loader; use in `_mcp_risk_from_catalog` fallback path |
| `templates/hooks/policy/sync_mcp_policy.py` | Replace local `classify_tool_name` with import from `mcp_classify` |
| `templates/hooks/policy/default.policy.json` | Optional: add `mcp.global_write_contains` regex list (move from sync script line 30) |
| `templates/hooks/policy/README.md` | Document “edit JSON → both engine and sync use it” |
| `templates/hooks/tests/test_mcp_classify.py` | **New** — parametrize prefix/fragment cases |

### Step-by-step implementation tasks

1. **Extract `McpHeuristics` dataclass** (or TypedDict) with fields matching JSON:
   - `read_prefixes`, `read_contains`, `write_prefixes`, `write_exact`, `write_name_regex` (from sync script’s push/merge/close rule)
2. **Add `load_mcp_heuristics(policy: dict) -> McpHeuristics`**
   - Read `policy["mcp"]` with defaults matching current `default.policy.json`
3. **Implement `classify_tool_name(name, heuristics) -> Literal["read","write","unknown"]`**
   - Order: exact specials (`mcp_auth` → read) → read prefixes → read contains → write prefixes → write regex → unknown
   - Port regex from `sync_mcp_policy.py:30` into JSON as `global_write_name_pattern` OR keep in Python constant documented as “sync with JSON”
4. **Refactor `hook_policy._mcp_risk_from_catalog`**
   - After catalog lookup fails, call `classify_tool_name(tool, load_mcp_heuristics(policy))` instead of inline loops
5. **Refactor `sync_mcp_policy.main`**
   - Load `default.policy.json` (or `--policy-file` sibling) for heuristics when classifying new tools
   - Pass same heuristics to `classify_tool_name`
6. **Add drift test**
   - Load JSON heuristics; assert `classify_tool_name("list_releases") == "read"`, `create_foo` → write, unknown → unknown
   - Golden file: snapshot of prefixes exported from JSON (optional)
7. **Update `sync_mcp_policy.py --help`** — note dependency on policy JSON for heuristics

### Acceptance criteria / test plan

- [ ] Removing a prefix from JSON changes both engine fallback and sync script output (one edit).
- [ ] `test_mcp_classify.py` covers all prefixes in `default.policy.json` (smoke loop).
- [ ] Existing `test_hook_policy.py` MCP tests still pass.
- [ ] `python sync_mcp_policy.py --mcps-dir …` (dry run) unchanged output for known tools.

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| Import path when run as `__main__` | Keep scripts invokable; add `templates/hooks/policy` to pytest pythonpath |
| Circular imports | `mcp_classify.py` must not import `hook_policy` |
| **Rollback** | Revert new module; restore duplicated function in sync script |

### Estimated effort

**M** (half day)

### Dependencies on other items

- **Depends on:** P0 pyproject (pytest).
- **Blocks:** P3 `test_sync_mcp_policy.py` (test unified classifier).

---

## Item 4 — Expand hook_policy tests

### Goal

Cover untested paths: `main()`, force-push protection, policy override merge, SQL heredoc carriers, `advisory`/`off`/`log` modes, Windows `shlex`, and security edge cases. Add JSON fixtures directory referenced by existing `FixtureFileTests`.

### Files to touch

| File | Change |
|------|--------|
| `templates/hooks/tests/test_hook_policy.py` | Extend or migrate to pytest |
| `templates/hooks/tests/test_hook_policy_main.py` | **New** — CLI/integration via `subprocess` or `io.StringIO` |
| `templates/hooks/tests/conftest.py` | **New** — `policy_dir`, `tmp_policy_root`, `monkeypatch` for `HOOK_POLICY_LOG` |
| `templates/hooks/tests/fixtures/` | **New** — `shell-db-*.json`, `shell-git-*.json`, `mcp-*.json` |
| `templates/hooks/tests/fixtures/policies/` | Minimal override JSON for merge tests |

### Step-by-step implementation tasks

#### 4a — Fixtures directory

1. Create `templates/hooks/tests/fixtures/` with schema:
   ```json
   {"domain":"shell-db","payload":{"command":"…"},"permission":"ask","note":"optional"}
   ```
2. Add 8–12 golden cases: psql delete, drop db, alembic upgrade, git bad commit, force-push, unknown MCP, etc.
3. Enable `FixtureFileTests` (currently skips when dir missing).

#### 4b — `main()` and stdin/stdout contract

1. `test_main_empty_stdin_returns_allow` — subprocess `hook_policy.py shell-db` with empty stdin
2. `test_main_invalid_json_returns_allow` — malformed stdin; assert exit 0; assert stderr log after P0 Item 2
3. `test_main_valid_payload_roundtrip` — echo JSON pipe; stdout parseable; single line
4. `test_main_unknown_domain_returns_allow`

#### 4c — Force-push (`classify_shell_git`)

1. Use `unittest.mock.patch` on `subprocess.check_output`
2. `test_force_push_main_denied` — branch `main`, cmd `git push --force`, mock returns `main`
3. `test_force_push_with_lease_allowed` — `--force-with-lease` not denied
4. `test_force_push_feature_branch_allowed` — mock branch `feature/x`
5. `test_force_push_subprocess_failure_allows` — mock raises; document current behavior (allows push check skip)

#### 4d — Policy overrides (`load_policy`)

1. `tmp_path` project root with `.cursor/hook-policy.json`:
   ```json
   {"modes":{"db_shell":"off"}}
   ```
2. `test_project_override_db_shell_off` — destructive SQL still allowed
3. `test_deep_merge_modes` — partial override preserves other keys
4. `test_custom_deny_rule` — add deny pattern in override

#### 4e — Heredoc SQL carriers (`_sql_carrier_segments`)

1. `test_heredoc_psql_delete_asks`:
   ```
   psql <<EOF
   DELETE FROM users WHERE id=1
   EOF
   ```
2. `test_heredoc_delimiter_quoted` — `<<'SQL'` variant per regex in `hook_policy.py:160`
3. `test_no_carrier_grep_delete_allowed` — `grep delete` not DB context

#### 4f — Mode matrix

| Mode key | Test |
|----------|------|
| `db_shell: off` | write SQL → allow |
| `db_shell: log` | write SQL → allow + stderr audit (after P2 Item 6) |
| `git_commit_format: advisory` | bad commit → allow |
| `git_commit_unparsed: deny` | `git commit` without `-m` → deny |
| `mcp_unknown: off` | unknown tool → allow |
| `mcp_write: log` | create PR → allow + log |

Use injected policy dict (unit tests) rather than file for speed.

#### 4g — Windows shlex (`_parse_argv`)

1. `@pytest.mark.skipif(os.name != "nt")` / parametrize platform
2. `test_windows_cmd_exe_git_commit` — `git.exe commit -m "feat: x"`
3. Document: tests run on CI windows + linux matrix

#### 4h — Security regression tests

1. `test_corrupt_policy_json_fail_open` — invalid JSON in temp policy dir
2. `test_db_binary_argv0_full_cmd_scan_narrow` — **expected after fix:** `bash -c 'psql …'` should NOT scan full cmd when argv[0] is bash (documents desired behavior for Item security fix)
3. `test_delete_all_rows_with_where_asks_not_denies` — `DELETE FROM t WHERE id=1` → ask not deny (documents current gap)

#### 4i — pytest migration (optional same PR or follow-up)

1. Convert `unittest.TestCase` classes to plain functions or keep dual-runner
2. pytest collects both; prefer functions for new tests

### Acceptance criteria / test plan

- [ ] `poetry run pytest templates/hooks/tests -v` — 40+ tests, 0 skips except platform-specific
- [ ] Coverage report: `hook_policy.py` ≥ 85% line coverage (`pytest --cov=hook_policy`)
- [ ] Fixtures dir exists; `FixtureFileTests` runs ≥ 8 files
- [ ] Force-push tests mock subprocess (no real git repo required)

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| Flaky subprocess tests | Prefer importing `main()` with patched stdin |
| Windows CI unavailable | skipif with documented gap |
| **Rollback** | Keep original unittest file; delete new files |

### Estimated effort

**L** (1–1.5 days)

### Dependencies on other items

- **Depends on:** P0 pyproject; P0 fail-open logging (for stderr assertions).
- **Blocks:** P2 cache invalidation tests; security fixes validation.

---

## Item 6 (hook_policy portions) — `lru_cache` on `load_policy` + real `log` mode

### Goal

Avoid re-reading and re-parsing JSON on every hook invocation within a process; implement `log` mode as allow + structured audit (not silent no-op).

### Files to touch

| File | Change |
|------|--------|
| `templates/hooks/policy/hook_policy.py` | `@lru_cache` wrapper; `_policy_cache_key()`; `_emit_policy_decision()` |
| `templates/hooks/tests/test_hook_policy.py` | Cache + log mode tests |

### Step-by-step implementation tasks

#### 6a — Policy cache

1. **Define cache key** — tuple of:
   - `project_root` (str or None)
   - mtimes: for each file in `_policy_dirs` order: `default.policy.json`, `mcp_tools.json`, `hook-policy.json`, project `.cursor/hook-policy.json`
   - Use `0` mtime for missing files
2. **Replace `load_policy` body** with:
   ```python
   @lru_cache(maxsize=32)
   def _load_policy_cached(key: tuple) -> str:  # return json.dumps merged
   ```
   Or cache the dict with frozen key; provide `load_policy(project_root)` that builds key and returns deserialized dict.
3. **Add `clear_policy_cache()`** — for tests only; call in `conftest` autouse fixture
4. **Performance test (optional)** — call `classify()` 1000×; assert file reads ≤ number of policy files (mock `read_text`)

**Note:** CLI invokes fresh process per hook today — cache helps tests and future in-process use; document limited win for subprocess CLI unless hooks batch calls.

#### 6b — Real `log` mode

Current (`hook_policy.py:224–225`, `433–434`, `444–445`): `log` treated same as `allow` with no audit.

1. **Add `_resolve_mode_action(mode: str) -> Literal["allow","ask","deny","log"]`**
2. **When action would be `ask` and mode is `log`:**
   - Call `_emit_log("info", "policy_would_ask", rule_id=…, domain=…)
   - Return `_allow_shell()`
3. **Apply in:** `classify_shell_db` ask rules, `classify_mcp` unknown/write paths
4. **Do not log** deny rules (still deny) or readonly allows (noise)
5. **Tests:** `test_db_shell_log_mode_emits_would_ask`; capture stderr

### Acceptance criteria / test plan

- [ ] Mutating policy file mtime → next `load_policy` sees new rules (cache invalidation)
- [ ] `modes.db_shell: log` + DELETE → allow + stderr contains `policy_would_ask`
- [ ] Existing `ask` mode unchanged

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| Stale cache if file replaced same mtime | Document; optional env `HOOK_POLICY_CACHE=0` |
| Log volume | Only log would-ask/would-deny, not every allow |
| **Rollback** | Remove decorator; restore log→allow one-liner |

### Estimated effort

**M** (3–4 hours)

### Dependencies on other items

- **Depends on:** P0 `_emit_log`; P1 tests for log/cache.
- **Blocks:** None.

---

## Security hardening (hook_policy cross-cutting)

Consolidated tasks to schedule with Items 4 and 6.

### Goal

Close review findings without changing default deny/ask semantics for valid inputs.

### Files to touch

`hook_policy.py`, `default.policy.json`, tests

### Tasks

1. **Corrupt JSON** — covered in P0 Item 2 (`_load_json` try/except)
2. **Narrow full-cmd scan** (`hook_policy.py:164–165`)
   - Remove `segments.append(cmd)` blanket when binary in argv[0]
   - Instead: only append when no `-c`/heredoc AND stdin invocation (`psql` with no args) — document as ask-worthy
   - Alternative: scan argv tokens only except explicit carriers
3. **Tighten `delete_all_rows` deny pattern**
   - Change from `(?i)\bdelete\s+from\s+\w+\s*;?\s*$` to require no `WHERE` clause:
     `(?i)\bdelete\s+from\s+\w+(?!\\s+where\\b)[^;]*;?\\s*$`
   - Add test: `DELETE FROM users` → deny; `DELETE FROM users WHERE id=1` → ask (sql_delete rule)
4. **Exception handling tiering**
   - `JSONDecodeError` on stdin → allow + log (not ask)
   - `Exception` in classify → configurable ask (P0)

### Acceptance criteria

- [ ] `psql -c "SELECT 1"` still allow
- [ ] `bash -c "psql -c 'DROP DATABASE x'"` behavior documented and tested
- [ ] No silent swallow without stderr log

### Estimated effort

**M** (bundled with P0/P1)

### Dependencies

P0 fail-open logging; P1 tests
