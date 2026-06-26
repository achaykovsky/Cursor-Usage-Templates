# Redact sensitive file content before passing to model.
# Input (stdin): JSON with content, file_path, hook_event_name
# Output (stdout): single JSON line with permission (allow/deny); optional content (redacted).

$payload = $null
try {
    . (Join-Path $PSScriptRoot "hook-common.ps1")

    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-ReadAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    $root = Get-ProjectRootFromPayload $payload
    $redactedJson = Invoke-RedactReadPayloadJson -Raw $raw -ProjectRoot $root
    if ($redactedJson) {
        [Console]::Out.WriteLine($redactedJson)
        exit 0
    }

    # Fallback when Python/redact_sensitive.py is unavailable — path-only env/PEM redaction.
    $content = if ($null -ne $payload -and $null -ne $payload.content) { "$($payload.content)" } else { "" }
    $path = if ($null -ne $payload -and $null -ne $payload.file_path) { "$($payload.file_path)" } else { "" }

    $sensitivePatterns = @(
        '\.env$', '\.env\.', '\.pem$', '\.key$', '\.pfx$', '\.p12$',
        'secrets\.', 'credentials\.', 'config\.local\.', '\.secret',
        'id_rsa', 'id_ed25519', 'service-account', 'token\.json'
    )

    $isSensitive = $false
    foreach ($p in $sensitivePatterns) {
        if ($path -match $p) { $isSensitive = $true; break }
    }

    if ($isSensitive) {
        $redactedContent = $content -replace '(?m)^([^#=]+)=(.*)$', '$1=***REDACTED***'
        $redactedContent = $redactedContent -replace '(-----BEGIN[^\r\n]+-----)[\s\S]*?(-----END[^\r\n]+-----)', '$1 ***REDACTED*** $2'
        Write-ReadAllowWithContent $redactedContent
    } else {
        Write-ReadAllow
    }
} catch {
    if (Get-Command Write-HookError -ErrorAction SilentlyContinue) {
        Write-HookError $_
    }
    [Console]::Out.WriteLine('{"permission":"allow"}')
} finally {
    if (Get-Command Register-HookExecution -ErrorAction SilentlyContinue) {
        Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
    }
}

exit 0
