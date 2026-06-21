# Redact sensitive file content before passing to model.
# Input (stdin): JSON with content, file_path, hook_event_name
# Output (stdout): single JSON line with permission (allow/deny); optional content (redacted).

. (Join-Path $PSScriptRoot "hook-common.ps1")

try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-ReadAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    $root = Get-ProjectRootFromPayload $payload
    $redacted = Invoke-RedactReadPayload -Raw $raw -ProjectRoot $root
    if ($redacted) {
        if ($redacted.content) {
            Write-ReadAllowWithContent "$($redacted.content)"
        } else {
            Write-ReadAllow
        }
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
    Write-HookError $_
    Write-ReadAllow
}

exit 0
