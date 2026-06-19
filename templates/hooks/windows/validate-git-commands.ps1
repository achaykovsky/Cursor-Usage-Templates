# Validate git commands (policy engine).

. (Join-Path $PSScriptRoot "hook-common.ps1")

try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-ShellAllow
        exit 0
    }
    $payload = Get-HookPayload $raw
    $root = Get-ProjectRootFromPayload $payload
    $result = Invoke-HookPolicy -Domain "shell-git" -Raw $raw -ProjectRoot $root
    Emit-HookPolicyResult $result
} catch {
    Write-HookError $_
    Write-ShellAllow
}

exit 0
