# Validate RAG corpus and golden eval JSON after edits.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

    $payload = Get-HookPayload $raw
    if (-not $payload) { exit 0 }

    if ("$($payload.hook_event_name)" -ne "afterFileEdit") { exit 0 }

    $filePath = if ($null -ne $payload.file_path) { "$($payload.file_path)" } else { "" }
    if ([string]::IsNullOrWhiteSpace($filePath)) { exit 0 }

    $isCorpus = $filePath -match '(?i)(templates[/\\]ai-runtime[/\\]rag[/\\].*\.json$|[/\\]rag[/\\].*corpus.*\.json$)'
    $isGolden = $filePath -match '(?i)(templates[/\\]ai-runtime[/\\]rag[/\\]eval[/\\].*\.json$|[/\\]rag[/\\]eval[/\\].*\.json$)'
    if (-not $isCorpus -and -not $isGolden) { exit 0 }
    if ($filePath -match '(?i)(\.schema\.json$|golden-questions\.schema\.json$)') { exit 0 }

    $root = Get-ProjectRootFromPayload $payload
    if (-not $root) { exit 0 }

    $validator = Join-Path $root "templates\ai-runtime\validate_bot_runtime.py"
    if (-not (Test-Path -LiteralPath $validator)) { exit 0 }

    $py = Get-PythonExecutable
    if (-not $py) { exit 0 }

    $fullPath = if ([System.IO.Path]::IsPathRooted($filePath)) { $filePath } else { Join-Path $root $filePath }
    if (-not (Test-Path -LiteralPath $fullPath)) { exit 0 }

    $kind = if ($isGolden) { "golden" } else { "corpus" }
    $stderr = & $py $validator $kind $fullPath 2>&1
    if ($LASTEXITCODE -ne 0) {
        $msg = ($stderr | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($msg)) { $msg = "RAG $kind validation failed" }
        Write-HookError "validate-rag-artifacts: $msg"
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
