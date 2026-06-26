#!/usr/bin/env bash
# Resource usage ledger: rules, skills, subagents, hooks.
# Writes .cursor/logs/resource-ledger/active.json during a generation;
# on stop, appends summary to cursor-resources-YYYY-MM-DD.jsonl.
# Requires: jq

set -euo pipefail

# shellcheck source=hook-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hook-common.sh"

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

agent_invoke_from_subagent_file() {
  local root="$1"
  local file="$2"
  local path
  for path in "${root}/templates/agents/subagents/${file}" "${root}/.cursor/agents/${file}"; do
    if [[ -f "$path" ]]; then
      grep -m1 -E '^[[:space:]]*name:[[:space:]]*' "$path" 2>/dev/null | sed -E 's/^[[:space:]]*name:[[:space:]]*([^[:space:]]+).*/\1/' | tr -d '\r'
      return
    fi
  done
}

agents_requested_from_prompt() {
  local prompt="$1"
  local root="$2"
  local -a out=()
  local name file invoke

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    out+=("$name")
  done < <(printf '%s' "$prompt" | grep -oE '@agent\([[:space:]]*[^)]+\)' | sed -E 's/@agent\([[:space:]]*([^)]+)[[:space:]]*\)/\1/' | tr -d '\r')

  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    invoke=$(agent_invoke_from_subagent_file "$root" "${file}.md")
    [[ -n "$invoke" ]] && out+=("$invoke")
  done < <(printf '%s' "$prompt" | grep -oiE 'subagents[/\\][a-zA-Z0-9_-]+\.md' | sed -E 's/.*[/\\]([a-zA-Z0-9_-]+)\.md/\1/i' | tr -d '\r')

  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if [[ "$file" =~ ^(AGENTS|AGENTS_USAGE)$ ]]; then
      continue
    fi
    invoke=$(agent_invoke_from_subagent_file "$root" "${file}.md")
    [[ -n "$invoke" ]] && out+=("$invoke")
  done < <(printf '%s' "$prompt" | grep -oiE '[/\\]agents[/\\][a-zA-Z0-9_-]+\.md' | sed -E 's/.*[/\\]([a-zA-Z0-9_-]+)\.md/\1/i' | tr -d '\r')

  if [[ ${#out[@]} -eq 0 ]]; then
    printf '[]'
    return
  fi
  printf '%s\n' "${out[@]}" | awk '!seen[$0]++' | jq -Rsc 'split("\n") | map(select(length > 0)) | sort'
}

routing_script_path() {
  local root="$1"
  for path in \
    "${root}/templates/commands/routing.py" \
    "${root}/.cursor/commands/routing.py"; do
    if [[ -f "$path" ]]; then
      printf '%s' "$path"
      return
    fi
  done
}

skills_matched_from_prompt() {
  local prompt="$1"
  local root="$2"
  local script py

  if [[ -z "$prompt" ]]; then
    printf '[]'
    return
  fi

  script=$(routing_script_path "$root")
  py=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)
  if [[ -z "$script" || -z "$py" ]]; then
    printf '[]'
    return
  fi

  "$py" "$script" skills-match --task "$prompt" 2>/dev/null || printf '[]'
}

append_hook_executed() {
  local ledger="$1"
  local entry="$2"
  echo "$ledger" | jq --arg e "$entry" '
    .hooks_executed = ((.hooks_executed // []) + [$e] | unique | sort)
  '
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
    model=$(echo "$raw" | jq -r '[.model, .model_name, .model_id, .subagent_model] | map(select(. != null and . != "")) | .[0] // empty')
    prompt=$(echo "$raw" | jq -r '[.prompt, .user_prompt, .content, .text, .input, .message] | map(select(. != null and . != "")) | .[0] // ""')
    agents_req=$(agents_requested_from_prompt "$prompt" "$project_root")
    skills_matched=$(skills_matched_from_prompt "$prompt" "$project_root")
    prompt_chars=${#prompt}
    tokens='null'
    if [[ "$prompt_chars" -gt 0 ]]; then
      est_in=$(( (prompt_chars + 3) / 4 ))
      tokens=$(jq -nc --argjson in "$est_in" --argjson pc "$prompt_chars" '{input_tokens: $in, total_tokens: $in, prompt_chars: $pc, estimated: true, source: "chars"}')
    fi
    ledger=$(echo "$raw" | jq -c \
      --argjson rules "$rules" \
      --argjson skills "$skills" \
      --argjson hooks "$hooks_cfg" \
      --argjson agents_req "$agents_req" \
      --argjson skills_matched "$skills_matched" \
      --arg model "$model" \
      --argjson tokens "$tokens" \
      --argjson prompt_chars "$prompt_chars" \
      --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
      '{
        ts: $ts,
        generation_id: (.generation_id // ""),
        conversation_id: (.conversation_id // ""),
        model: (if ($model | length) > 0 then $model else null end),
        tokens: (if $tokens == null then null else $tokens end),
        prompt_chars: (if $prompt_chars > 0 then $prompt_chars else null end),
        rules: $rules,
        skills_payload: $skills,
        skills_matched: $skills_matched,
        skills_read: [],
        agents_requested: $agents_req,
        subagents: [],
        hooks_configured: $hooks,
        hooks_executed: ["beforeSubmitPrompt:log-resource-usage.sh"],
        tracking_events: ["beforeSubmitPrompt"]
      }')
    write_active_ledger_atomic "$active_path" "$ledger"
    emit_allow "$event"
    ;;

  preToolUse)
    tool_name=$(echo "$raw" | jq -r '.tool_name // empty')
    if [[ "$tool_name" == "Read" ]]; then
      read_path=$(echo "$raw" | jq -r '.tool_input.path // .tool_input.target_file // empty')
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
          hooks_executed: [],
          tracking_events: []
        }')
      fi
      ledger=$(append_hook_executed "$ledger" "preToolUse:log-resource-usage.sh")
      if [[ -n "$read_path" ]]; then
        skill_name=$(skill_name_from_path "$read_path")
        if [[ -n "$skill_name" ]]; then
          ledger=$(echo "$ledger" | jq --arg s "$skill_name" '
            .skills_read = ((.skills_read // []) + [$s] | unique) |
            .ts = (now | todate)
          ')
          ledger=$(append_tracking_event "$ledger" "preToolUse:skill_read")
        fi
      fi
      ledger=$(echo "$ledger" | jq '.ts = (now | todate)')
      write_active_ledger_atomic "$active_path" "$ledger"
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
    ledger=$(append_hook_executed "$ledger" "subagentStart:log-resource-usage.sh")
    write_active_ledger_atomic "$active_path" "$ledger"
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
    ledger=$(append_hook_executed "$ledger" "subagentStop:log-resource-usage.sh")
    write_active_ledger_atomic "$active_path" "$ledger"
    ;;

  preCompact|afterAgentResponse)
    if [[ ! -f "$active_path" ]]; then
      ledger=$(echo "$raw" | jq -c '{
        ts: (now | todate),
        generation_id: (.generation_id // ""),
        conversation_id: (.conversation_id // ""),
        model: ([.model, .model_name, .subagent_model] | map(select(. != null and . != "")) | .[0] // null),
        tokens: null,
        rules: [],
        skills_payload: [],
        skills_read: [],
        subagents: [],
        tracking_events: []
      }')
      write_active_ledger_atomic "$active_path" "$ledger"
    fi
    ledger=$(cat "$active_path")
    model=$(echo "$raw" | jq -r '[.model, .model_name, .subagent_model] | map(select(. != null and . != "")) | .[0] // empty')
    token_patch=$(echo "$raw" | jq -c --arg ev "$event" '{
      input_tokens: (.usage.input_tokens // .usage.prompt_tokens // .input_tokens // .prompt_tokens // null),
      output_tokens: (.usage.output_tokens // .usage.completion_tokens // .output_tokens // .completion_tokens // null),
      total_tokens: (.usage.total_tokens // .total_tokens // null),
      context_tokens: .context_tokens,
      context_usage_percent: .context_usage_percent,
      context_window_size: .context_window_size,
      source: $ev
    } | with_entries(select(.value != null))')
    ledger=$(echo "$ledger" | jq --arg m "$model" --argjson patch "$token_patch" --arg ev "$event" '
      (if ($m | length) > 0 then .model = $m else . end) |
      (if ($patch | length) > 0 then .tokens = ((.tokens // {}) * $patch) else . end) |
      .tracking_events = ((.tracking_events // []) + [$ev] | unique) |
      .ts = (now | todate)
    ')
    ledger=$(append_hook_executed "$ledger" "${event}:log-resource-usage.sh")
    if [[ "$event" == "afterAgentResponse" ]]; then
      response=$(echo "$raw" | jq -r '[.text, .response, .content, .message] | map(select(. != null and . != "")) | .[0] // ""')
      response_chars=${#response}
      if [[ "$response_chars" -gt 0 ]]; then
        est_out=$(( (response_chars + 3) / 4 ))
        ledger=$(echo "$ledger" | jq --argjson rc "$response_chars" --argjson out "$est_out" '
          .response_chars = $rc |
          .tokens = ((.tokens // {}) * {
            output_tokens: $out,
            response_chars: $rc,
            estimated: true,
            source: "chars"
          }) |
          .tokens.total_tokens = ((.tokens.input_tokens // 0) + (.tokens.output_tokens // 0))
        ')
      fi
    fi
    write_active_ledger_atomic "$active_path" "$ledger"
    ;;

  stop)
    if [[ ! -f "$active_path" ]]; then
      exit 0
    fi
    ledger=$(cat "$active_path")
    status=$(echo "$raw" | jq -r '.status // empty')
    model=$(echo "$raw" | jq -r '[.model, .model_name, .subagent_model] | map(select(. != null and . != "")) | .[0] // empty')
    token_patch=$(echo "$raw" | jq -c '{
      input_tokens: (.usage.input_tokens // .usage.prompt_tokens // .input_tokens // .prompt_tokens // null),
      output_tokens: (.usage.output_tokens // .usage.completion_tokens // .output_tokens // .completion_tokens // null),
      total_tokens: (.usage.total_tokens // .total_tokens // null)
    } | with_entries(select(.value != null))')
    ledger=$(echo "$ledger" | jq --arg m "$model" --argjson patch "$token_patch" '
      (if ($m | length) > 0 then .model = $m else . end) |
      (if ($patch | length) > 0 then .tokens = ((.tokens // {}) * $patch | .source = "stop") else . end)
    ')
    summary=$(echo "$ledger" | jq -c \
      --arg st "$status" \
      --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
      '{
        ts: $ts,
        event: "resource_summary",
        generation_id: .generation_id,
        conversation_id: .conversation_id,
        model: .model,
        tokens: .tokens,
        prompt_chars: .prompt_chars,
        response_chars: .response_chars,
        status: $st,
        rules: (.rules // []),
        skills_payload: (.skills_payload // []),
        skills_matched: (.skills_matched // []),
        skills_read: (.skills_read // []),
        agents_requested: (.agents_requested // []),
        subagents: (.subagents // []),
        hooks_configured: (.hooks_configured // []),
        hooks_executed: (.hooks_executed // []),
        tracking_events: ((.tracking_events // []) + ["stop"] | unique)
      }')
    resources_log="${log_dir}/cursor-resources-$(date +%Y-%m-%d).jsonl"
    printf '%s\n' "$summary" >>"$resources_log"
    printf '%s\n' "$summary" | jq '.' >"${ledger_dir}/latest.json"
    ledger=$(append_tracking_event "$ledger" "stop")
    ledger=$(append_hook_executed "$ledger" "stop:log-resource-usage.sh")
    write_active_ledger_atomic "$active_path" "$ledger"
    ;;

  *)
    exit 0
    ;;
esac

exit 0
