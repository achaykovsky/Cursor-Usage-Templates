# Cursor Prompt: Plan Cursor Hooks for a Codebase

Use this prompt in Cursor Chat or Composer to generate a structured implementation plan for Cursor Hooks. Works for any codebase—Cursor analyzes the project and proposes hooks accordingly.

**Usage:** Paste this entire document into Cursor Chat or Composer. Cursor will analyze the repo and output a structured plan—no hook code, only specifications.

**Reference:** [Cursor Third-Party Hooks](https://cursor.com/docs/agent/third-party-hooks) | Hooks config: `.cursor/hooks.json` (project) or `~/.cursor/hooks.json` (user)

---

## Implemented Hooks (Scripts)

This repo includes `templates/hooks/` with ready-to-use scripts. Run `.\templates\commands\sync-cursor.ps1` to copy to `.cursor/`. Scripts live in `templates/hooks/scripts/` → `.cursor/hooks/scripts/`.

| Hook | Script | Skill mapping | Purpose |
|------|--------|---------------|---------|
| `beforeShellExecution` | `block-destructive-shell.ps1` | `suggest-commands-dont-run-destructive` | Block `rm -rf /`, `git push --force`, `DROP TABLE`, etc. |
| `beforeReadFile` | `redact-sensitive-read.ps1` | `redact-sensitive-in-output` | Redact `.env`, `*.pem`, credentials before passing to model. |
| `afterFileEdit` | `format-after-edit.ps1` | (code quality) | Run black/prettier/gofmt on edited file—saves tokens. |
| `stop` | `suggest-commit-on-stop.ps1` | `prepare-atomic-commit` | Output git status/diff and suggested commit groups; user runs skill for full analysis. |
| `beforeShellExecution` | `validate-git-commands.ps1` | `prepare-atomic-commit` | Validate commit message (conventional); deny force-push on main/master. |
| `beforeShellExecution` | `validate-pre-push.ps1` | `validate-pre-deploy` | Run pytest/npm test before push if configured. |
| `beforeSubmitPrompt`, `beforeShellExecution`, `afterFileEdit`, `stop` | `log-cursor-activity.ps1` | — | Log prompts, commands, edits, session end to `project/.cursor/logs/cursor-activity-YYYY-MM-DD.jsonl` (JSONL). Never writes to `~/.cursor`. |

**Note:** Hooks do not receive LLM responses—only user prompts, edits, commands, and session status. Logs may contain sensitive data; `.cursor/` is gitignored.

**Dependencies:** `pwsh`, `black`/`prettier`/`gofmt` (optional, for format-after-edit).

---

## Planned Hooks: Git and Logs

Specifications for hooks to implement. Scripts save tokens; skills apply when agent reasoning is needed.

### Git Hooks (implemented)

| Name | Trigger | Script | Status |
|------|---------|--------|--------|
| **validate-git-commit** | `beforeShellExecution` | `validate-git-commands.ps1` | Enforces length (≤72), conventional format. Create `.cursor/allow-non-conventional-commit` to skip. |
| **warn-force-push** | `beforeShellExecution` | `validate-git-commands.ps1` | Denies `git push --force` on main/master; allows `--force-with-lease`. |
| **suggest-commit-split** | `stop` | `suggest-commit-on-stop.ps1` | Groups changed files by type (feat/docs/test/chore); suggests commit split. |
| **block-git-reset-hard** | `beforeShellExecution` | `block-destructive-shell.ps1` | Blocks `git reset --hard origin`. |
| **validate-pre-push** | `beforeShellExecution` | `validate-pre-push.ps1` | Runs `pytest` or `npm test` before push if pyproject.toml/package.json present. |

### Log Hooks

| Name | Trigger | Purpose | Inputs | Actions | Script / Skill |
|------|---------|---------|--------|---------|----------------|
| **scan-logs-in-edit** | `afterFileEdit` | After editing code, scan for secrets/PII in log statements | file_path, edits (old_string, new_string) | Grep for `log.`, `print(`, `console.log`, etc.; check for password/token/email patterns; write report to temp file or Hooks channel | Script: regex on new_string |
| **redact-logs-before-read** | `beforeReadFile` | When reading log files (e.g. `*.log`), redact before passing to model | content, file_path | If path matches `*.log`, redact secrets/PII patterns | Script: extend redact-sensitive-read |
| **block-log-edit-secrets** | `afterFileEdit` | Warn when edit introduces obvious secret-in-log (e.g. `log.info(password)`) | file_path, edits | Parse new_string; write warning to Hooks channel (edit already applied) | Script: high-precision regex |
| **block-secret-in-write** | `preToolUse` (Write) | Block Write/Edit if content contains `log.*(password|token|secret)` etc. | tool_input (content) | Deny with userMessage; edit never applied | Script: regex on content |
| **audit-log-patterns** | `stop` | Session summary: list files touched that contain log calls; suggest `sensitive-data-handling` review | workspace_roots, generation_id | Scan edited files from session for log usage; output checklist | Script: lightweight; skill: `sensitive-data-handling`, `audit-config-and-secrets` |

### Implementation Notes

- **Git**: `validate-git-commit` and `warn-force-push` are script-first (deterministic). `suggest-commit-split` can enhance existing `suggest-commit-on-stop.ps1` with commit-grouping heuristics.
- **Logs**: `scan-logs-in-edit` and `block-log-edit-secrets` run on `afterFileEdit` (informational—edit already applied). They write warnings to Hooks channel. To block before write: use `preToolUse` with Write matcher to scan content and deny. `redact-logs-before-read` extends `redact-sensitive-read.ps1` for `*.log` paths.
- **Skills**: When scripts flag issues, the plan should reference `prepare-atomic-commit`, `redact-sensitive-in-output`, `sensitive-data-handling`, `audit-config-and-secrets`.

### Rollout Order

1. **Git**: Extend `block-destructive-shell.ps1` with `validate-git-commit` logic (or separate script). Add `warn-force-push`.
2. **Logs**: Extend `redact-sensitive-read.ps1` for `*.log`. Add `scan-logs-in-edit.ps1` (afterFileEdit).
3. **Optional**: `validate-pre-push`, `audit-log-patterns` (stop).

---

## Instructions for Cursor

Analyze the repository and produce a **Cursor Hooks implementation plan**. Do not generate hook implementation code—focus on planning, clarity, and practical automation value.

### Phase 1: Analysis

1. **Project structure**
   - Map directories, key files, entry points, and config locations.
   - Identify package manifests, build configs, and any automation scripts.
   - If present: list skills in `.cursor/skills/` (each `SKILL.md` has `name` and `description` in frontmatter).

2. **Tech stack**
   - Primary languages, frameworks, and tooling (package manager, linter, formatter, test runner).
   - Build, test, and deploy workflows.

3. **Developer workflows**
   - Common actions: feature work, refactors, PRs, releases, config changes.
   - Infer from README, docs, and project conventions.

4. **Leverage points**
   - Where would hooks provide the most value? Consider: file creation, refactors, feature scaffolding, cleanup, validation, testing, PR preparation.

### Phase 2: Hook Proposals

Propose a clear set of Cursor Hooks. For each hook, define:

| Field | Description |
|-------|-------------|
| **Name** | Short, descriptive identifier |
| **Trigger** | Cursor lifecycle event: `beforeSubmitPrompt`, `beforeReadFile`, `beforeShellExecution`, `beforeMCPExecution`, `afterFileEdit`, `preToolUse`, `postToolUse`, `stop`, `sessionStart`, `sessionEnd`, `subagentStop`, `preCompact` |
| **Scope** | Files, folders, or contexts (e.g. globs, tool matchers) |
| **Purpose** | One-sentence goal |
| **Inputs** | What the hook receives (e.g. file path, command, prompt) |
| **Actions** | What it does (allow/deny, modify, run side effect) |
| **Output** | JSON schema or format the hook must produce |
| **Safety constraints** | What it must NOT modify, assume, or block |
| **Skills** | Agent skills to invoke when this hook runs (see Skill Mapping below) |

### Phase 2b: Skill Mapping

If the project has Cursor skills in `.cursor/skills/`, map them to hooks. When a hook triggers, the implementation can invoke or inject the corresponding skill (e.g. via prompt-based hooks). Use this mapping as a reference—adapt to the skills present in the repo.

| Hook trigger / context | Skill(s) to invoke |
|------------------------|-------------------|
| **afterFileEdit** (code files) | `add-tests-for-change`, `security-scan-changes`, `keep-docs-in-sync-with-code` |
| **afterFileEdit** (new module/package) | `review-architecture-fit` |
| **afterFileEdit** (refactor/rename) | `refactor-safely`, `handle-breaking-change` |
| **stop** / **sessionEnd** | `prepare-atomic-commit`, `redact-sensitive-in-output` |
| **beforeShellExecution** | `suggest-commands-dont-run-destructive` (inform block/warn logic) |
| **postToolUse** (Write/Edit on config) | `audit-config-and-secrets` |
| **beforeSubmitPrompt** (feature/design keywords) | `design-feature-from-requirements` |
| **beforeSubmitPrompt** (onboarding/explain) | `explain-codebase-structure` |
| **beforeSubmitPrompt** (bug/error in prompt) | `reproduce-and-document-failure`, `fix-bug-systematically` |
| **beforeSubmitPrompt** (API/spec keywords) | `validate-api-contract`, `implement-or-extend-api-surface` |
| **beforeSubmitPrompt** (API evolution / breaking change) | `check-api-backward-compatibility`, `review-openapi-diff`, `manage-request-response-schema-changes`, `api-versioning-guidance`, `analyze-api-consumer-impact`, `handle-breaking-change` |
| **beforeSubmitPrompt** (migration keywords) | `plan-and-execute-migration`, `handle-breaking-change` |
| **beforeSubmitPrompt** (release/deploy) | `prepare-release`, `validate-pre-deploy` |
| **beforeSubmitPrompt** (cleanup/audit) | `audit-codebase-cleanup` |
| **beforeSubmitPrompt** (security review) | `security-scan-changes`, `sensitive-data-handling` |
| **beforeSubmitPrompt** (performance) | `investigate-performance-issue`, `add-observability-for-debugging` |
| **beforeSubmitPrompt** (git history) | `explain-and-navigate-git-history` |
| **beforeSubmitPrompt** (deps/upgrade) | `assess-and-update-dependencies` |
| **beforeSubmitPrompt** (PR/staged/diff) | `review-pull-request` |
| **beforeSubmitPrompt** (design decision/ADR) | `write-or-update-adr` |
| **beforeSubmitPrompt** (setup/onboard) | `reproduce-environment-from-docs` |
| **beforeReadFile** (sensitive paths) | `redact-sensitive-in-output` (filter before model) |
| **postToolUse** (Write/Edit on code) | `trace-data-flow` (optional: when flow-tracing requested) |

**Skill paths** (for implementation): `code-workflows/*`, `api-workflows/*`, `config-workflows/*`, `dependency-workflows/*`, `docs-workflows/*`, `git-workflows/*`, `migration-workflows/*`, `navigation-workflows/*`, `performance-workflows/*`, `release-workflows/*`, `security-workflows/*`, `shared-practices/*`, `testing-workflows/*`.

### Phase 3: Hook Categories

Include hooks in these categories. Prioritize high-impact over low-value automation.

#### A. Code Quality Enforcement

- Validation of edits (formatting, lint rules, type checks).
- Block or warn on edits that violate project standards.
- Scope: code files, config files, or specific globs.

#### B. Architectural Consistency

- Enforce layering, boundaries, or naming conventions.
- Check that new/modified code aligns with project rules or conventions.
- Flag edits that violate architecture (e.g. domain logic in controllers).

#### C. Preventing Duplication or Dead Code

- Detect or warn when edits introduce obvious duplication.
- Flag edits that add code with no references or that duplicate existing logic.
- Surface patterns that suggest extraction or consolidation.

#### D. Feature Scaffolding

- When creating new modules, components, or packages: ensure required files exist, conventions are followed, and cross-references are consistent.
- Validate structure of new additions (e.g. correct placement, exports, imports).

#### E. Refactoring Assistance

- After bulk renames or moves: suggest or validate import/export updates.
- Ensure refactors preserve build, tests, and dependency graphs.

#### F. Safety and Guardrails

- Block destructive shell commands (e.g. `rm -rf /`, `git push --force` to protected branches).
- Prevent edits to sensitive paths (e.g. `.env`, secrets) unless explicitly allowed.
- Redact or filter sensitive content before it leaves the machine (if applicable).

### Phase 4: Output Format

Produce a structured implementation plan with:

1. **Executive summary** – Top 5–7 hooks by impact, with rationale.
2. **Full hook specifications** – One section per hook, using the table format above. Include the **Skills** column: which skill(s) to invoke when the hook runs.
3. **Skill–hook matrix** – For each skill in `.cursor/skills/`, which hook(s) trigger it and under what conditions.
4. **Trigger matrix** – Which lifecycle events are used and for what.
5. **Dependencies** – Scripts or tools each hook assumes (e.g. `jq`, `pwsh`, `black`).
6. **Rollout order** – Suggested implementation order (safety first, then quality, then convenience).
7. **Caveats** – Limitations, false-positive risks, and when to prefer manual review.

### Constraints

- **Do not** generate new hook scripts or `hooks.json` content beyond what exists in `templates/hooks/`; reference the implementation above when present.
- **Do not** invent files or APIs; only reference what exists in the repo.
- **Skill mapping**: Only map skills that exist in `.cursor/skills/`; omit or adapt entries if a skill is absent.
- **Prioritize** hooks that prevent mistakes and enforce consistency over purely cosmetic automation.
- **Adapt** hook proposals to the project's structure, conventions, and workflows—no one-size-fits-all.
