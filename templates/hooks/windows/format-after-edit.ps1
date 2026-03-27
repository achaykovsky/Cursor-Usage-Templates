# Run formatter on edited file. Saves tokens—agent doesn't need to format.
# Maps to: code quality enforcement. Input: file_path, edits. Informational only (no output to agent).

$ErrorActionPreference = "SilentlyContinue"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
$payload = $raw | ConvertFrom-Json
$path = $payload.file_path
$roots = $payload.workspace_roots
if (-not $path) { exit 0 }
if (-not (Test-Path $path) -and $roots) {
    $path = Join-Path $roots[0] $path
}
if (-not (Test-Path $path)) { exit 0 }
$path = (Resolve-Path $path).Path

$ext = [System.IO.Path]::GetExtension($path)
$formatter = $null

switch -Regex ($ext) {
    '\.py$' { if (Get-Command black -ErrorAction SilentlyContinue) { $formatter = "black" } }
    '\.(ts|tsx|js|jsx|json|css|md)$' { if (Get-Command npx -ErrorAction SilentlyContinue) { $formatter = "npx prettier --write" } }
    '\.go$' { if (Get-Command gofmt -ErrorAction SilentlyContinue) { $formatter = "gofmt -w" } }
}

if ($formatter) {
    $dir = Split-Path -Parent $path
    $fname = Split-Path -Leaf $path
    Push-Location $dir
    try {
        if ($formatter -eq "black") { & black $fname 2>$null }
        elseif ($formatter -match "prettier") { & npx prettier --write $fname 2>$null }
        elseif ($formatter -match "gofmt") { & gofmt -w $fname 2>$null }
    } finally { Pop-Location }
}
exit 0
