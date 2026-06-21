# Log Cursor activity. beforeShellExecution must emit JSON on stdout.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$needsShellJson = $false
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        exit 0
    }

    $payload = Get-HookPayload $raw
    $hookEvent = if ($payload) { "$($payload.hook_event_name)" } else { "" }
    $needsShellJson = ($hookEvent -eq "beforeShellExecution")

    $projectRoot = Get-ProjectRootFromPayload $payload
    if (-not $projectRoot) { exit 0 }

    $logDir = Join-Path (Join-Path $projectRoot ".cursor") "logs"
    $null = New-Item -ItemType Directory -Path $logDir -Force
    $logFile = Join-Path $logDir ("cursor-activity-{0:yyyy-MM-dd}.jsonl" -f (Get-Date))

    $line = $null
    $py = Get-PythonExecutable
    $activityScript = Get-CursorActivityScript $projectRoot
    if ($py -and $activityScript) {
        try {
            $line = $raw | & $py $activityScript normalize
        } catch {
            Write-HookError $_
        }
    }

    if ([string]::IsNullOrWhiteSpace($line)) {
        $entry = @{}
        if ($payload) {
            if ($payload.file_path -and $payload.edits) { $entry["event"] = "afterFileEdit" }
            elseif ($payload.prompt) { $entry["event"] = "beforeSubmitPrompt" }
            elseif ($payload.command) { $entry["event"] = "beforeShellExecution" }
            elseif ($payload.status) { $entry["event"] = "stop" }
            else { $entry["event"] = if ($hookEvent) { $hookEvent } else { "unknown" } }

            foreach ($key in @("conversation_id", "generation_id", "prompt", "file_path", "command", "cwd", "status")) {
                if ($null -ne $payload.$key) { $entry[$key] = $payload.$key }
            }
        }
        $entry["ts"] = (Get-Date).ToString("o")
        $line = $entry | ConvertTo-Json -Compress -Depth 10
    }

    Add-Content -Path $logFile -Value $line.Trim() -Encoding UTF8
} catch {
    Write-HookError $_
} finally {
    if ($needsShellJson) {
        Write-ShellAllow
    }
}

exit 0
