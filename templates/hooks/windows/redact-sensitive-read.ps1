# Redact or block sensitive file content before passing to model. Maps to: redact-sensitive-in-output
# Input (stdin): JSON with content, file_path, hook_event_name
# Output (stdout): JSON with permission (allow/deny). If allow, optionally content (redacted).

$ErrorActionPreference = "Stop"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Write-Output '{"permission":"allow"}'; exit 0 }
$payload = $raw | ConvertFrom-Json
$content = $payload.content
$path = $payload.file_path

$sensitivePatterns = @(
    '\.env$', '\.env\.', '\.pem$', '\.key$', 'secrets\.', 'credentials\.',
    'config\.local\.', '\.secret', 'id_rsa', 'id_ed25519'
)

$isSensitive = $false
foreach ($p in $sensitivePatterns) {
    if ($path -match $p) { $isSensitive = $true; break }
}

if ($isSensitive) {
    # Redact: replace values that look like secrets with placeholder
    $redacted = $content -replace '(?m)^([^#=]+)=(.*)$', '$1=***REDACTED***'
    $redacted = $redacted -replace '(-----BEGIN[^\r\n]+-----)[\s\S]*?(-----END[^\r\n]+-----)', '$1 ***REDACTED*** $2'
    $out = @{
        permission = "allow"
        content = $redacted
    } | ConvertTo-Json -Compress
    Write-Output $out
} else {
    $out = @{ permission = "allow" } | ConvertTo-Json -Compress
    Write-Output $out
}
