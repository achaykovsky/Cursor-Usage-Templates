# After edits under templates/, copy changed components into project .cursor/ for immediate try.
# Input (stdin): JSON with file_path, workspace_roots, hook_event_name

. (Join-Path $PSScriptRoot "hook-common.ps1")

$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        exit 0
    }

    $payload = Get-HookPayload $raw
    if (-not $payload) {
        exit 0
    }

    if ("$($payload.hook_event_name)" -ne "afterFileEdit") {
        exit 0
    }

    $path = $payload.file_path
    $roots = $payload.workspace_roots
    if (-not $path) {
        exit 0
    }
    if (-not (Test-Path $path) -and $roots -and $roots.Count -gt 0) {
        $path = Join-Path $roots[0] $path
    }
    if (-not (Test-Path $path)) {
        exit 0
    }
    $path = (Resolve-Path $path).Path

    if ($path -notmatch '[\\/]templates[\\/]') {
        exit 0
    }

    $root = $payload.cwd
    if (-not $root -and $roots -and $roots.Count -gt 0) {
        $root = "$($roots[0])"
    }
    if (-not $root -or -not (Test-Path $root)) {
        exit 0
    }

    $syncPy = Join-Path $root "templates\commands\sync-cursor.py"
    if (-not (Test-Path $syncPy)) {
        exit 0
    }

    $python = $null
    foreach ($name in @("python", "python3", "py")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            $python = $name
            break
        }
    }
    if (-not $python) {
        exit 0
    }

    $pyArgs = @($syncPy, "--project-root", $root, "--trigger-file", $path)
    if ($python -eq "py") {
        $pyArgs = @("-3", $syncPy, "--project-root", $root, "--trigger-file", $path)
    }

    & $python @pyArgs 2>$null | Out-Null
} catch {
    Write-HookError $_
} finally {
    Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
}

exit 0
