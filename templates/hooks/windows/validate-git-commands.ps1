# Validate git commit messages and block force-push on protected branches.
# Maps to: validate-git-commit, warn-force-push, prepare-atomic-commit
# Input (stdin): JSON with command, cwd, workspace_roots
# Output (stdout): JSON with continue, permission, user_message, agent_message (Cursor uses snake_case)

$ErrorActionPreference = "Stop"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }
$payload = $raw | ConvertFrom-Json
$cmd = if ($payload.command) { $payload.command.Trim() } else { "" }
$cwd = $payload.cwd
$roots = $payload.workspace_roots
$gitRoot = if ($cwd) { $cwd } elseif ($roots) { $roots[0] } else { $null }

function Deny {
    param([string]$userMsg, [string]$agentMsg)
    $out = @{ continue = $false; permission = "deny"; user_message = $userMsg; agent_message = $agentMsg } | ConvertTo-Json -Compress
    Write-Output $out
    exit 0
}

# --- git commit -m "msg" validation ---
if ($cmd -match 'git\s+commit\s+.*-m\s+["'']([^"'']+)["'']') {
    $msg = $matches[1]
    $firstLine = ($msg -split "`n")[0]
    if ($firstLine.Length -gt 72) {
        Deny "Commit message first line too long ($($firstLine.Length) > 72 chars)." "Use prepare-atomic-commit: keep first line <= 72 chars."
    }
    if ($firstLine.Length -lt 10) {
        Deny "Commit message too short. Use imperative mood (e.g. 'Add X', 'Fix Y')." "Use prepare-atomic-commit for message format."
    }
    # Conventional commit: type(scope): description (skip if .cursor/allow-non-conventional-commit exists)
    $skipConventional = $gitRoot -and (Test-Path (Join-Path $gitRoot ".cursor/allow-non-conventional-commit"))
    if (-not $skipConventional) {
        $conventional = '^(feat|fix|chore|docs|refactor|test|style|perf|build|ci)(\([a-z0-9-]+\))?!?: .+'
        if ($firstLine -notmatch $conventional) {
            Deny "Commit message should follow conventional format: type(scope): description (e.g. feat: add login). Create .cursor/allow-non-conventional-commit to skip." "Use prepare-atomic-commit for conventional commits."
        }
    }
}

# --- git push --force (without --force-with-lease) on protected branches ---
if ($cmd -match 'git\s+push\s+.*--force(?!-with-lease)') {
    if (-not $gitRoot -or -not (Test-Path (Join-Path $gitRoot ".git"))) {
        $out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
        Write-Output $out
        exit 0
    }
    Push-Location $gitRoot
    try {
        $branch = git branch --show-current 2>$null
        $protected = @("main", "master")
        if ($protected -contains $branch) {
            Deny "Force push to $branch is blocked. Use --force-with-lease if you must." "Use suggest-commands-dont-run-destructive: suggest the command for the user to run."
        }
    } finally { Pop-Location }
}

$out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
Write-Output $out
