#!/usr/bin/env bash
# Log prompt-level context for beforeSubmitPrompt.
# Captures: timestamp, prompt, observed skill/rule fields, and predicted fallback.

set -euo pipefail

predict_skills() {
  local p
  p=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  local -a out=()
  [[ "$p" =~ fastapi|flask|endpoint|openapi|swagger|api ]] && out+=("api-workflows/implement-or-extend-api-surface")
  [[ "$p" =~ version|deprecat|backward|breaking\ change ]] && out+=("api-workflows/check-api-backward-compatibility")
  [[ "$p" =~ bug|broken|fix|error|exception|failing ]] && out+=("code-workflows/fix-bug-systematically")
  [[ "$p" =~ refactor|cleanup|rename ]] && out+=("code-workflows/refactor-safely")
  [[ "$p" =~ test|pytest|coverage|assert ]] && out+=("testing-workflows/add-tests-for-change")
  [[ "$p" =~ security|secret|owasp|xss|sql\ injection|auth ]] && out+=("security-workflows/security-scan-changes")
  [[ "$p" =~ deploy|release|pipeline|ci/cd|terraform|cloudformation ]] && out+=("devops-workflows/implement-ci-cd-pipeline")
  [[ "$p" =~ doc|readme|adr|documentation ]] && out+=("docs-workflows/keep-docs-in-sync-with-code")
  if ((${#out[@]} == 0)); then
    printf '[]'
  else
    printf '%s\n' "${out[@]}" | jq -Rsc 'split("\n") | map(select(length > 0)) | unique'
  fi
}

predict_rules() {
  local p
  p=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  local -a out=("security.mdc" "token-efficiency.mdc" "ai-guardrails.mdc")
  [[ "$p" =~ python|pytest|poetry|fastapi|django ]] && out+=("python-backend.mdc")
  [[ "$p" =~ (^|[[:space:]])go($|[[:space:]])|golang ]] && out+=("go-backend.mdc")
  [[ "$p" =~ react|tsx|frontend|ui|ux|css ]] && out+=("frontend.mdc")
  [[ "$p" =~ api|openapi|endpoint|swagger ]] && out+=("api-contract.mdc")
  [[ "$p" =~ test|coverage|assert ]] && out+=("testing.mdc")
  [[ "$p" =~ perf|latency|optimi ]] && out+=("performance.mdc")
  [[ "$p" =~ doc|readme|adr|markdown ]] && out+=("documentation.mdc")
  printf '%s\n' "${out[@]}" | jq -Rsc 'split("\n") | map(select(length > 0)) | unique'
}

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
if [[ -n "$event" && "$event" != "beforeSubmitPrompt" ]]; then
  exit 0
fi

parse_error=""
if ! echo "$raw" | jq empty 2>/dev/null; then
  parse_error="invalid json"
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
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

log_dir="${project_root}/.cursor/logs"
mkdir -p "$log_dir"
log_file="${log_dir}/cursor-prompt-context-$(date +%Y-%m-%d).jsonl"

prompt=$(echo "$raw" | jq -r '
  def first_str($keys):
    reduce $keys[] as $k (""; if length > 0 then . else (.[$k] // "" | if type == "string" then . else tostring end) end);
  first_str(["prompt","user_prompt","content","text","input","message"])
')
if [[ ${#prompt} -gt 50000 ]]; then
  prompt="${prompt:0:50000}...[truncated]"
fi

skills=$(echo "$raw" | jq -c '
  def as_names:
    if . == null then []
    elif type == "string" then (if length > 0 then [.] else [] end)
    elif type == "array" then
      map(if type == "string" then . elif type == "object" then (.name // .id // tostring) else tostring end)
      | map(select(length > 0)) | unique
    else [] end;
  def first_non_empty($obj; $keys):
    reduce $keys[] as $k ([]; if length > 0 then . else (($obj[$k] // null) | as_names) end);
  first_non_empty(.; ["skills","used_skills","applied_skills","matched_skills","selected_skills","skill_names"])
')

rules=$(echo "$raw" | jq -c '
  def as_names:
    if . == null then []
    elif type == "string" then (if length > 0 then [.] else [] end)
    elif type == "array" then
      map(if type == "string" then . elif type == "object" then (.name // .id // tostring) else tostring end)
      | map(select(length > 0)) | unique
    else [] end;
  def first_non_empty($obj; $keys):
    reduce $keys[] as $k ([]; if length > 0 then . else (($obj[$k] // null) | as_names) end);
  first_non_empty(.; ["rules","used_rules","applied_rules","matched_rules","active_rules","rule_names"])
')

predicted_skills='[]'
predicted_rules='[]'
if [[ "$skills" == "[]" ]]; then
  predicted_skills=$(predict_skills "$prompt")
fi
if [[ "$rules" == "[]" ]]; then
  predicted_rules=$(predict_rules "$prompt")
fi

payload_keys=$(echo "$raw" | jq -c 'keys | sort')
payload_key_count=$(echo "$payload_keys" | jq 'length')
has_payload_json=$([[ -z "$parse_error" ]] && echo true || echo false)
prompt_field_found=$([[ -n "$prompt" ]] && echo true || echo false)

line=$(jq -nc \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --arg event "${event:-beforeSubmitPrompt}" \
  --arg conversation_id "$(echo "$raw" | jq -r '.conversation_id // empty')" \
  --arg generation_id "$(echo "$raw" | jq -r '.generation_id // empty')" \
  --arg prompt "$prompt" \
  --argjson skills "$skills" \
  --argjson rules "$rules" \
  --argjson predicted_skills "$predicted_skills" \
  --argjson predicted_rules "$predicted_rules" \
  --argjson has_payload_json "$has_payload_json" \
  --arg parse_error "$parse_error" \
  --argjson payload_key_count "$payload_key_count" \
  --argjson payload_keys "$payload_keys" \
  --argjson prompt_field_found "$prompt_field_found" \
  '{
    ts: $ts,
    event: $event,
    conversation_id: (if ($conversation_id | length) > 0 then $conversation_id else null end),
    generation_id: (if ($generation_id | length) > 0 then $generation_id else null end),
    prompt: $prompt,
    skills: $skills,
    rules: $rules,
    predicted_skills: $predicted_skills,
    predicted_rules: $predicted_rules,
    source: {
      has_payload_json: $has_payload_json,
      parse_error: (if ($parse_error | length) > 0 then $parse_error else null end),
      payload_key_count: $payload_key_count,
      payload_keys: $payload_keys,
      prompt_field_found: $prompt_field_found
    }
  }')

printf '%s\n' "$line" >>"$log_file"
printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
