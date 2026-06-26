# Run tests before git push when pytest/npm test is configured (policy engine).

. (Join-Path $PSScriptRoot "hook-common.ps1")

$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-ShellAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    $root = Get-ProjectRootFromPayload $payload
    $result = Invoke-HookPolicy -Domain "pre-push" -Raw $raw -ProjectRoot $root
    Emit-HookPolicyResult $result
} catch {
    Write-HookError $_
    Write-ShellAllow
} finally {
    Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
}

exit 0
