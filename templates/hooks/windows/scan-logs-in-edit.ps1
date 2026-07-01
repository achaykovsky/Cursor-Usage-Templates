# Warn when edits introduce secrets in log statements (advisory after edit).

. (Join-Path $PSScriptRoot "hook-common.ps1")

$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

    $payload = Get-HookPayload $raw
    if (-not $payload) { exit 0 }

    if ("$($payload.hook_event_name)" -ne "afterFileEdit") { exit 0 }

    $filePath = if ($null -ne $payload.file_path) { "$($payload.file_path)" } else { "" }
    $isCorpusEdit = $filePath -match '(?i)(templates[/\\]ai-runtime[/\\]rag[/\\].*\.json$|[/\\]rag[/\\].*corpus.*\.json$)'
    if ($filePath -match '(?i)\.schema\.json$') { $isCorpusEdit = $false }

    $py = Get-PythonExecutable
    $scanner = Join-Path (Split-Path $PSScriptRoot -Parent) "policy\scan_write_content.py"
    if (-not $py -or -not (Test-Path -LiteralPath $scanner)) { exit 0 }

    # Single Python invocation for all edits — avoids per-edit process spawn overhead.
    $scanMode = if ($isCorpusEdit) { "corpus-pii-scan" } else { "log-scan" }
    $out = $raw | & $py $scanner edit-payload $scanMode 2>$null
    $issues = @()
    if (-not [string]::IsNullOrWhiteSpace($out)) {
        $parsed = $out | ConvertFrom-Json
        $issues = @($parsed.issues)
    }

    if ($issues.Count -gt 0) {
        $list = ($issues | Select-Object -First 3) -join ", "
        if ($isCorpusEdit) {
            Write-HookError "scan-logs-in-edit: possible PII in RAG corpus ($list). Review sensitive-data-handling and rag-pipeline rules."
        } else {
            Write-HookError "scan-logs-in-edit: possible secret in log statement ($list). Review sensitive-data-handling skill."
        }
    }
} catch {
    if (Get-Command Write-HookError -ErrorAction SilentlyContinue) {
        Write-HookError $_
    }
} finally {
    Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
}

exit 0
