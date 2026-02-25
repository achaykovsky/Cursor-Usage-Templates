---
name: prepare-atomic-commit
description: Analyzes working tree and staged state, groups changes into logical commits, proposes imperative commit messages, and optionally validates against conventional-commit or project rules. Use when the user asks for a commit message, "split this into commits," or pre-push cleanup.
---

# Prepare Atomic Commit

## Workflow

1. **Analyze working tree**
   - Run `git status` and `git diff` (staged and unstaged). List all changed files and the nature of changes (new feature, fix, refactor, docs, config, formatting).

2. **Group into logical commits**
   - One logical change per commit. Typical groups: feature + tests, fix + test, refactor, docs, style/lint, dependency or config.
   - Avoid mixing unrelated edits (e.g. "fix bug" and "bump dependency" in one commit). If the user has one big working tree, propose a split.

3. **Propose commit messages**
   - Use imperative mood: "Add X," "Fix Y," "Refactor Z." First line concise (e.g. <72 chars); body optional for why.
   - If the project uses conventional commits (e.g. `feat:`, `fix:`, `chore:`), follow that. Otherwise propose a consistent style.
   - For each proposed commit: list the files or hunks that belong in it, then the message.

4. **Optional validation**
   - If the repo has commit message rules (e.g. in `.github/`, `commitlint`, or CONTRIBUTING): check length, format, and required scope/type. Suggest edits if the proposal violates them.

## Output

- For "one commit": single message + optional body.
- For "split into commits": ordered list of (files/hunks, message) pairs and exact commands to stage per commit if the user wants to apply the split (e.g. `git add ...` then `git commit -m "..."`).

## Notes

- Apply **suggest-commands-dont-run-destructive** (shared-practices). Prefer showing commands for the user to run. If there are only unstaged changes, propose messages and staging order; do not assume `git add -A` without user intent.
