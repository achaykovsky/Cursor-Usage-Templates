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

function Read-HookStdinBytes() {
    try {
        $stdin = [Console]::OpenStandardInput()
        try {
            $ms = New-Object System.IO.MemoryStream
            $stdin.CopyTo($ms)
            return $ms.ToArray()
        } finally {
            $stdin.Dispose()
        }
    } catch {
        try {
            $text = [Console]::In.ReadToEnd()
            if ([string]::IsNullOrEmpty($text)) {
                return [byte[]]@()
            }
            return [System.Text.Encoding]::UTF8.GetBytes($text)
        } catch {
            return [byte[]]@()
        }
    }
}

function Get-HookStdinTextCandidates([byte[]]$Bytes) {
    $candidates = New-Object System.Collections.Generic.List[string]
    if (-not $Bytes -or $Bytes.Length -eq 0) {
        return @()
    }

    # UTF-8 BOM — Cursor on Windows may pipe JSON with EF BB BF; default console
    # encoding misreads that prefix as garbage (e.g. U+2229) and breaks ConvertFrom-Json.
    if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
        $candidates.Add([System.Text.Encoding]::UTF8.GetString($Bytes, 3, $Bytes.Length - 3)) | Out-Null
    }

    # UTF-16 LE / BE BOM
    if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xFE) {
        $candidates.Add([System.Text.Encoding]::Unicode.GetString($Bytes, 2, $Bytes.Length - 2)) | Out-Null
    }
    if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFE -and $Bytes[1] -eq 0xFF) {
        $candidates.Add([System.Text.Encoding]::BigEndianUnicode.GetString($Bytes, 2, $Bytes.Length - 2)) | Out-Null
    }

    # UTF-16 LE without BOM (leading "{" or quote followed by null byte)
    if ($Bytes.Length -ge 2 -and $Bytes[1] -eq 0x00 -and ($Bytes[0] -eq 0x7B -or $Bytes[0] -eq 0x22)) {
        $candidates.Add([System.Text.Encoding]::Unicode.GetString($Bytes)) | Out-Null
    }

    $candidates.Add([System.Text.Encoding]::UTF8.GetString($Bytes)) | Out-Null
    $candidates.Add([System.Text.Encoding]::Unicode.GetString($Bytes)) | Out-Null

    return @($candidates | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
}

function Read-HookStdin() {
    $bytes = Read-HookStdinBytes
    if ($bytes.Length -eq 0) {
        return ""
    }

    $candidates = Get-HookStdinTextCandidates $bytes
    if ($candidates.Count -gt 0) {
        return $candidates[0]
    }

    return [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Test-PayloadPropertiesCorrupt($payload) {
    if (-not $payload) { return $false }

    foreach ($prop in $payload.PSObject.Properties) {
        if ($prop.Name -match "`0") {
            return $true
        }
    }

    return $false
}

function ConvertFrom-HookJsonText([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }

    try {
        $payload = $Text.Trim() | ConvertFrom-Json
        if (Test-PayloadPropertiesCorrupt $payload) {
            return $null
        }
        return $payload
    } catch {
        return $null
    }
}

function Get-HookPayload([string]$Raw) {
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
    return ConvertFrom-HookJsonText $Raw
}

function Get-HookPayloadFromBytes([byte[]]$Bytes) {
    if (-not $Bytes -or $Bytes.Length -eq 0) { return $null }

    foreach ($text in (Get-HookStdinTextCandidates $Bytes)) {
        $payload = ConvertFrom-HookJsonText $text
        if ($payload) {
            return $payload
        }
    }

    return $null
}

function Read-HookPayload() {
    return Get-HookPayloadFromBytes (Read-HookStdinBytes)
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

function Resolve-ProjectRoot($data) {
    $root = Get-ProjectRootFromPayload $data
    if ($root -and (Test-Path -LiteralPath (Join-Path $root ".cursor"))) {
        return $root
    }

    foreach ($startDir in @(
        if ($data -and $data.cwd) { "$($data.cwd)" } else { $null }
        (Get-Location).Path
    )) {
        if ([string]::IsNullOrWhiteSpace($startDir)) { continue }

        $gitRoot = & git -C $startDir rev-parse --show-toplevel 2>$null
        if ($gitRoot -and (Test-Path -LiteralPath (Join-Path $gitRoot ".cursor"))) {
            return "$gitRoot"
        }
    }

    # Hook scripts live at <project>/.cursor/hooks/scripts — infer when payload is corrupt.
    $scriptRoot = $PSScriptRoot
    if (-not [string]::IsNullOrWhiteSpace($scriptRoot)) {
        $cursorDir = Split-Path (Split-Path $scriptRoot -Parent) -Parent
        if (Test-Path -LiteralPath (Join-Path $cursorDir "hooks.json")) {
            return $cursorDir
        }
    }

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

function Get-CursorLogsDir([string]$ProjectRoot) {
    $dir = Join-Path $ProjectRoot "logs"
    $null = New-Item -ItemType Directory -Path $dir -Force
    return $dir
}

function Get-CursorDailyLogDir([string]$ProjectRoot) {
    $dateFolder = (Get-Date).ToString("yyyy-MM-dd")
    $dir = Join-Path (Get-CursorLogsDir $ProjectRoot) $dateFolder
    $null = New-Item -ItemType Directory -Path $dir -Force
    return $dir
}

function Get-CursorLogFilePath([string]$ProjectRoot, [string]$LogBaseName) {
    return Join-Path (Get-CursorDailyLogDir $ProjectRoot) ("{0}.jsonl" -f $LogBaseName)
}

function Get-ResourceLedgerDir([string]$ProjectRoot) {
    $dir = Join-Path (Get-CursorLogsDir $ProjectRoot) "resource-ledger"
    $null = New-Item -ItemType Directory -Path $dir -Force
    return $dir
}

function Get-ResourceActiveLedgerPath([string]$ProjectRoot) {
    return Join-Path (Get-ResourceLedgerDir $ProjectRoot) "active.json"
}

function Read-ActiveLedger([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Add-HookExecutedEntry($ledger, [string]$EventName, [string]$ScriptFileName) {
    if (-not $ledger -or [string]::IsNullOrWhiteSpace($EventName) -or [string]::IsNullOrWhiteSpace($ScriptFileName)) {
        return $ledger
    }

    $entry = "${EventName}:${ScriptFileName}"
    $executed = [System.Collections.Generic.List[string]]::new()
    foreach ($e in @($ledger.hooks_executed)) { Add-UniqueToStringList $executed $e }
    Add-UniqueToStringList $executed $entry
    Set-LedgerProperty $ledger "hooks_executed" @($executed | Sort-Object)
    return $ledger
}

function Register-HookExecution($payload, [string]$ScriptFileName) {
    if ([string]::IsNullOrWhiteSpace($ScriptFileName)) { return }

    $event = if ($payload) { "$($payload.hook_event_name)" } else { "" }
    if ([string]::IsNullOrWhiteSpace($event)) { return }

    $projectRoot = Resolve-ProjectRoot $payload
    if (-not $projectRoot) { return }

    $activePath = Get-ResourceActiveLedgerPath $projectRoot

    try {
        $ledger = Read-ActiveLedger $activePath
        if (-not $ledger) {
            $ledger = [PSCustomObject][ordered]@{
                ts              = (Get-Date).ToString("o")
                generation_id   = if ($payload.generation_id) { "$($payload.generation_id)" } else { "" }
                conversation_id = if ($payload.conversation_id) { "$($payload.conversation_id)" } else { "" }
                hooks_executed  = @()
            }
        }

        $ledger = Add-HookExecutedEntry $ledger $event $ScriptFileName
        $ledger.ts = (Get-Date).ToString("o")
        Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
    } catch {
        Write-HookError $_
    }
}

function Write-ActiveLedgerAtomic([string]$Path, [object]$Ledger) {
    if ([string]::IsNullOrWhiteSpace($Path) -or $null -eq $Ledger) { return }

    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        $null = New-Item -ItemType Directory -Path $dir -Force
    }

    $lockPath = "$Path.lock"
    $lockStream = $null
    try {
        # Exclusive lock prevents concurrent hook events from interleaving ledger writes.
        $lockStream = [System.IO.File]::Open(
            $lockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        $tmp = Join-Path $dir ("active.json.{0}.tmp" -f [Guid]::NewGuid().ToString("N"))
        ($Ledger | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $tmp -Encoding UTF8
        Move-Item -LiteralPath $tmp -Destination $Path -Force
    } catch {
        Write-HookError $_
        throw
    } finally {
        if ($null -ne $lockStream) {
            $lockStream.Dispose()
        }
    }
}

function Get-NumericField($data, [string[]]$keys) {
    if (-not $data) { return $null }

    foreach ($key in $keys) {
        $prop = $data.PSObject.Properties[$key]
        if ($null -eq $prop -or $null -eq $prop.Value) { continue }

        $value = $prop.Value
        if ($value -is [int] -or $value -is [long] -or $value -is [decimal] -or $value -is [double]) {
            return [long]$value
        }

        $text = "$value".Trim()
        if ($text -match '^\d+$') {
            return [long]$text
        }
    }

    return $null
}

function Get-PayloadModel($data) {
    if (-not $data) { return $null }

    $model = Get-FirstString $data @(
        "model", "model_name", "modelName", "model_id", "selected_model", "agent_model", "subagent_model"
    )
    if (-not [string]::IsNullOrWhiteSpace($model)) {
        return $model
    }

    $modelObj = $data.model
    if ($modelObj -is [PSCustomObject]) {
        $nested = Get-FirstString $modelObj @("id", "name", "display_name")
        if (-not [string]::IsNullOrWhiteSpace($nested)) {
            return $nested
        }
    }

    return $null
}

function Get-UsageFromObject($obj) {
    $usage = @{}
    if (-not $obj) { return $usage }

    $inputTokens = Get-NumericField $obj @("input_tokens", "prompt_tokens", "inputTokens")
    $outputTokens = Get-NumericField $obj @("output_tokens", "completion_tokens", "outputTokens")
    $totalTokens = Get-NumericField $obj @("total_tokens", "totalTokens", "tokens")

    if ($null -ne $inputTokens) { $usage.input_tokens = $inputTokens }
    if ($null -ne $outputTokens) { $usage.output_tokens = $outputTokens }
    if ($null -ne $totalTokens) { $usage.total_tokens = $totalTokens }

    return $usage
}

function Get-PayloadTokenUsage($data, [string]$EventName) {
    $usage = @{}
    if (-not $data) { return $usage }

    foreach ($key in @("usage", "usage_stats", "token_usage", "tokens")) {
        $prop = $data.PSObject.Properties[$key]
        if ($null -eq $prop -or $null -eq $prop.Value) { continue }

        $nested = Get-UsageFromObject $prop.Value
        foreach ($field in $nested.Keys) {
            $usage[$field] = $nested[$field]
        }
    }

    $flatFields = [ordered]@{
        input_tokens            = @("input_tokens", "prompt_tokens")
        output_tokens           = @("output_tokens", "completion_tokens")
        total_tokens            = @("total_tokens")
        context_tokens          = @("context_tokens")
        context_usage_percent   = @("context_usage_percent")
        context_window_size     = @("context_window_size")
    }

    foreach ($field in $flatFields.Keys) {
        $value = Get-NumericField $data $flatFields[$field]
        if ($null -ne $value) {
            $usage[$field] = $value
        }
    }

    if ($usage.Count -gt 0) {
        $usage.source = $EventName
    }

    return $usage
}

function Merge-TokenUsageHashtable($base, $incoming) {
    if (-not $incoming -or $incoming.Count -eq 0) {
        return $base
    }

    if (-not $base) {
        $base = @{}
    }

    foreach ($key in $incoming.Keys) {
        if ($null -ne $incoming[$key]) {
            $base[$key] = $incoming[$key]
        }
    }

    return $base
}

function Set-LedgerProperty($ledger, [string]$Name, $Value) {
    if ($null -eq $ledger) { return }
    if ($null -eq $Value -and $Name -ne "model") { return }

    $prop = $ledger.PSObject.Properties[$Name]
    if ($null -ne $prop) {
        $ledger.$Name = $Value
    } else {
        $ledger | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
    }
}

function Update-LedgerModelAndTokens($ledger, $payload, [string]$EventName) {
    if (-not $ledger) { return $ledger }

    $model = Get-PayloadModel $payload
    if (-not [string]::IsNullOrWhiteSpace($model)) {
        Set-LedgerProperty $ledger "model" $model
    }

    $incoming = Get-PayloadTokenUsage $payload $EventName
    if ($incoming.Count -gt 0) {
        $existing = @{}
        if ($ledger.tokens) {
            foreach ($prop in $ledger.tokens.PSObject.Properties) {
                $existing[$prop.Name] = $prop.Value
            }
        }
        Set-LedgerProperty $ledger "tokens" ([PSCustomObject](Merge-TokenUsageHashtable $existing $incoming))
    }

    return $ledger
}

function Add-UniqueToStringList([System.Collections.Generic.List[string]]$List, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return }
    $trimmed = $Value.Trim()
    if (-not $List.Contains($trimmed)) {
        $List.Add($trimmed) | Out-Null
    }
}

function Get-AgentInvokeFromSubagentFile([string]$ProjectRoot, [string]$FileName) {
    if ([string]::IsNullOrWhiteSpace($FileName) -or [string]::IsNullOrWhiteSpace($ProjectRoot)) {
        return $null
    }

    $candidates = @(
        (Join-Path $ProjectRoot "templates\agents\subagents\$FileName"),
        (Join-Path $ProjectRoot ".cursor\agents\$FileName")
    )
    foreach ($path in $candidates) {
        if (-not (Test-Path -LiteralPath $path)) { continue }
        try {
            $lines = Get-Content -LiteralPath $path -TotalCount 12 -Encoding UTF8
            foreach ($line in $lines) {
                if ($line -match '^\s*name:\s*(\S+)\s*$') {
                    return $Matches[1].Trim()
                }
            }
        } catch {
            continue
        }
    }
    return $null
}

function Get-AgentsRequestedFromPrompt([string]$Prompt, [string]$ProjectRoot) {
    $agents = [System.Collections.Generic.List[string]]::new()
    if ([string]::IsNullOrWhiteSpace($Prompt)) {
        return @()
    }

    foreach ($match in [regex]::Matches($Prompt, '@agent\(\s*([^)]+?)\s*\)', 'IgnoreCase')) {
        Add-UniqueToStringList $agents $match.Groups[1].Value
    }

    foreach ($match in [regex]::Matches($Prompt, 'subagents[/\\]([a-zA-Z0-9_-]+)\.md', 'IgnoreCase')) {
        $invoke = Get-AgentInvokeFromSubagentFile $ProjectRoot ($match.Groups[1].Value + '.md')
        if ($invoke) {
            Add-UniqueToStringList $agents $invoke
        }
    }

    foreach ($match in [regex]::Matches($Prompt, '[/\\]agents[/\\]([a-zA-Z0-9_-]+)\.md', 'IgnoreCase')) {
        $fileName = $match.Groups[1].Value + '.md'
        if ($fileName -match '^(AGENTS|AGENTS_USAGE)\.md$') { continue }
        $invoke = Get-AgentInvokeFromSubagentFile $ProjectRoot $fileName
        if ($invoke) {
            Add-UniqueToStringList $agents $invoke
        }
    }

    return @($agents | Sort-Object)
}

function Get-RoutingScript([string]$ProjectRoot) {
    $candidates = @()
    if ($ProjectRoot) {
        $candidates += Join-Path (Join-Path $ProjectRoot "templates") "commands\routing.py"
        $candidates += Join-Path (Join-Path (Join-Path $ProjectRoot ".cursor") "commands") "routing.py"
    }
    $templatesRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $candidates += Join-Path (Join-Path $templatesRoot "commands") "routing.py"
    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath $path) { return $path }
    }
    return $null
}

function Get-SkillsMatchedFromPrompt([string]$Prompt, [string]$ProjectRoot) {
    if ([string]::IsNullOrWhiteSpace($Prompt)) {
        return @()
    }

    $py = Get-PythonExecutable
    $script = Get-RoutingScript $ProjectRoot
    if (-not $py -or -not $script) {
        return @()
    }

    try {
        $out = & $py $script skills-match --task $Prompt 2>$null
        if ([string]::IsNullOrWhiteSpace($out)) {
            return @()
        }
        $parsed = $out | ConvertFrom-Json
        if ($null -eq $parsed) {
            return @()
        }
        return @($parsed)
    } catch {
        return @()
    }
}

function Get-RulesMatchedFromPrompt([string]$Prompt, [string]$ProjectRoot) {
    if ([string]::IsNullOrWhiteSpace($Prompt)) {
        return @()
    }

    $py = Get-PythonExecutable
    $script = Get-RoutingScript $ProjectRoot
    if (-not $py -or -not $script) {
        return @()
    }

    try {
        $out = & $py $script rules-match --task $Prompt 2>$null
        if ([string]::IsNullOrWhiteSpace($out)) {
            return @()
        }
        $parsed = $out | ConvertFrom-Json
        if ($null -eq $parsed) {
            return @()
        }
        return @($parsed)
    } catch {
        return @()
    }
}

function Get-PromptPredictions([string]$Prompt, [string]$ProjectRoot) {
    $empty = @{
        predicted_skills = @()
        predicted_rules  = @()
    }
    if ([string]::IsNullOrWhiteSpace($Prompt)) {
        return $empty
    }

    $py = Get-PythonExecutable
    $script = Get-RoutingScript $ProjectRoot
    if (-not $py -or -not $script) {
        return $empty
    }

    try {
        $out = & $py $script predict --task $Prompt 2>$null
        if ([string]::IsNullOrWhiteSpace($out)) {
            return $empty
        }
        $parsed = $out | ConvertFrom-Json
        return @{
            predicted_skills = @($parsed.predicted_skills)
            predicted_rules  = @($parsed.predicted_rules)
        }
    } catch {
        return $empty
    }
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

function Get-RedactSensitiveScript([string]$ProjectRoot) {
    $candidates = @()
    if ($ProjectRoot) {
        $candidates += Join-Path (Join-Path (Join-Path $ProjectRoot ".cursor") "hooks") "policy\redact_sensitive.py"
    }
    $candidates += Join-Path (Split-Path $PSScriptRoot -Parent) "policy\redact_sensitive.py"
    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath $path) { return $path }
    }
    return $null
}

function Invoke-RedactText([string]$Text, [string]$ProjectRoot) {
    if ([string]::IsNullOrEmpty($Text)) { return $Text }

    $py = Get-PythonExecutable
    $script = Get-RedactSensitiveScript $ProjectRoot
    if (-not $py -or -not $script) {
        return $Text
    }

    try {
        $out = $Text | & $py $script redact-text 2>$null
        if ($null -eq $out) { return $Text }
        return "$out"
    } catch {
        return $Text
    }
}

function Invoke-RedactReadPayload([string]$Raw, [string]$ProjectRoot) {
    $py = Get-PythonExecutable
    $script = Get-RedactSensitiveScript $ProjectRoot
    if (-not $py -or -not $script) {
        return $null
    }

    try {
        $out = $Raw | & $py $script redact-read-payload 2>$null
        if ([string]::IsNullOrWhiteSpace($out)) { return $null }
        return $out | ConvertFrom-Json
    } catch {
        return $null
    }
}


function Invoke-RedactReadPayloadJson([string]$Raw, [string]$ProjectRoot) {
    # Pass through redact_sensitive.py JSON unchanged — ConvertTo-Json corrupts Unicode in large bodies.
    $py = Get-PythonExecutable
    $script = Get-RedactSensitiveScript $ProjectRoot
    if (-not $py -or -not $script) {
        return $null
    }

    try {
        $out = $Raw | & $py $script redact-read-payload 2>$null
        if ([string]::IsNullOrWhiteSpace($out)) { return $null }
        $line = "$out".Trim()
        if ($line -match "[
]") { return $null }
        $null = $line | ConvertFrom-Json
        return $line
    } catch {
        return $null
    }
}

function Get-CursorActivityScript([string]$ProjectRoot) {
    $candidates = @()
    if ($ProjectRoot) {
        $candidates += Join-Path (Join-Path $ProjectRoot "templates") "commands\cursor_activity.py"
        $candidates += Join-Path (Join-Path (Join-Path $ProjectRoot ".cursor") "commands") "cursor_activity.py"
    }
    $templatesRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $candidates += Join-Path (Join-Path $templatesRoot "commands") "cursor_activity.py"
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
