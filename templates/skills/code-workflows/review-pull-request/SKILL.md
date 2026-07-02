---
name: review-pull-request
description: Performs end-to-end PR review or author feedback resolution: diff analysis, checklist, structured feedback (CRITICAL, WARNING, GOOD), triage/fix/reply/resolve review threads, and follow-up verification. Use for PR review, addressing reviewer comments on your PR, or when context includes staged or diff content.
---

# Review Pull Request

## Routing: reviewer vs author

- **Reviewer** (someone else's PR): sections **Reviewer workflow** and **Output Contract** below.
- **Author** (your PR got comments): use **Address review feedback (author)** — fix, reply, resolve threads, re-request review.

## Reviewer workflow

1. **Gather context**
   - Obtain the full diff (staged, unstaged, or branch comparison). Use `git diff` or provided patch.
   - Identify touched files, new vs modified, and affected areas (e.g. API layer, DB, tests).
   - If GitHub MCP is configured, pull PR metadata (title/body, checks, review comments, linked issues) and include it in review context.

2. **Apply review checklist**
   - Correctness: logic, edge cases, off-by-one, null/empty handling.
   - Security: injection (SQL, command, XSS), auth/authz, secrets, unsafe deserialization.
   - Maintainability: naming, function size, duplication, coupling.
   - Error handling: specific exception/error types, narrow catches, preserved cause chains; flag generic `Exception`, broad `except Exception:`, swallowed errors.
   - Style: match project conventions (linter/formatter); flag only meaningful violations.
   - Tests: changes have corresponding tests; existing tests still pass.

3. **Produce structured feedback**
   - **CRITICAL:** Must fix before merge (bugs, security, contract breaks).
   - **WARNING:** Should consider (readability, performance, robustness).
   - **GOOD:** Optional improvement.
   - Cite file and line or snippet; be specific and actionable.

4. **Summarize**
   - One short summary: overall assessment and top 1–3 items to address.
   - If applicable, note follow-up verification (e.g. "run tests," "check migration").
   - If GitHub MCP was used, include unresolved review threads/check failures as explicit blockers.

## Output Contract

- Overall assessment (1–2 sentences) and top 1–3 items to address
- Findings grouped by **CRITICAL** / **WARNING** / **GOOD** with file:line or region references (do not repeat the full diff)
- Follow-up verification (e.g. tests to run, migrations to check)

## Routing boundaries

- If findings are primarily security-sensitive, run `security-scan-changes` as the primary in-template security review step.
- For frontend-only deep quality checks, route execution to FE agents and keep this skill focused on cross-stack PR hygiene.

## Address review feedback (author)

After opening a PR and receiving review comments:

1. **Fetch threads** — `gh pr view <n> --comments`, `gh api` review threads, or GitHub MCP `pull_request_read`.
2. **Triage** — valid bug/security/contract → fix; nit → fix or reply with rationale; out of scope → reply and open a follow-up issue.
3. **Fix** on the same branch; run the full test suite locally; push (triggers CI).
4. **Reply on every thread** — cite file/commit or explain why not changing.
5. **Resolve** each thread via GitHub UI/API after the fix is pushed.
6. **Re-request review** when all threads are resolved and required checks are green.

Do not merge until CI passes, threads are resolved, and approvals are satisfied. Follow `git-github-workflow.mdc` for merge method (merge commit only, keep branch).
