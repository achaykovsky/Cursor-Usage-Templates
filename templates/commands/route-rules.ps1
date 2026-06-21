param(
    [string[]] $Files = @(),
    [string] $Task = ""
)

$ErrorActionPreference = "Stop"

if ($args -contains "-h" -or $args -contains "--help") {
    . (Join-Path $PSScriptRoot "_command-common.ps1")
    Show-RoutingHelp "route-rules.ps1"
    exit 0
}

. (Join-Path $PSScriptRoot "_command-common.ps1")

$pyArgs = @("rules")
if ($Files.Count -gt 0) {
    $pyArgs += @("--files")
    $pyArgs += $Files
}
if ($Task) { $pyArgs += @("--task", $Task) }
Invoke-CommandsPython "routing.py" $pyArgs
