#!/usr/bin/env bash
# Resource usage ledger: rules, skills, subagents, hooks.
# Writes .cursor/logs/resource-ledger/active.json during a generation;
# on stop, appends summary to cursor-resources-YYYY-MM-DD.jsonl.
# Requires: jq

set -euo pipefail

emit_allow() {
  local ev="$1"
  case "$ev" in
    beforeSubmitPrompt) printf '%s\n' '{"continue":true,"permission":"allow"}' ;;
    preToolUse|subagentStart) printf '%s\n' '{"permission":"allow"}' ;;
  esac
}

extract_hook_event() {
  local raw="$1"
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$raw" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('hook_event_name') or '')" 2>/dev/null || true
    return
  fi
  if printf '%s' "$raw" | grep -q '"hook_event_name"'; then
    printf '%s' "$raw" | sed -n 's/.*"hook_event_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1
  fi
}

if ! command -v jq >/dev/null 2>&1; then
  raw=$(cat || true)
  event=$(extract_hook_event "$raw")
  if [[ -n "$event" ]]; then
    emit_allow "$event"
  elif [[ -n "${raw//[[:space:]]/}" ]]; then
    printf '%s\n' '{"continue":true,"permission":"allow"}'
  fi
  exit 0
fi

raw=$(cat || true)
if [[ -z "${raw//[[:space:]]/}" ]]; then
  exit 0
fi

event=$(echo "$raw" | jq -r '.hook_event_name // empty')
if [[ -z "$event" ]]; then
  exit 0
fi

project_root=$(echo "$raw" | jq -r '.workspace_roots[0] // empty')
if [[ -z "$project_root" || "$project_root" == "null" ]]; then
  start_dir=$(echo "$raw" | jq -r '.cwd // empty')
  if [[ -z "$start_dir" ]]; then
    start_dir=$(pwd)
  fi
  project_root=$(git -C "$start_dir" rev-parse --show-toplevel 2>/dev/null || true)
fi

if [[ -z "$project_root" ]]; then
  if [[ "$event" == "beforeSubmitPrompt" || "$event" == "preToolUse" || "$event" == "subagentStart" ]]; then
    emit_allow "$event"
  fi
  exit 0
fi

ledger_dir="${project_root}/.cursor/logs/resource-ledger"
log_dir="${project_root}/.cursor/logs"
mkdir -p "$ledger_dir" "$log_dir"
active_path="${ledger_dir}/active.json"

get_hooks_configured() {
  local hooks_json="${project_root}/.cursor/hooks.json"
  if [[ ! -f "$hooks_json" ]]; then
    printf '[]'
    return
  fi
  jq -c '
    [.hooks | to_entries[] | .key as $hook | .value[]? | "\($hook):\(.command | split(" ") | last | gsub("\""; ""))"]
    | unique | sort
  ' "$hooks_json" 2>/dev/null || printf '[]'
}

skill_name_from_path() {
  local p="${1//\\//}"
  if [[ "$p" =~ /skills/([^/]+)/SKILL\.md$ ]]; then
    echo "${BASH_REMATCH[1]}"
  elif [[ "$p" =~ /([^/]+)/SKILL\.md$ ]]; then
    echo "${BASH_REMATCH[1]}"
  fi
}

append_tracking_event() {
  local ledger="$1"
  local track="$2"
  echo "$ledger" | jq --arg t "$track" '
    .tracking_events = ((.tracking_events // []) + [$t] | unique)
  '
}

case "$event" in
  beforeSubmitPrompt)
    rules=$(echo "$raw" | jq -c '
      def names:
        if . == null then []
        elif type == "string" then (if length > 0 then [.] else [] end)
        elif type == "array" then map(if type == "string" then . elif type == "object" then (.name // .id // tostring) else tostring end) | map(select(length > 0)) | unique
        else [] end;
      [
        .rules, .used_rules, .applied_rules, .matched_rules, .active_rules, .rule_names
      ] | map(select(. != null)) | .[0] // [] | names
    ')
    skills=$(echo "$raw" | jq -c '
      def names:
        if . == null then []
        elif type == "string" then (if length > 0 then [.] else [] end)
        elif type == "array" then map(if type == "string" then . elif type == "object" then (.name // .id // tostring) else tostring end) | map(select(length > 0)) | unique
        else [] end;
      [
        .skills, .used_skills, .applied_skills, .matched_skills, .selected_skills, .skill_names
      ] | map(select(. != null)) | .[0] // [] | names
    ')
    hooks_cfg=$(get_hooks_configured)
    echo "$raw" | jq -c \
      --argjson rules "$rules" \
      --argjson skills "$skills" \
      --argjson hooks "$hooks_cfg" \
      --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
      '{
        ts: $ts,
        generation_id: (.generation_id // ""),
        conversation_id: (.conversation_id // ""),
        rules: $rules,
        skills_payload: $skills,
        skills_read: [],
        subagents: [],
        hooks_configured: $hooks,
        tracking_events: ["beforeSubmitPrompt"]
      }' >"$active_path"
    emit_allow "$event"
    ;;

  preToolUse)
    tool_name=$(echo "$raw" | jq -r '.tool_name // empty')
    if [[ "$tool_name" == "Read" ]]; then
      read_path=$(echo "$raw" | jq -r '.tool_input.path // .tool_input.target_file // empty')
      skill_name=$(skill_name_from_path "$read_path")
      if [[ -n "$skill_name" ]]; then
        if [[ -f "$active_path" ]]; then
          ledger=$(cat "$active_path")
        else
          ledger=$(echo "$raw" | jq -c '{
            ts: (now | todate),
            generation_id: (.generation_id // ""),
            conversation_id: (.conversation_id // ""),
            rules: [],
            skills_payload: [],
            skills_read: [],
            subagents: [],
            tracking_events: []
          }')
        fi
        ledger=$(echo "$ledger" | jq --arg s "$skill_name" '
          .skills_read = ((.skills_read // []) + [$s] | unique) |
          .ts = (now | todate)
        ')
        ledger=$(append_tracking_event "$ledger" "preToolUse:skill_read")
        printf '%s\n' "$ledger" >"$active_path"
      fi
    fi
    emit_allow "$event"
    ;;

  subagentStart)
    if [[ -f "$active_path" ]]; then
      ledger=$(cat "$active_path")
    else
      ledger=$(echo "$raw" | jq -c '{
        ts: (now | todate),
        generation_id: (.generation_id // ""),
        conversation_id: (.conversation_id // ""),
        rules: [],
        skills_payload: [],
        skills_read: [],
        subagents: [],
        tracking_events: []
      }')
    fi
    entry=$(echo "$raw" | jq -c '{
      id: (.subagent_id // ""),
      type: (.subagent_type // ""),
      task: (.task // ""),
      status: "started",
      ts: (now | todate)
    }')
    ledger=$(echo "$ledger" | jq --argjson e "$entry" '
      .subagents = ((.subagents // []) + [$e]) |
      .ts = (now | todate)
    ')
    ledger=$(append_tracking_event "$ledger" "subagentStart")
    printf '%s\n' "$ledger" >"$active_path"
    emit_allow "$event"
    ;;

  subagentStop)
    if [[ ! -f "$active_path" ]]; then
      exit 0
    fi
    sub_type=$(echo "$raw" | jq -r '.subagent_type // empty')
    sub_status=$(echo "$raw" | jq -r '.status // empty')
    sub_task=$(echo "$raw" | jq -r '.task // empty')
    ledger=$(cat "$active_path" | jq \
      --arg t "$sub_type" \
      --arg st "$sub_status" \
      --arg tk "$sub_task" \
      '
      . as $root |
      (.subagents // []) as $subs |
      (reduce range(0; ($subs | length)) as $i (
        {subs: $subs, matched: false};
        if .matched then .
        elif (.subs[$i].type == $t and .subs[$i].status == "started") then
          .subs[$i] |= (
            .status = $st |
            .task = (if ($tk | length) > 0 then $tk else .task end) |
            .ts = (now | todate)
          ) |
          .matched = true
        else .
        end
      )) as $r |
      if $r.matched then
        $root | .subagents = $r.subs | .ts = (now | todate)
      else
        $root | .subagents = $subs + [{id: "", type: $t, task: $tk, status: $st, ts: (now | todate)}] | .ts = (now | todate)
      end
      ')
    ledger=$(append_tracking_event "$ledger" "subagentStop")
    printf '%s\n' "$ledger" >"$active_path"
    ;;

  stop)
    if [[ ! -f "$active_path" ]]; then
      exit 0
    fi
    ledger=$(cat "$active_path")
    status=$(echo "$raw" | jq -r '.status // empty')
    summary=$(echo "$ledger" | jq -c \
      --arg st "$status" \
      --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
      '{
        ts: $ts,
        event: "resource_summary",
        generation_id: .generation_id,
        conversation_id: .conversation_id,
        status: $st,
        rules: (.rules // []),
        skills_payload: (.skills_payload // []),
        skills_read: (.skills_read // []),
        subagents: (.subagents // []),
        hooks_configured: (.hooks_configured // []),
        tracking_events: ((.tracking_events // []) + ["stop"] | unique)
      }')
    resources_log="${log_dir}/cursor-resources-$(date +%Y-%m-%d).jsonl"
    printf '%s\n' "$summary" >>"$resources_log"
    printf '%s\n' "$summary" | jq '.' >"${ledger_dir}/latest.json"
    ledger=$(append_tracking_event "$ledger" "stop")
    printf '%s\n' "$ledger" >"$active_path"
    ;;

  *)
    exit 0
    ;;
esac

exit 0
