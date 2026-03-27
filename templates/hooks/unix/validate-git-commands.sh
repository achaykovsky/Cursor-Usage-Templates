#!/usr/bin/env bash
# Validate git commit messages and block force-push on protected branches.
# Requires: jq

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

cmd=$(echo "$raw" | jq -r '.command // ""' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
cwd=$(echo "$raw" | jq -r '.cwd // empty')
root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
git_root=$cwd
if [[ -z "$git_root" ]]; then
  git_root=$root
fi

deny() {
  local user_msg=$1
  local agent_msg=$2
  jq -nc --arg u "$user_msg" --arg a "$agent_msg" \
    '{continue:false,permission:"deny",user_message:$u,agent_message:$a}'
  exit 0
}

# --- git commit -m "msg" validation ---
if [[ "$cmd" =~ git[[:space:]]+commit ]]; then
  msg=""
  if [[ "$cmd" =~ -m[[:space:]]+\"([^\"]+)\" ]]; then
    msg="${BASH_REMATCH[1]}"
  elif [[ "$cmd" =~ -m[[:space:]]+\'([^\']+)\' ]]; then
    msg="${BASH_REMATCH[1]}"
  fi
  if [[ -n "$msg" ]]; then
    first_line=${msg%%$'\n'*}
    flen=${#first_line}
    if ((flen > 72)); then
      deny "Commit message first line too long ($flen > 72 chars)." "Use prepare-atomic-commit: keep first line <= 72 chars."
    fi
    if ((flen < 10)); then
      deny "Commit message too short. Use imperative mood (e.g. 'Add X', 'Fix Y')." "Use prepare-atomic-commit for message format."
    fi
    skip_conventional=false
    if [[ -n "$git_root" && -f "${git_root}/.cursor/allow-non-conventional-commit" ]]; then
      skip_conventional=true
    fi
    if [[ "$skip_conventional" == false ]]; then
      if ! printf '%s\n' "$first_line" | grep -qE '^(feat|fix|chore|docs|refactor|test|style|perf|build|ci)(\([a-z0-9-]+\))?!?: .+'; then
        deny "Commit message should follow conventional format: type(scope): description (e.g. feat: add login). Create .cursor/allow-non-conventional-commit to skip." "Use prepare-atomic-commit for conventional commits."
      fi
    fi
  fi
fi

# --- git push --force (without --force-with-lease) on protected branches ---
# Match --force as a flag token, not the prefix of --force-with-lease
if printf '%s\n' "$cmd" | grep -qE 'git[[:space:]]+push' && printf '%s\n' "$cmd" | grep -qE '(^|[[:space:]])--force([[:space:]]|$)'; then
  if [[ -z "$git_root" || ! -d "${git_root}/.git" ]]; then
    printf '%s\n' '{"continue":true,"permission":"allow"}'
    exit 0
  fi
  branch=$(git -C "$git_root" branch --show-current 2>/dev/null || true)
  if [[ "$branch" == "main" || "$branch" == "master" ]]; then
    deny "Force push to ${branch} is blocked. Use --force-with-lease if you must." "Use suggest-commands-dont-run-destructive: suggest the command for the user to run."
  fi
fi

printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
