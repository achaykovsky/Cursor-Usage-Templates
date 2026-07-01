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

find_redact_script() {
  local project_root="${1:-}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  if [[ -n "$project_root" && -f "${project_root}/.cursor/hooks/policy/redact_sensitive.py" ]]; then
    printf '%s\n' "${project_root}/.cursor/hooks/policy/redact_sensitive.py"
    return 0
  fi
  if [[ -f "${script_dir}/policy/redact_sensitive.py" ]]; then
    printf '%s\n' "${script_dir}/policy/redact_sensitive.py"
    return 0
  fi
  return 1
}

invoke_redact_text() {
  local text="$1"
  local project_root="${2:-}"
  local py script out
  if [[ -z "$text" ]]; then
    printf '%s' "$text"
    return 0
  fi
  if ! py=$(find_python); then
    printf '%s' "$text"
    return 0
  fi
  if ! script=$(find_redact_script "$project_root"); then
    printf '%s' "$text"
    return 0
  fi
  out=$(printf '%s' "$text" | "$py" "$script" redact-text 2>/dev/null) || {
    printf '%s' "$text"
    return 0
  }
  printf '%s' "$out"
}

cursor_logs_root_dir() {
  local project_root="$1"
  printf '%s\n' "${project_root}/logs"
}

cursor_logs_date_dir() {
  local project_root="$1"
  local date_folder
  date_folder=$(date +%Y-%m-%d)
  local dir
  dir=$(cursor_logs_root_dir "$project_root")
  dir="${dir}/${date_folder}"
  mkdir -p "$dir"
  printf '%s\n' "$dir"
}

cursor_log_file_path() {
  local project_root="$1"
  local log_base_name="$2"
  local dir
  dir=$(cursor_logs_date_dir "$project_root")
  printf '%s\n' "${dir}/${log_base_name}.jsonl"
}

read_active_ledger() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    return 1
  fi
  cat "$path"
}

register_hook_execution() {
  local raw="$1"
  local script_file="$2"
  local event project_root active_path ledger entry

  if [[ -z "$script_file" ]] || ! command -v jq >/dev/null 2>&1; then
    return 0
  fi

  event=$(printf '%s' "$raw" | jq -r '.hook_event_name // empty' 2>/dev/null || true)
  if [[ -z "$event" ]]; then
    return 0
  fi

  project_root=$(project_root_from_payload "$raw")
  if [[ -z "$project_root" ]]; then
    return 0
  fi

  active_path="$(cursor_logs_root_dir "$project_root")/resource-ledger/active.json"
  mkdir -p "$(dirname "$active_path")"
  entry="${event}:${script_file}"

  if read_active_ledger "$active_path" >/dev/null 2>&1; then
    ledger=$(cat "$active_path")
  else
    ledger=$(printf '%s' "$raw" | jq -c '{
      ts: (now | todate),
      generation_id: (.generation_id // ""),
      conversation_id: (.conversation_id // ""),
      hooks_executed: []
    }')
  fi

  ledger=$(echo "$ledger" | jq --arg e "$entry" '
    .hooks_executed = ((.hooks_executed // []) + [$e] | unique | sort) |
    .ts = (now | todate)
  ')

  if [[ "$event" == "beforeMCPExecution" ]]; then
    mcp_entry=$(printf '%s' "$raw" | jq -c '{
      server: (.server // .server_name // .mcp_server // ""),
      tool: (.tool_name // .toolName // .name // .mcp_tool_name // "")
    }' 2>/dev/null || true)
    if [[ -n "$mcp_entry" && "$mcp_entry" != '{"server":"","tool":""}' ]]; then
      ledger=$(echo "$ledger" | jq --argjson entry "$mcp_entry" '
        .mcp = (
          (.mcp // []) + [$entry]
          | unique_by(.server + "|" + .tool)
        )
      ')
    fi
  fi

  write_active_ledger_atomic "$active_path" "$ledger"
}

write_active_ledger_atomic() {
  local path="$1"
  local content="$2"
  local dir lock tmp
  dir=$(dirname "$path")
  mkdir -p "$dir"
  lock="${path}.lock"
  tmp="${dir}/active.json.$$.$RANDOM.tmp"
  if command -v flock >/dev/null 2>&1; then
    (
      flock -x 200
      printf '%s\n' "$content" >"$tmp"
      mv -f "$tmp" "$path"
    ) 200>"$lock"
  else
    printf '%s\n' "$content" >"$tmp"
    mv -f "$tmp" "$path"
  fi
}

find_routing_script() {
  local project_root="${1:-}"
  local script_dir templates_root path
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  templates_root="$(cd "${script_dir}/.." && pwd)"
  for path in \
    "${project_root}/templates/commands/routing.py" \
    "${project_root}/.cursor/commands/routing.py" \
    "${templates_root}/commands/routing.py"; do
    if [[ -n "$path" && -f "$path" ]]; then
      printf '%s\n' "$path"
      return 0
    fi
  done
  return 1
}

prompt_predictions_from_routing() {
  local prompt="$1"
  local project_root="${2:-}"
  local py script out
  if [[ -z "$prompt" ]]; then
    printf '%s\n' '{"predicted_skills":[],"predicted_rules":[]}'
    return 0
  fi
  if ! py=$(find_python); then
    printf '%s\n' '{"predicted_skills":[],"predicted_rules":[]}'
    return 0
  fi
  if ! script=$(find_routing_script "$project_root"); then
    printf '%s\n' '{"predicted_skills":[],"predicted_rules":[]}'
    return 0
  fi
  out=$("$py" "$script" predict --task "$prompt" 2>/dev/null) || {
    printf '%s\n' '{"predicted_skills":[],"predicted_rules":[]}'
    return 0
  }
  if [[ -z "$out" ]]; then
    printf '%s\n' '{"predicted_skills":[],"predicted_rules":[]}'
    return 0
  fi
  printf '%s\n' "$out"
}
