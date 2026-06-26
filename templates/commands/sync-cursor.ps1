# Sync Cursor config — delegates to sync-cursor.py (cross-platform).
# Requires: Python 3.10+ on PATH (python or python3).

param(
    [string] $ProjectRoot = "",
    [ValidateSet("TemplatesToLocal", "TemplatesToGlobal", "FromGlobal")]
    [string] $Mode = "TemplatesToLocal",
    [ValidateSet("auto", "windows", "unix")]
    [string] $HooksVariant = "auto",
    [string] $Components = ""
)

$ErrorActionPreference = "Stop"

# When called from a central templates repo, default the target project to the
# caller's current directory so the command works globally in any project.
if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}

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
if ($Components) {
    $pyArgs += @("--components", $Components)
}
if ($ProjectRoot) {
    $pyArgs += @("--project-root", $ProjectRoot)
}

& $python @pyArgs
exit $LASTEXITCODE
