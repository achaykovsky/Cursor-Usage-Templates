# Query cursor-activity JSONL logs grouped by generation_id.

param(
    [string] $Date = "",
    [string] $GenerationId = "",
    [string] $ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

if ($args -contains "-h" -or $args -contains "--help" -or $args -contains "/?") {
    @"
query-cursor-logs.ps1 — summarize prompt → files → commands → status

Usage:
  .\templates\commands\query-cursor-logs.ps1 -Date 2026-02-25
  .\templates\commands\query-cursor-logs.ps1 -GenerationId <id>
  .\templates\commands\query-cursor-logs.ps1 -ProjectRoot C:\path\to\project

Reads .cursor/logs/cursor-activity-YYYY-MM-DD.jsonl
"@
    exit 0
}

. (Join-Path $PSScriptRoot "_command-common.ps1")

if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}

$pyArgs = @("query", "--project-root", $ProjectRoot)
if ($Date) { $pyArgs += @("--date", $Date) }
if ($GenerationId) { $pyArgs += @("--generation-id", $GenerationId) }

Invoke-CommandsPython "cursor_activity.py" $pyArgs
