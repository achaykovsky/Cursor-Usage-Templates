# GitHub templates

Repository policy templates aligned with [`git-github-workflow.mdc`](../rules/git-github-workflow.mdc).

## Branch protection ruleset

[`rulesets/default-branch-protection.json`](rulesets/default-branch-protection.json) enforces:

- **Merge commit only** (`allowed_merge_methods: ["merge"]`)
- **Required status checks** with strict up-to-date policy (customize `required_status_checks[].context` to match your CI job names)
- **Review thread resolution** before merge
- **No bypass actors** (`bypass_actors: []`)
- **No force-push** to the default branch (`non_fast_forward`)

### Apply with GitHub CLI

1. Edit `required_status_checks` contexts to match your workflow (e.g. `test`, `lint`, `build`).
2. Create or update the ruleset:

```bash
gh api repos/{owner}/{repo}/rulesets \
  --method POST \
  --input templates/github/rulesets/default-branch-protection.json
```

Or import via **Settings → Rules → Rulesets** in the GitHub UI.

### CI context names

Find check contexts from a recent PR:

```bash
gh pr checks <number> --json name,state,bucket
```

Use the `name` values in `required_status_checks[].context`.

## CODEOWNERS

[`CODEOWNERS`](CODEOWNERS) pairs with `require_code_owner_review` in the ruleset. Update paths and teams for your org.

## Related Cursor config

- **Hooks:** `validate-git-commands` blocks local history rewrite; `validate-pre-push` blocks push on test failure (`pre_push: deny`).
- **Rule:** `git-github-workflow.mdc` — agent merge/review policy.
- **Override (emergency only):** `.cursor/hook-policy.json` with `git_history_rewrite: ask`.
