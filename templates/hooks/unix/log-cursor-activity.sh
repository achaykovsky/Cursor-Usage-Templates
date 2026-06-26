#!/usr/bin/env bash
# Log Cursor activity: structured JSONL per event type.
# Writes to project/.cursor/logs/YYYY-MM-DD/cursor-activity.jsonl

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

allow_shell() {
  printf '%s\n' '{"continue":true,"permission":"allow"}'
}

find_python() {
  for bin in python3 python py; do
    if command -v "$bin" >/dev/null 2>&1; then
      command -v "$bin"
      return 0
    fi
  done
  return 1
}

find_activity_script() {
  local project_root="${1:-}"
  local script_dir templates_root
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  templates_root="$(cd "${script_dir}/.." && pwd)"
  if [[ -n "$project_root" && -f "${project_root}/templates/commands/cursor_activity.py" ]]; then
    printf '%s\n' "${project_root}/templates/commands/cursor_activity.py"
    return 0
  fi
  if [[ -n "$project_root" && -f "${project_root}/.cursor/commands/cursor_activity.py" ]]; then
    printf '%s\n' "${project_root}/.cursor/commands/cursor_activity.py"
    return 0
  fi
  if [[ -f "${templates_root}/commands/cursor_activity.py" ]]; then
    printf '%s\n' "${templates_root}/commands/cursor_activity.py"
    return 0
  fi
  return 1
}

raw=$(cat || true)
_hook_script="$(basename "${BASH_SOURCE[0]}")"
trap 'register_hook_execution "$raw" "$_hook_script"' EXIT
if [[ -z "${raw//[[:space:]]/}" ]]; then
  allow_shell
  exit 0
fi

event=""
if command -v jq >/dev/null 2>&1; then
  event=$(echo "$raw" | jq -r '.hook_event_name // empty')
fi

project_root=""
if command -v jq >/dev/null 2>&1; then
  project_root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
fi
if [[ -z "$project_root" || "$project_root" == "null" ]]; then
  start_dir=""
  if command -v jq >/dev/null 2>&1; then
    start_dir=$(echo "$raw" | jq -r '.cwd // empty')
  fi
  if [[ -z "$start_dir" ]]; then
    start_dir=$(pwd)
  fi
  project_root=$(git -C "$start_dir" rev-parse --show-toplevel 2>/dev/null || true)
fi

if [[ -z "$project_root" ]]; then
  if [[ "$event" == "beforeShellExecution" ]]; then
    allow_shell
  fi
  exit 0
fi

log_file=$(cursor_log_file_path "$project_root" "cursor-activity")

line=""
if py=$(find_python); then
  if activity=$(find_activity_script "$project_root"); then
    line=$(printf '%s' "$raw" | "$py" "$activity" normalize 2>/dev/null || true)
  fi
fi

if [[ -z "$line" ]]; then
  if command -v jq >/dev/null 2>&1; then
    line=$(echo "$raw" | jq -c --arg ev "$event" '
      . + {
        ts: (now | todate),
        event: (if $ev != "" then $ev else
          if .file_path and .edits then "afterFileEdit"
          elif .prompt then "beforeSubmitPrompt"
          elif .command then "beforeShellExecution"
          elif .status then "stop"
          else "unknown" end)
      }
      | {
          ts, event,
          conversation_id,
          generation_id,
          prompt,
          file_path,
          command,
          cwd,
          status
        }
      | with_entries(select(.value != null))
    ')
  else
  line='{"ts":"'"$(date -Iseconds)"'","event":"'"${event:-unknown}"'"}'
  fi
fi

printf '%s\n' "$line" >>"$log_file"

if [[ "$event" == "beforeShellExecution" ]]; then
  allow_shell
fi
exit 0
