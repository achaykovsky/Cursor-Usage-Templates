# Python Remediation: Sync Scripts

> **Historical plan (2026-02).** Implemented in `sync-cursor.py`. Current policy: **`templates/` only** as source; `ToGlobal` removed; `FromGlobal` writes `.cursor/` only; `sync-templates-to-local` hook on `afterFileEdit`. See [`commands/README.md`](../commands/README.md).

**Hub:** [Overview](plan-python-remediation-overview.md) | **Priority:** P2–P3

Plans for `sync-cursor.py` deduplication, structured logging, and test coverage for sync commands. **No code in this document.**

---

## Item 5 — Deduplicate sync-cursor.py

### Goal

Remove parallel implementations so `sync_templates_to_cursor()` delegates to existing helpers (`sync_agents_dir`, `sync_rules_dir`, `sync_hooks_tree`, `sync_skills_tree`, unified docs sync) — one code path per resource type, consistent behavior across four sync modes.

### Current duplication (ground truth)

| Concern | Dedicated helper | Reimplemented in `sync_templates_to_cursor()` |
|---------|------------------|-----------------------------------------------|
| Agents | `sync_agents_dir()` (lines 69–84) | Lines 351–358 — custom subagent source logic + copy loop |
| Rules | `sync_rules_dir()` (87–102) | Lines 360–370 |
| Hooks | `sync_hooks_tree()` (105–183) | Lines 372–392 — partial (no fallback/template logic) |
| Skills | `sync_skills_tree()` (226–246) | Lines 394–409 |
| Docs | `sync_docs_from_templates()` (259–280) | Called at end ✓ |
| Docs (global) | `sync_docs_tree()` (283–304) | Not used in TemplatesToLocal ✓ |

**Additional overlap:** `sync_docs_from_templates` vs `sync_docs_tree` — nearly identical except source root (`templates/` vs `.cursor/`).

### Files to touch

| File | Change |
|------|--------|
| `templates/commands/sync-cursor.py` | Refactor only |
| `templates/commands/tests/test_sync_cursor.py` | **New** (Item 7) — guards refactor |
| `templates/commands/README.md` | Note internal helper structure (optional) |

### Step-by-step implementation tasks

#### 5a — Unify docs sync

1. **Add `_sync_docs_paths(source_root: Path, dest_cursor: Path, *, prompts: bool = True) -> int`**
   - Parameterize `DOC_SYNC_PATHS` loop + optional prompts tree copy
   - `sync_docs_from_templates(templates_root, dest)` → `_sync_docs_paths(templates_root, dest)`
   - `sync_docs_tree(source, dest)` → `_sync_docs_paths(source, dest)`
2. Delete duplicated loops in both functions; keep thin wrappers for call-site clarity.

#### 5b — Extract agent source resolution

1. **Add `resolve_agents_source(project_root: Path, global_cursor: Path) -> Path | None`**
   - Move logic from `sync_templates_to_cursor` lines 342–349:
     - Prefer `templates/agents/subagents/*.md`
     - Else global `~/.cursor/agents/*.md`
2. **Add `sync_agents_from_source(source_dir: Path, dest_cursor: Path) -> int`**
   - Generalize `sync_agents_dir`: if source is not `source_cursor/agents`, copy flat `*.md` from given dir
   - Or: `sync_agents_dir` accepts optional `source_agents: Path | None`

#### 5c — Refactor `sync_templates_to_cursor`

Replace inline blocks with:

```python
agents_src = resolve_agents_source(project_root, global_cursor or Path.home() / ".cursor")
if agents_src:
    copied += sync_agents_from_source(agents_src, dest_cursor)

templates_cursor = project_root / "templates"
# Virtual .cursor-like layout OR call helpers with explicit paths:
copied += sync_rules_dir(templates_cursor, dest_cursor)  # requires rules under templates/rules
copied += sync_hooks_from_templates(project_root, dest_cursor, hooks_variant)  # new wrapper
copied += sync_skills_tree(project_root / "templates" / "skills", dest_cursor / "skills")
copied += sync_docs_from_templates(project_root / "templates", dest_cursor)
```

#### 5d — Hooks template path

`sync_hooks_tree` expects `source_cursor/hooks.json` + `hooks/scripts/`. Templates layout differs (`templates/hooks/hooks.json`, `windows|unix/`).

1. **Add `sync_hooks_from_templates(project_root, dest_cursor, hooks_variant) -> int`**
   - Build temp or logical source: reuse logic currently in lines 372–392
   - Long-term: align templates tree to mirror `.cursor/` so `sync_hooks_tree` works with `source_cursor = templates` stub — **prefer wrapper** to avoid layout migration
2. Wrapper calls:
   - `resolve_hooks_json_template`, `iter_template_hook_scripts`, `sync_hooks_policy`
   - Consider delegating script copy to shared function used by both `sync_hooks_tree` fallback and templates path

#### 5e — Verify four modes unchanged

| Mode | Entry | Expected helpers |
|------|-------|------------------|
| `TemplatesToLocal` | `sync_templates_to_cursor` | unified helpers |
| `TemplatesToGlobal` | same + `write_global_hooks_json` | same |
| `ToGlobal` | `sync_agents_dir`, `sync_rules_dir`, `sync_hooks_tree`, `sync_skills_tree`, `sync_docs_tree` | unchanged |
| `FromGlobal` | mirror of ToGlobal | unchanged |

Run manual diff: file list before/after refactor on sample project.

#### 5f — Optional CLI improvements (same PR or follow-up)

- `--dry-run` — print would-copy paths, no writes
- `--verbose` — log skips (missing dirs)

See logging section below.

### Acceptance criteria / test plan

- [ ] Item 7 tests pass for all four modes before/after refactor
- [ ] Line count of `sync_templates_to_cursor` reduced by ≥ 50%
- [ ] No duplicate `_clear_matching` + copy loops for rules/skills/agents
- [ ] Manual: `python templates/commands/sync-cursor.py` on this repo produces same `.cursor/` file set (compare checksums)

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| Subagent fallback order change | Tests lock precedence: templates subagents > global |
| Hooks template vs project layout | Dedicated wrapper; don't force layout change |
| **Rollback** | Git revert single refactor commit |

### Estimated effort

**M** (half day)

### Dependencies on other items

- **Depends on:** P0 pytest (for Item 7 tests — write tests first or in same PR TDD)
- **Blocks:** P3 sync tests (smaller surface after dedup)

---

## Item 7 — Add test_sync_cursor.py and test_sync_mcp_policy.py

### Goal

Automated coverage for sync commands and MCP policy sync script — zero coverage today.

### Files to touch

| File | Change |
|------|--------|
| `templates/commands/tests/test_sync_cursor.py` | **New** |
| `templates/commands/tests/test_sync_mcp_policy.py` | **New** |
| `templates/commands/tests/conftest.py` | **New** — `tmp_project`, `templates_tree` fixture |
| `templates/commands/tests/fixtures/minimal_templates/` | **New** — tiny templates tree |
| `pyproject.toml` | Ensure `testpaths` includes `templates/commands/tests` |

### Step-by-step implementation tasks

#### 7a — Fixture layout `minimal_templates/`

```
minimal_templates/
  agents/subagents/agent_a.md
  rules/rule_a.mdc
  hooks/hooks.json
  hooks/windows/script.ps1
  hooks/policy/default.policy.json
  skills/foo/SKILL.md
  USAGE.md
  prompts/plan-test.md
```

#### 7b — `test_sync_mcp_policy.py`

1. **Fixture mcps dir:**
   ```
   mcps/user-test/tools/get_item.json  {"name":"get_item"}
   mcps/user-test/tools/create_item.json
   mcps/user-test/tools/opaque.json  {"name":"opaque_xyz"}
   ```
2. `test_classify_via_shared_module` — after Item 3 unify
3. `test_dry_run_stdout_json` — run `sync_mcp_policy.main` via subprocess without `--write`
4. `test_write_merges_unknown_tools` — `--write` to tmp `mcp_tools.json`; assert `get_item` → read, `create_item` → write, opaque not added
5. `test_existing_tools_not_overwritten` — pre-seed catalog with custom risk

#### 7c — `test_sync_cursor.py`

Use `tmp_path` as project root; copy `minimal_templates` to `tmp_path/templates/`.

1. `test_templates_to_local_creates_cursor_tree`
   - Run `main(["--project-root", str(tmp_path)])`
   - Assert `.cursor/agents/agent_a.md`, `rules/`, `hooks/scripts/script.ps1`, `skills/foo/SKILL.md`, `USAGE.md`, `prompts/plan-test.md`
2. `test_templates_to_local_hooks_variant_unix` — `--hooks-variant unix` copies `.sh` if present in fixture
3. `test_to_global_and_from_global_roundtrip` — mock `Path.home()` to `tmp_path/home`; run ToGlobal then FromGlobal; compare file contents
4. `test_sync_skills_prunes_stale` — pre-create stale `SKILL.md`; sync; assert removed
5. `test_sync_agents_prefers_templates_subagents` — both templates and global have agents; assert templates win
6. `test_missing_templates_dirs_no_crash` — empty templates; exit 0, copied 0 or partial
7. `test_doc_sync_paths` — only `DOC_SYNC_PATHS` files copied

**Invocation pattern:**

```python
from sync_cursor import main
import sys
monkeypatch.setattr(sys, "argv", ["sync-cursor.py", "--project-root", str(tmp_path)])
assert main() == 0
```

Or subprocess with `PYTHONPATH=templates/commands`.

#### 7d — pytest vs unittest

- New files use pytest + `tmp_path` fixture
- Keep `test_hook_policy.py` unittest-compatible until migrated

#### 7e — Missing fixtures dir (hook tests)

Cross-link: create `templates/hooks/tests/fixtures/` per hook-policy plan Item 4a — separate from sync fixtures.

### Acceptance criteria / test plan

- [ ] `poetry run pytest templates/commands/tests -v` — all green
- [ ] Tests hermetic — no writes to real `~/.cursor` (mock home)
- [ ] Coverage: `sync-cursor.py` ≥ 70% line coverage
- [ ] `sync_mcp_policy.py` ≥ 80% coverage

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| Platform-specific hook suffix | Parametrize windows/unix fixtures |
| Global home pollution | Always monkeypatch `Path.home` |
| **Rollback** | Delete tests dir; no production impact |

### Estimated effort

**L** (1 day)

### Dependencies on other items

- **Depends on:** P0 pytest; Item 3 for MCP classify tests; Item 5 preferred before finalizing sync tests
- **Blocks:** None

---

## Logging — sync-cursor dry-run / verbose (cross-cutting)

### Goal

Observable sync operations for debugging template drift without diffing entire trees.

### Files to touch

| File | Change |
|------|--------|
| `templates/commands/sync-cursor.py` | `--dry-run`, `--verbose`; structured log helper |
| `templates/commands/README.md` | Document flags |

### Step-by-step implementation tasks

1. **Add `_log(level, event, **fields)`** — print JSON lines to stderr when `--verbose`; summary counts always to stdout
2. **`--dry-run`** — helpers return count but skip `shutil.copy2` / `unlink`; log `would_copy` events
3. **Refactor `_write_sync_line`** — respect dry-run: `DRY  agents/foo.md` vs `OK  agents/foo.md`
4. **Tests** — `test_dry_run_no_files_written`, `test_verbose_emits_stderr_json`

### Acceptance criteria

- [ ] Default behavior unchanged (no flags)
- [ ] `--dry-run` → `"Synced N files"` with N would-copy count, disk unchanged

### Estimated effort

**S** (2 hours) — can ship with Item 5

### Dependencies

Item 5 refactor (apply logging in unified helpers once)
