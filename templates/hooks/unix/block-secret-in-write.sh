#!/usr/bin/env bash
# Block Write/Edit when content contains hardcoded secrets.

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

raw=$(cat || true)
_hook_script="$(basename "${BASH_SOURCE[0]}")"
trap 'register_hook_execution "$raw" "$_hook_script"' EXIT

if [[ -z "${raw//[[:space:]]/}" ]]; then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

event=$(echo "$raw" | jq -r '.hook_event_name // empty')
if [[ "$event" != "preToolUse" ]]; then
  exit 0
fi

project_root=$(project_root_from_payload "$raw")
if ! py=$(find_python); then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi
if ! scanner=$(find_scan_write_script "$project_root"); then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

out=$(printf '%s' "$raw" | "$py" "$scanner" tool-payload 2>/dev/null) || {
  printf '%s\n' '{"permission":"allow"}'
  exit 0
}

issues=$(echo "$out" | jq -r '.issues // [] | join(", ")' 2>/dev/null || true)
count=$(echo "$out" | jq -r '.issues // [] | length' 2>/dev/null || echo 0)
if [[ "${count:-0}" -gt 0 ]]; then
  jq -n \
    --arg list "$issues" \
    '{
      permission: "deny",
      user_message: ("Write blocked: possible secret in content (" + $list + "). Use env vars or placeholders."),
      agent_message: "Remove hardcoded secrets; reference environment variable names only."
    }'
  exit 0
fi

printf '%s\n' '{"permission":"allow"}'
exit 0
