# Block destructive shell commands.

. (Join-Path $PSScriptRoot "hook-common.ps1")

try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-ShellAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    $cmd = if ($payload -and $payload.command) { "$($payload.command)".Trim() } else { "" }

    $blocked = @(
        { $cmd -match 'rm\s+-rf\s+/' },
        { $cmd -match 'rm\s+-rf\s+\$' },
        { $cmd -match ':\s*\(\s*\)\s*\{\s*:\s*\|' },
        { $cmd -match 'git\s+reset\s+--hard\s+origin' },
        { $cmd -match 'DROP\s+(TABLE|DATABASE)\s+' },
        { $cmd -match 'DELETE\s+FROM\s+\w+\s*;?\s*$' }
    )

    foreach ($pred in $blocked) {
        if (& $pred) {
            Write-ShellDeny "Blocked: destructive command not allowed." "Command blocked by hook. Use suggest-commands-dont-run-destructive: suggest the command for the user to run instead."
            exit 0
        }
    }

    Write-ShellAllow
} catch {
    Write-HookError $_
    Write-ShellAllow
}

exit 0
