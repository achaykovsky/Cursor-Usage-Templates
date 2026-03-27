# Sync Cursor config — delegates to sync-cursor.py (cross-platform).
# Requires: Python 3.7+ on PATH (python or python3).

param(
    [string] $ProjectRoot = "",
    [ValidateSet("TemplatesToLocal", "ToGlobal", "FromGlobal")]
    [string] $Mode = "TemplatesToLocal",
    [ValidateSet("auto", "windows", "unix")]
    [string] $HooksVariant = "auto"
)

$ErrorActionPreference = "Stop"

$python = $null
foreach ($name in @("python", "python3")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        $python = $name
        break
    }
}

if (-not $python) {
    Write-Error "Python 3 not found on PATH. Install Python 3 or run: python templates/commands/sync-cursor.py --help"
    exit 1
}

$script = Join-Path $PSScriptRoot "sync-cursor.py"
if (-not (Test-Path $script)) {
    Write-Error "Missing $script"
    exit 1
}

$pyArgs = @($script, "--mode", $Mode, "--hooks-variant", $HooksVariant)
if ($ProjectRoot) {
    $pyArgs += @("--project-root", $ProjectRoot)
}

& $python @pyArgs
exit $LASTEXITCODE
