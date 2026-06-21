# Shared helpers for templates/commands PowerShell entry points.

function Get-CommandsPython {
    foreach ($name in @("python", "python3", "py")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function Invoke-CommandsPython([string]$ScriptName, [string[]]$PyArgs) {
    $python = Get-CommandsPython
    if (-not $python) {
        Write-Error "Python 3 not found on PATH. Install Python 3 or run the .py script directly."
        exit 1
    }
    $script = Join-Path $PSScriptRoot $ScriptName
    if (-not (Test-Path -LiteralPath $script)) {
        Write-Error "Missing $script"
        exit 1
    }
    & $python $script @PyArgs
    exit $LASTEXITCODE
}

function Show-RoutingHelp([string]$Name) {
    @"
$Name — deterministic routing (keyword heuristics)

Usage examples:
  .\templates\commands\$Name.ps1 -Task "fix auth bug in API"
  .\templates\commands\$Name.ps1 --help

Delegates to routing.py. See templates/commands/README.md.
"@
}
