#!/usr/bin/env bash
# Log Cursor activity: prompts, edits, shell commands, session end.
# Writes to project/.cursor/logs/cursor-activity-YYYY-MM-DD.jsonl
# Requires: jq (https://jqlang.org/)

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

event=$(echo "$raw" | jq -r '.hook_event_name // empty')

project_root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
if [[ -z "$project_root" || "$project_root" == "null" ]]; then
  start_dir=$(echo "$raw" | jq -r '.cwd // empty')
  if [[ -z "$start_dir" ]]; then
    start_dir=$(pwd)
  fi
  project_root=$(git -C "$start_dir" rev-parse --show-toplevel 2>/dev/null || true)
fi

if [[ -z "$project_root" ]]; then
  exit 0
fi

log_dir="${project_root}/.cursor/logs"
mkdir -p "$log_dir"
log_file="${log_dir}/cursor-activity-$(date +%Y-%m-%d).jsonl"

line=$(echo "$raw" | jq -c --arg ev "$event" '
  def trunc(s):
    if s == null then null
    elif (s | type) == "string" and (s | length) > 50000 then s[0:50000] + "...[truncated]"
    else s end;
  .content |= trunc |
  .prompt |= trunc |
  .edits |= if . == null then null else map(.old_string |= trunc | .new_string |= trunc) end |
  . + { ts: (now | todate), event: $ev }
')

printf '%s\n' "$line" >>"$log_file"

if [[ "$event" == "beforeShellExecution" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
fi
exit 0
