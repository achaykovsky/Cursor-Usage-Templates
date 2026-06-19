# Log Cursor activity. beforeShellExecution must emit JSON on stdout.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$needsShellJson = $false
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        exit 0
    }

    $payload = Get-HookPayload $raw
    $event = if ($payload) { "$($payload.hook_event_name)" } else { "" }
    $needsShellJson = ($event -eq "beforeShellExecution")

    $projectRoot = Get-ProjectRootFromPayload $payload
    if (-not $projectRoot) { exit 0 }

    $logDir = Join-Path (Join-Path $projectRoot ".cursor") "logs"
    $null = New-Item -ItemType Directory -Path $logDir -Force
    $logFile = Join-Path $logDir ("cursor-activity-{0:yyyy-MM-dd}.jsonl" -f (Get-Date))

    $entry = @{}
    if ($payload) {
        $payload.PSObject.Properties | ForEach-Object { $entry[$_.Name] = $_.Value }
    }
    $entry["ts"] = (Get-Date).ToString("o")
    $entry["event"] = $event

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
} catch {
    Write-HookError $_
} finally {
    if ($needsShellJson) {
        Write-ShellAllow
    }
}

exit 0
