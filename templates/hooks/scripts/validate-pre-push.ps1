# Run tests before git push if project has pytest or npm test. Maps to: validate-pre-deploy
# Input (stdin): JSON with command, cwd, workspace_roots
# Skips if no test config found. Denies push if tests fail.

$ErrorActionPreference = "SilentlyContinue"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }
$payload = $raw | ConvertFrom-Json
$cmd = if ($payload.command) { $payload.command.Trim() } else { "" }
if ($cmd -notmatch '^\s*git\s+push\b') {
    $out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
    Write-Output $out
    exit 0
}

$roots = $payload.workspace_roots
$cwd = $payload.cwd
$root = if ($cwd) { $cwd } elseif ($roots) { $roots[0] } else { $null }
if (-not $root -or -not (Test-Path $root)) {
    $out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
    Write-Output $out
    exit 0
}

Push-Location $root
try {
    $ran = $false
    if (Test-Path "pyproject.toml") {
        poetry run pytest -q 2>$null
        $ran = $true
    }
    elseif (Test-Path "package.json") {
        $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
        if ($pkg.scripts.test) {
            npm test 2>$null
            $ran = $true
        }
    }
    if (-not $ran) {
        $out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
        Write-Output $out
        exit 0
    }
    if ($LASTEXITCODE -ne 0) {
        $out = @{
            continue = $false
            permission = "deny"
            user_message = "Tests failed. Fix before pushing."
            agent_message = "Run tests locally. Use validate-pre-deploy for full pre-push checklist."
        } | ConvertTo-Json -Compress
        Write-Output $out
        exit 0
    }
} finally { Pop-Location }

$out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
Write-Output $out
