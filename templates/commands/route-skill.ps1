param(
    [Parameter(Mandatory = $true)]
    [string] $Task,
    [string] $Phase = ""
)

$ErrorActionPreference = "Stop"

if ($args -contains "-h" -or $args -contains "--help") {
    . (Join-Path $PSScriptRoot "_command-common.ps1")
    Show-RoutingHelp "route-skill.ps1"
    exit 0
}

. (Join-Path $PSScriptRoot "_command-common.ps1")

$pyArgs = @("skill", "--task", $Task)
if ($Phase) { $pyArgs += @("--phase", $Phase) }
Invoke-CommandsPython "routing.py" $pyArgs
