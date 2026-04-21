#!/usr/bin/env bash
# Validate template terminology/policy consistency before submit or after edits.
# Requires: jq, rg

set -euo pipefail

if ! command -v jq >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

cwd=$(echo "$raw" | jq -r '.cwd // empty')
root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
r="$cwd"
if [[ -z "$r" ]]; then
  r="$root"
fi
if [[ -z "$r" || ! -d "$r" || ! -d "$r/templates" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

issues=()
check_pattern() {
  local pattern=$1
  local message=$2
  local scope=$3
  local target="$r/$scope"
  if [[ ! -d "$target" && ! -f "$target" ]]; then
    return
  fi
  local hit
  hit=$(rg -n --glob '*.md' --glob '*.mdc' --glob '*.json' "$pattern" "$target" 2>/dev/null | head -n 1 || true)
  if [[ -n "$hit" ]]; then
    issues+=("$message ($hit)")
  fi
}

check_pattern '@agent\(FRONTEND\)' 'Legacy @agent(FRONTEND) reference found. Use FE_* invokes.' 'templates'
check_pattern '\| FRONTEND \|' 'Legacy FRONTEND table entry found. Use FE_* agents.' 'templates'
check_pattern 'frontend_engineer\.md' 'Legacy frontend_engineer.md reference found. Use fe_ui_engineer.md.' 'templates'
check_pattern 'authoritative security pass' "Use 'primary in-template security review step' wording." 'templates/skills'
check_pattern 'tabIndex for focus order' 'Use semantic DOM order guidance (avoid positive tabIndex).' 'templates/rules'
check_pattern 'dev-secret-change-in-prod' 'Insecure secret default found in templates.' 'templates'

if [[ ${#issues[@]} -gt 0 ]]; then
  msg="${issues[0]}"
  if [[ ${#issues[@]} -gt 1 ]]; then
    msg="$msg | ${issues[1]}"
  fi
  if [[ ${#issues[@]} -gt 2 ]]; then
    msg="$msg | ${issues[2]}"
  fi
  jq -nc --arg m "$msg" \
    '{continue:false,permission:"deny",user_message:("Template consistency check failed: " + $m),agent_message:"Update docs/rules/skills to canonical terminology and policy."}'
  exit 0
fi

printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
