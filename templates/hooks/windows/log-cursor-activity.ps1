# Log Cursor activity: prompts, edits, shell commands, session end.
# Writes to project/.cursor/logs/cursor-activity-YYYY-MM-DD.jsonl (never ~/.cursor)
# Note: Hooks do not receive LLM responses—only user prompts, edits, commands, and session status.

$ErrorActionPreference = "SilentlyContinue"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }
$payload = $raw | ConvertFrom-Json
$event = $payload.hook_event_name

# Log dir: always project/.cursor/logs (never ~/.cursor)
$roots = $payload.workspace_roots
$projectRoot = if ($roots -and $roots.Count -gt 0) {
    $roots[0]
} else {
    # Fallback: git root from cwd (payload.cwd or current dir)
    $startDir = if ($payload.cwd) { $payload.cwd } else { (Get-Location).Path }
    $gitRoot = & git -C $startDir rev-parse --show-toplevel 2>$null
    if ($gitRoot) { $gitRoot } else { $null }
}
if (-not $projectRoot) { exit 0 }
$logDir = Join-Path $projectRoot ".cursor"
$logDir = Join-Path $logDir "logs"
$null = New-Item -ItemType Directory -Path $logDir -Force
$logFile = Join-Path $logDir ("cursor-activity-{0:yyyy-MM-dd}.jsonl" -f (Get-Date))

$entry = @{}
$payload.PSObject.Properties | ForEach-Object { $entry[$_.Name] = $_.Value }
$entry["ts"] = (Get-Date).ToString("o")
$entry["event"] = $event

# Truncate very large fields to avoid huge log files
$maxLen = 50000
foreach ($key in @("content", "prompt")) {
    if ($entry[$key] -and $entry[$key].Length -gt $maxLen) {
        $entry[$key] = $entry[$key].Substring(0, $maxLen) + "...[truncated]"
    }
}
if ($entry.edits) {
    foreach ($e in $entry.edits) {
        if ($e.old_string -and $e.old_string.Length -gt $maxLen) { $e.old_string = $e.old_string.Substring(0, $maxLen) + "...[truncated]" }
        if ($e.new_string -and $e.new_string.Length -gt $maxLen) { $e.new_string = $e.new_string.Substring(0, $maxLen) + "...[truncated]" }
    }
}

$line = $entry | ConvertTo-Json -Compress -Depth 10
Add-Content -Path $logFile -Value $line -Encoding UTF8

# beforeShellExecution: pass through so block-destructive-shell can run
if ($event -eq "beforeShellExecution") {
    $out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
    Write-Output $out
}
exit 0
