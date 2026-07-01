# Validate bot manifest JSON under templates/ai-runtime/bots after edits.
# Input (stdin): JSON with file_path, hook_event_name
# Output: silent on success; Hooks channel warning on validation failure (advisory)

. (Join-Path $PSScriptRoot "hook-common.ps1")

$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

    $payload = Get-HookPayload $raw
    if (-not $payload) { exit 0 }

    $hookEvent = "$($payload.hook_event_name)"
    if ($hookEvent -ne "afterFileEdit") { exit 0 }

    $filePath = if ($null -ne $payload.file_path) { "$($payload.file_path)" } else { "" }
    if (-not $filePath -match '(?i)templates[/\\]ai-runtime[/\\]bots[/\\].*\.json$') { exit 0 }
    if ($filePath -match '(?i)manifest\.schema\.json$') { exit 0 }

    $root = Get-ProjectRootFromPayload $payload
    if (-not $root) { exit 0 }

    $validator = Join-Path $root "templates\ai-runtime\validate_bot_runtime.py"
    if (-not (Test-Path -LiteralPath $validator)) { exit 0 }

    $py = Get-PythonExecutable
    if (-not $py) { exit 0 }

    $fullPath = if ([System.IO.Path]::IsPathRooted($filePath)) { $filePath } else { Join-Path $root $filePath }
    if (-not (Test-Path -LiteralPath $fullPath)) { exit 0 }

    $stderr = & $py $validator manifest $fullPath 2>&1
    if ($LASTEXITCODE -ne 0) {
        $msg = ($stderr | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "manifest validation failed" }
        Write-HookError "validate-bot-manifest: $msg"
    }
} catch {
    if (Get-Command Write-HookError -ErrorAction SilentlyContinue) {
        Write-HookError $_
    }
} finally {
    if (Get-Command Register-HookExecution -ErrorAction SilentlyContinue) {
        Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
    }
}

exit 0
