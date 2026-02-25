---
name: review-pull-request
description: Performs end-to-end PR review: diff analysis, checklist against project or team standards, structured feedback (critical, suggestion, nice-to-have), and follow-up verification. Use when the user asks for a PR or code review, says "review this change," or when context includes staged or diff content.
---

# Review Pull Request

## Workflow

1. **Gather context**
   - Obtain the full diff (staged, unstaged, or branch comparison). Use `git diff` or provided patch.
   - Identify touched files, new vs modified, and affected areas (e.g. API layer, DB, tests).

2. **Apply review checklist**
   - Correctness: logic, edge cases, off-by-one, null/empty handling.
   - Security: injection (SQL, command, XSS), auth/authz, secrets, unsafe deserialization.
   - Maintainability: naming, function size, duplication, coupling.
   - Style: match project conventions (linter/formatter); flag only meaningful violations.
   - Tests: changes have corresponding tests; existing tests still pass.

3. **Produce structured feedback**
   - **Critical:** Must fix before merge (bugs, security, contract breaks).
   - **Suggestion:** Should consider (readability, performance, robustness).
   - **Nice to have:** Optional improvement.
   - Cite file and line or snippet; be specific and actionable.

4. **Summarize**
   - One short summary: overall assessment and top 1–3 items to address.
   - If applicable, note follow-up verification (e.g. "run tests," "check migration").

## Output format

Use clear headings and bullet lists. Group feedback by severity. Do not repeat the diff; reference it by file/region.
