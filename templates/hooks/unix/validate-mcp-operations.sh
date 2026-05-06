#!/usr/bin/env bash
# Guard MCP tool execution: allow read-only, ask on risky operations.
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

server=$(echo "$raw" | jq -r '.server // .server_name // .mcp_server // ""')
tool=$(echo "$raw" | jq -r '.tool_name // .toolName // .name // .mcp_tool_name // ""')

if [[ -z "$tool" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

if [[ "$tool" == "mcp_auth" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

readonly_pattern='(^|[_-])(get|list|read|fetch|search|query|select|describe|show|view)($|[_-])'
risky_pattern='(^|[_-])(create|update|delete|insert|drop|truncate|alter|write|upsert|deploy|publish|push|merge|close|assign|comment|tag|release|apply)($|[_-])'
db_server_pattern='(sql|postgres|mysql|database|snowflake|bigquery|databricks)'

is_readonly=false
is_risky=false
is_db=false

if [[ "$tool" =~ $readonly_pattern ]]; then is_readonly=true; fi
if [[ "$tool" =~ $risky_pattern ]]; then is_risky=true; fi
if [[ "$server" =~ $db_server_pattern ]]; then is_db=true; fi

if [[ "$is_risky" == true && "$is_readonly" == false ]]; then
  risk_type="state-changing"
  if [[ "$is_db" == true ]]; then
    risk_type="DB-write or schema-change"
  fi
  jq -nc --arg t "$tool" --arg s "$server" --arg r "$risk_type" \
    '{continue:true,permission:"ask",user_message:("MCP tool \($t) on server \($s) looks \($r). Approve only if this action is explicitly requested."),agent_message:"Default policy: MCP operations should be read-only unless user explicitly asks for writes/deploy/publish changes."}'
  exit 0
fi

printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
