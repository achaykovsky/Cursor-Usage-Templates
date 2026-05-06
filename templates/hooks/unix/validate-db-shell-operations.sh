#!/usr/bin/env bash
# Guard risky database shell operations. Ask for confirmation or deny obviously destructive patterns.
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

cmd=$(echo "$raw" | jq -r '.command // ""' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if [[ -z "$cmd" ]]; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

db_context_pattern='(psql|mysql|mariadb|sqlite3|sqlcmd|mongosh|mongo|alembic|flyway|liquibase|dbmate|prisma|typeorm|knex|sequelize)'
if ! printf '%s\n' "$cmd" | grep -qiE "\\b${db_context_pattern}\\b" && ! printf '%s\n' "$cmd" | grep -qiE '\b(select|insert|update|delete|drop|truncate|alter|create[[:space:]]+table)\b'; then
  printf '%s\n' '{"continue":true,"permission":"allow"}'
  exit 0
fi

deny() {
  jq -nc '{continue:false,permission:"deny",user_message:"Blocked: destructive database operation detected.",agent_message:"DB safety hook blocked a destructive command. Ask the user explicitly and provide a safer plan (backup + rollback + scoped target)."}'
  exit 0
}

ask() {
  jq -nc '{continue:true,permission:"ask",user_message:"Database write/schema command detected. Confirm this action is explicitly requested and scoped to the intended environment.",agent_message:"DB safety hook: require explicit user approval for write/schema operations. Prefer read-only validation first."}'
  exit 0
}

if printf '%s\n' "$cmd" | grep -qiE '\bdrop[[:space:]]+database\b'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\btruncate[[:space:]]+table\b'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\bdrop[[:space:]]+table\b'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\bdelete[[:space:]]+from[[:space:]]+[[:alnum:]_]+[[:space:]]*;?[[:space:]]*$'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\balembic[[:space:]]+downgrade[[:space:]]+-1\b'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\bflyway[[:space:]]+clean\b'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\bliquibase[[:space:]]+rollback\b'; then deny; fi
if printf '%s\n' "$cmd" | grep -qiE '\bprisma[[:space:]]+migrate[[:space:]]+reset\b'; then deny; fi

if printf '%s\n' "$cmd" | grep -qiE '\bdelete[[:space:]]+from\b'; then ask; fi
if printf '%s\n' "$cmd" | grep -qiE '\bupdate[[:space:]]+[[:alnum:]_]+[[:space:]]+set\b'; then ask; fi
if printf '%s\n' "$cmd" | grep -qiE '\binsert[[:space:]]+into\b'; then ask; fi
if printf '%s\n' "$cmd" | grep -qiE '\balter[[:space:]]+table\b'; then ask; fi
if printf '%s\n' "$cmd" | grep -qiE '\bcreate[[:space:]]+table\b'; then ask; fi
if printf '%s\n' "$cmd" | grep -qiE '\bmigrate\b'; then ask; fi
if printf '%s\n' "$cmd" | grep -qiE '\bapply\b'; then ask; fi

printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
