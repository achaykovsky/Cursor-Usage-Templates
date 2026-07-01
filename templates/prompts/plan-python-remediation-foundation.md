# Python Remediation: P0 Foundation

**Hub:** [Overview](plan-python-remediation-overview.md) | **Priority:** P0

Plans for tooling baseline and fail-open vs fail-closed policy behavior. **No code in this document.**

---

## Item 1 — Align `requires-python` and add pytest dev deps

### Goal

Make the repo’s declared Python floor match actual source (3.10+ syntax in `hook_policy.py`, `sync-cursor.py`) and add a reproducible pytest dev environment so hook/sync tests can run in CI and locally via Poetry.

### Files to touch

| File | Change |
|------|--------|
| `pyproject.toml` | `requires-python = ">=3.10"`; `[tool.poetry.group.dev.dependencies]` or `[project.optional-dependencies] dev` with pytest |
| `README.md` | Replace “Python 3.7+” with “Python 3.10+” (lines ~25, hooks section) |
| `templates/hooks/HOOKS_USAGE.md` | Update policy engine Python requirement |
| `templates/commands/README.md` | Note pytest dev install for contributors |
| `.github/workflows/*.yml` (if present) or document manual CI | Add `poetry install --with dev && poetry run pytest …` |
| `templates/prompts/plan-python-remediation-overview.md` | Mark item complete when done |

Optional (recommended):

| File | Change |
|------|--------|
| `pyproject.toml` | `[tool.pytest.ini_options]` — `testpaths`, `pythonpath` for `templates/hooks/policy` import |
| `templates/hooks/tests/conftest.py` | Shared fixtures (created in P1 test plan; stub path here) |

### Step-by-step implementation tasks

1. **Audit syntax usage** — Confirm all four Python files use 3.10+ only (`X | Y`, `list[str]`, etc.). No 3.9 backport needed if floor is 3.10.
2. **Update `pyproject.toml`**
   - Set `requires-python = ">=3.10"`.
   - Add dev dependency group:
     ```toml
     [tool.poetry.group.dev.dependencies]
     pytest = "^8.0"
     ```
   - If project uses PEP 621 only (no Poetry deps table yet), add:
     ```toml
     [project.optional-dependencies]
     dev = ["pytest>=8.0"]
     ```
3. **Configure pytest** — Add to `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["templates/hooks/tests", "templates/commands/tests"]
   pythonpath = ["templates/hooks/policy"]
   ```
4. **Verify locally**
   - `poetry install --with dev`
   - `poetry run pytest templates/hooks/tests/test_hook_policy.py -q`
5. **Update docs** — README, HOOKS_USAGE, commands README: Python 3.10+, `poetry run pytest` for contributors.
6. **CI** — Add or extend workflow to run pytest on push/PR (matrix: windows-latest + ubuntu-latest, Python 3.10–3.12).

### Acceptance criteria / test plan

- [ ] `poetry check` succeeds.
- [ ] `python --version` 3.9 fails `poetry install` or pip resolution with clear message.
- [ ] `poetry run pytest templates/hooks/tests -q` runs existing unittest module (pytest collects `unittest.TestCase` subclasses).
- [ ] Docs no longer mention Python 3.7.

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| Contributors on 3.9 | Document upgrade; hooks already use 3.10 syntax |
| Poetry vs pip-only users | Document `pip install -e ".[dev]"` alternative |
| **Rollback** | Revert `pyproject.toml` and doc lines; tests still runnable via `python -m unittest` |

### Estimated effort

**S** (1–2 hours)

### Dependencies on other items

- **Blocks:** P1 hook_policy tests, P3 sync tests, pytest migration.
- **Depends on:** None.

---

## Item 2 — Fail-open vs fail-closed policy: decide approach; log + ask on policy errors

### Goal

Resolve the intentional fail-open design (documented in `hook_policy.py` module docstring and `hook-common.ps1` / `hook-common.sh`) with explicit product rules: when the policy engine fails, operators and auditors must see **structured evidence** on stderr; default remains **allow** (fail-open) unless project opts into stricter modes.

### Current behavior (ground truth)

| Location | Behavior |
|----------|----------|
| `hook_policy.py:466–486` `main()` | Invalid stdin JSON → allow; any `Exception` in `classify()` → allow; exit 0 always |
| `hook_policy.py:57–60` `_load_json()` | Missing file → `{}`; corrupt JSON → `json.loads` raises → caught by `main()` → allow |
| `hook-common.ps1:210–227` `Invoke-HookPolicy` | No Python / no script / empty stdout / JSON parse error → allow; stderr discarded (`2>$null`) |
| `hook-common.sh:48–60` `invoke_hook_policy` | Same fail-open pattern |

**Review finding:** Fail-open on all errors is consistent with “hooks must not block the agent on infrastructure failure,” but **silent** failure hides misconfiguration and corrupt policy files.

### Recommended decision (for plan)

| Error class | Stdout (hook response) | Stderr (audit) | Configurable? |
|-------------|------------------------|----------------|---------------|
| Invalid hook payload JSON | `allow` | `WARN` structured event | No |
| Corrupt / unreadable policy file | `allow` | `ERROR` with path + exception type | Yes → `modes.policy_load_error: ask\|deny` |
| Classifier bug (`Exception`) | `allow` (default) | `ERROR` with domain + exception | Yes → `modes.policy_engine_error: ask` |
| Missing Python / script (shell wrapper) | `allow` | Already none — add wrapper log to activity JSONL optional | Future |

**Minimum viable (P0):** Keep fail-open stdout; add **structured JSON lines on stderr** from `hook_policy.py`; stop suppressing stderr in shell wrappers (or tee to `logs/hook-policy-errors.jsonl`).

### Files to touch

| File | Change |
|------|--------|
| `templates/hooks/policy/hook_policy.py` | `_log_event()`, wrap `_load_json`, `load_policy`, `main()` exception paths |
| `templates/hooks/policy/default.policy.json` | Optional `modes.policy_load_error`, `modes.policy_engine_error` (default `allow`) |
| `templates/hooks/windows/hook-common.ps1` | Stop `2>$null`; optionally forward stderr to host |
| `templates/hooks/unix/hook-common.sh` | Same |
| `templates/hooks/policy/README.md` | Document fail-open contract + stderr schema |
| `templates/hooks/HOOKS_USAGE.md` | Troubleshooting: “policy errors → check stderr / logs” |
| `templates/hooks/tests/test_hook_policy.py` | Error-path tests (detailed cases in hook-policy plan) |

### Step-by-step implementation tasks

1. **ADR-style decision note** (in policy README, not separate ADR file unless requested)
   - Rationale: Cursor hooks must not brick sessions when Python missing.
   - Tradeoff: fail-closed `deny` available via `hook-policy.json` for regulated projects.
2. **Define stderr schema** (one JSON object per line):
   ```json
   {"level":"error","component":"hook_policy","event":"policy_load_failed","path":"…","error_type":"JSONDecodeError","domain":"shell-db"}
   ```
   Fields: `timestamp` (ISO8601), `level`, `component`, `event`, optional `path`, `domain`, `error_type`, `message` (no secrets, no full command bodies).
3. **Implement `_emit_log(level, event, **fields)`** in `hook_policy.py` — write to `sys.stderr`, never stdout (stdout is hook JSON only).
4. **Harden `_load_json(path)`**
   - try/except `JSONDecodeError`, `OSError`
   - log event; return `{}` for that file (partial merge continues)
   - if **all** policy sources fail and merged policy empty → log `policy_empty`
5. **Wrap `classify()` errors in `main()`**
   - Log `policy_engine_error` with `domain`
   - Read `modes.policy_engine_error` from merged policy (default `allow`)
   - If `ask`: return `_ask_shell("Policy engine error…", "…")` instead of silent allow
6. **Shell wrapper changes**
   - PowerShell: remove `2>$null` from `Invoke-HookPolicy`; document that stderr is visible in Cursor hook debug
   - Bash: allow stderr through (already default)
7. **Document override** — Example in `templates/hook-policy.example.json` (create if missing):
   ```json
   "modes": {
     "policy_load_error": "ask",
     "policy_engine_error": "allow"
   }
   ```
8. **Tests** — See [hook-policy plan](plan-python-remediation-hook-policy.md) Item 4: `test_main_invalid_json_emits_log`, `test_corrupt_policy_file_fail_open_with_stderr`.

### Acceptance criteria / test plan

- [ ] Valid classification unchanged for happy paths.
- [ ] Corrupt `default.policy.json` → stdout still valid allow JSON; stderr contains `policy_load_failed`.
- [ ] With `policy_engine_error: ask`, forced exception in classifier → stdout `permission: ask`.
- [ ] Shell wrappers no longer discard Python stderr.
- [ ] HOOKS_USAGE documents fail-open + how to tighten.

### Risks & rollback

| Risk | Mitigation |
|------|------------|
| stderr noise in Cursor UI | Use ERROR only for true failures; WARN for recoverable |
| Breaking users expecting silent allow | Default modes unchanged (`allow`) |
| **Rollback** | Revert logging + wrapper stderr change; keep fail-open stdout |

### Estimated effort

**M** (half day)

### Dependencies on other items

- **Depends on:** Item 1 (pytest for error-path tests).
- **Blocks:** P2 real `log` mode (needs `_emit_log` infrastructure); P1 test suite error cases.
