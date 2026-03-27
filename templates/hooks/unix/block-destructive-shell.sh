#!/usr/bin/env bash
# Block destructive shell commands.
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

deny() {
  jq -nc '{continue:false,permission:"deny",user_message:"Blocked: destructive command not allowed.",agent_message:"Command blocked by hook. Use suggest-commands-dont-run-destructive: suggest the command for the user to run instead."}'
  exit 0
}

# Patterns mirror block-destructive-shell.ps1
if printf '%s\n' "$cmd" | grep -qE 'rm[[:space:]]+-rf[[:space:]]+/([[:space:]]|$)'; then deny; fi
if printf '%s\n' "$cmd" | grep -qE 'rm[[:space:]]+-rf[[:space:]]+\$'; then deny; fi
if printf '%s\n' "$cmd" | grep -qE ':[[:space:]]*\([[:space:]]*\)[[:space:]]*\{[[:space:]]*:[[:space:]]*\|'; then deny; fi
if printf '%s\n' "$cmd" | grep -qEi 'git[[:space:]]+reset[[:space:]]+--hard[[:space:]]+origin'; then deny; fi
if printf '%s\n' "$cmd" | grep -qEi 'DROP[[:space:]]+(TABLE|DATABASE)[[:space:]]+'; then deny; fi
if printf '%s\n' "$cmd" | grep -qEi 'DELETE[[:space:]]+FROM[[:space:]]+[[:alnum:]_]+[[:space:]]*;?[[:space:]]*$'; then deny; fi

printf '%s\n' '{"continue":true,"permission":"allow"}'
exit 0
