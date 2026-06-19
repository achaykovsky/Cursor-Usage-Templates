# Run tests before git push when pytest/npm test is configured.

. (Join-Path $PSScriptRoot "hook-common.ps1")

try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-ShellAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    $cmd = if ($payload -and $payload.command) { "$($payload.command)".Trim() } else { "" }
    if ($cmd -notmatch '^\s*git\s+push\b') {
        Write-ShellAllow
        exit 0
    }

    $roots = if ($payload) { $payload.workspace_roots } else { $null }
    $cwd = if ($payload) { $payload.cwd } else { $null }
    $root = if ($cwd) { "$cwd" } elseif ($roots -and $roots.Count -gt 0) { "$($roots[0])" } else { $null }
    if (-not $root -or -not (Test-Path $root)) {
        Write-ShellAllow
        exit 0
    }

    Push-Location $root
    try {
        $ran = $false
        if (Test-Path "pyproject.toml") {
            if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
                Write-ShellAllow
                exit 0
            }
            poetry run pytest -q 2>$null
            $ran = $true
        } elseif (Test-Path "package.json") {
            $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
            if ($pkg.scripts.test) {
                npm test 2>$null
                $ran = $true
            }
        }
        if (-not $ran) {
            Write-ShellAllow
            exit 0
        }
        if ($LASTEXITCODE -ne 0) {
            Write-ShellDeny "Tests failed. Fix before pushing." "Run tests locally. Use validate-pre-deploy for full pre-push checklist."
            exit 0
        }
    } finally {
        Pop-Location
    }

    Write-ShellAllow
} catch {
    Write-HookError $_
    Write-ShellAllow
}

exit 0
