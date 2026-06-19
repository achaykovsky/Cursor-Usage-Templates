#!/usr/bin/env bash
# Shared helpers for Unix hook scripts that invoke the policy engine.

set -euo pipefail

find_python() {
  for bin in python3 python py; do
    if command -v "$bin" >/dev/null 2>&1; then
      command -v "$bin"
      return 0
    fi
  done
  return 1
}

find_policy_script() {
  local project_root="${1:-}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  if [[ -n "$project_root" && -f "${project_root}/.cursor/hooks/policy/hook_policy.py" ]]; then
    printf '%s\n' "${project_root}/.cursor/hooks/policy/hook_policy.py"
    return 0
  fi
  if [[ -f "${script_dir}/policy/hook_policy.py" ]]; then
    printf '%s\n' "${script_dir}/policy/hook_policy.py"
    return 0
  fi
  return 1
}

project_root_from_payload() {
  local raw="$1"
  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi
  local root
  root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
  if [[ -n "$root" && "$root" != "null" ]]; then
    printf '%s\n' "$root"
    return 0
  fi
  root=$(echo "$raw" | jq -r '.cwd // empty')
  if [[ -n "$root" ]]; then
    printf '%s\n' "$root"
  fi
}

invoke_hook_policy() {
  local domain="$1"
  local raw="$2"
  local project_root="${3:-}"
  local py policy
  if ! py=$(find_python); then
    printf '%s\n' '{"continue":true,"permission":"allow"}'
    return 0
  fi
  if ! policy=$(find_policy_script "$project_root"); then
    printf '%s\n' '{"continue":true,"permission":"allow"}'
    return 0
  fi
  printf '%s' "$raw" | "$py" "$policy" "$domain" || printf '%s\n' '{"continue":true,"permission":"allow"}'
}
