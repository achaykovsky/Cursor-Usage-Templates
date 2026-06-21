param(
    [Parameter(Mandatory = $true)]
    [string] $Task,
    [string[]] $Files = @()
)

$ErrorActionPreference = "Stop"

if ($args -contains "-h" -or $args -contains "--help") {
    . (Join-Path $PSScriptRoot "_command-common.ps1")
    Show-RoutingHelp "route-session.ps1"
    exit 0
}

. (Join-Path $PSScriptRoot "_command-common.ps1")

$pyArgs = @("session", "--task", $Task)
if ($Files.Count -gt 0) {
    $pyArgs += @("--files")
    $pyArgs += $Files
}
Invoke-CommandsPython "routing.py" $pyArgs
