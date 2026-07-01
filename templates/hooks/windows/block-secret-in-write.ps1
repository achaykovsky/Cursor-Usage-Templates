# Block Write/Edit when content contains hardcoded secrets.
# preToolUse matcher: Write

. (Join-Path $PSScriptRoot "hook-common.ps1")

$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-PreToolUseAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    if (-not $payload) {
        Write-PreToolUseAllow
        exit 0
    }

    if ("$($payload.hook_event_name)" -ne "preToolUse") {
        exit 0
    }

    $root = Get-ProjectRootFromPayload $payload
    $py = Get-PythonExecutable
    $scanner = Join-Path (Split-Path $PSScriptRoot -Parent) "policy\scan_write_content.py"
    if (-not $py -or -not (Test-Path -LiteralPath $scanner)) {
        Write-PreToolUseAllow
        exit 0
    }

    $out = $raw | & $py $scanner tool-payload 2>$null
    if ([string]::IsNullOrWhiteSpace($out)) {
        Write-PreToolUseAllow
        exit 0
    }

    $parsed = $out | ConvertFrom-Json
    $issues = @($parsed.issues)
    if ($issues.Count -gt 0) {
        $list = ($issues | Select-Object -First 3) -join ", "
        Write-HookJson @{
            permission    = "deny"
            user_message  = "Write blocked: possible secret in content ($list). Use env vars or placeholders."
            agent_message = "Remove hardcoded secrets; reference environment variable names only."
        }
        exit 0
    }

    Write-PreToolUseAllow
} catch {
    Write-HookError $_
    Write-PreToolUseAllow
} finally {
    Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
}

exit 0
