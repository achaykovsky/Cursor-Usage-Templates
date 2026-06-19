# Shared helpers for Cursor hook scripts. Dot-source from $PSScriptRoot:
#   . (Join-Path $PSScriptRoot "hook-common.ps1")
# Rules: stderr only for diagnostics; stdout is exactly one JSON line for gated hooks.

$ErrorActionPreference = "SilentlyContinue"

function Write-HookJson([object]$Obj) {
    $json = $Obj | ConvertTo-Json -Compress -Depth 32
    [Console]::Out.WriteLine($json)
}

function Write-ReadAllow() {
    Write-HookJson @{ permission = "allow" }
}

function Write-ReadAllowWithContent([string]$Content) {
    Write-HookJson @{ permission = "allow"; content = $Content }
}

function Write-ShellAllow() {
    Write-HookJson @{ continue = $true; permission = "allow" }
}

function Write-PromptAllow() {
    Write-HookJson @{ continue = $true; permission = "allow" }
}

function Write-ShellDeny([string]$UserMsg, [string]$AgentMsg) {
    Write-HookJson @{
        continue       = $false
        permission     = "deny"
        user_message   = $UserMsg
        agent_message  = $AgentMsg
    }
}

function Write-ShellAsk([string]$UserMsg, [string]$AgentMsg) {
    Write-HookJson @{
        continue       = $true
        permission     = "ask"
        user_message   = $UserMsg
        agent_message  = $AgentMsg
    }
}

function Read-HookStdin() {
    try {
        return [System.Console]::In.ReadToEnd()
    } catch {
        return ""
    }
}

function Get-HookPayload([string]$Raw) {
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
    try {
        return $Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Write-HookError([object]$Err) {
    $msg = if ($Err -is [System.Management.Automation.ErrorRecord]) {
        $Err.Exception.Message
    } elseif ($Err -is [Exception]) {
        $Err.Message
    } else {
        "$Err"
    }
    if (-not [string]::IsNullOrWhiteSpace($msg)) {
        [Console]::Error.WriteLine("hook: $msg")
    }
}

function Get-ProjectRootFromPayload($data) {
    if (-not $data) { return $null }

    $roots = $data.workspace_roots
    if ($roots -and $roots.Count -gt 0) {
        return "$($roots[0])"
    }

    $startDir = if ($data.cwd) { "$($data.cwd)" } else { (Get-Location).Path }
    $gitRoot = & git -C $startDir rev-parse --show-toplevel 2>$null
    if ($gitRoot) { return "$gitRoot" }
    return $null
}

function ConvertTo-NameList($value) {
    if ($null -eq $value) { return @() }

    if ($value -is [string]) {
        if ([string]::IsNullOrWhiteSpace($value)) { return @() }
        return @($value.Trim())
    }

    if ($value -is [System.Collections.IEnumerable]) {
        $items = @()
        foreach ($item in $value) {
            if ($null -eq $item) { continue }

            if ($item -is [string]) {
                if (-not [string]::IsNullOrWhiteSpace($item)) {
                    $items += $item.Trim()
                }
                continue
            }

            $name = $item.name
            if (-not [string]::IsNullOrWhiteSpace($name)) {
                $items += "$name".Trim()
                continue
            }

            $id = $item.id
            if (-not [string]::IsNullOrWhiteSpace($id)) {
                $items += "$id".Trim()
                continue
            }

            $str = "$item"
            if (-not [string]::IsNullOrWhiteSpace($str)) {
                $items += $str.Trim()
            }
        }
        return @($items | Select-Object -Unique)
    }

    return @("$value")
}

function Get-FirstList($data, [string[]]$keys) {
    if (-not $data) { return @() }

    foreach ($key in $keys) {
        $prop = $data.PSObject.Properties[$key]
        if ($null -ne $prop -and $null -ne $prop.Value) {
            $normalized = ConvertTo-NameList $prop.Value
            if ($normalized.Count -gt 0) {
                return $normalized
            }
        }
    }
    return @()
}

function Get-FirstString($data, [string[]]$keys) {
    if (-not $data) { return "" }

    foreach ($key in $keys) {
        $prop = $data.PSObject.Properties[$key]
        if ($null -eq $prop -or $null -eq $prop.Value) { continue }

        $value = $prop.Value
        if ($value -is [string]) {
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                return $value.Trim()
            }
            continue
        }

        $text = "$value"
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            return $text.Trim()
        }
    }

    return ""
}

function Get-ResourceLedgerDir([string]$ProjectRoot) {
    $dir = Join-Path (Join-Path (Join-Path $ProjectRoot ".cursor") "logs") "resource-ledger"
    $null = New-Item -ItemType Directory -Path $dir -Force
    return $dir
}

function Get-ResourceActiveLedgerPath([string]$ProjectRoot) {
    return Join-Path (Get-ResourceLedgerDir $ProjectRoot) "active.json"
}

function Write-PreToolUseAllow() {
    Write-HookJson @{ permission = "allow" }
}

function Write-SubagentAllow() {
    Write-HookJson @{ permission = "allow" }
}

function Get-PythonExecutable() {
    foreach ($name in @("python", "python3", "py")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function Get-HookPolicyScript([string]$ProjectRoot) {
    $candidates = @()
    if ($ProjectRoot) {
        $candidates += Join-Path (Join-Path (Join-Path $ProjectRoot ".cursor") "hooks") "policy\hook_policy.py"
    }
    $candidates += Join-Path (Split-Path $PSScriptRoot -Parent) "policy\hook_policy.py"
    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath $path) { return $path }
    }
    return $null
}

function Invoke-HookPolicy([string]$Domain, [string]$Raw, [string]$ProjectRoot) {
    $py = Get-PythonExecutable
    if (-not $py) {
        return @{ continue = $true; permission = "allow" }
    }
    $script = Get-HookPolicyScript $ProjectRoot
    if (-not $script) {
        return @{ continue = $true; permission = "allow" }
    }
    try {
        $out = $Raw | & $py $script $Domain
        if ([string]::IsNullOrWhiteSpace($out)) {
            return @{ continue = $true; permission = "allow" }
        }
        return $out | ConvertFrom-Json
    } catch {
        return @{ continue = $true; permission = "allow" }
    }
}

function Emit-HookPolicyResult($result) {
    if (-not $result) {
        Write-ShellAllow
        return
    }
    Write-HookJson $result
}
