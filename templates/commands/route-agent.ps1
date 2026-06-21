param(
    [Parameter(Mandatory = $true)]
    [string] $Task
)

$ErrorActionPreference = "Stop"

if ($args -contains "-h" -or $args -contains "--help") {
    . (Join-Path $PSScriptRoot "_command-common.ps1")
    Show-RoutingHelp "route-agent.ps1"
    exit 0
}

. (Join-Path $PSScriptRoot "_command-common.ps1")
Invoke-CommandsPython "routing.py" @("agent", "--task", $Task)
