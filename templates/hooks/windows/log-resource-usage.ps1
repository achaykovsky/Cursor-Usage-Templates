# Resource usage ledger: rules, skills, subagents, hooks.
# Writes .cursor/logs/resource-ledger/active.json during a generation;
# on stop, appends summary to cursor-resources-YYYY-MM-DD.jsonl.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$needsGatedJson = $false
$gatedEvent = ""

try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        exit 0
    }

    $payload = Get-HookPayload $raw
    if (-not $payload) {
        exit 0
    }

    $event = "$($payload.hook_event_name)"
    if ([string]::IsNullOrWhiteSpace($event)) {
        exit 0
    }

    switch ($event) {
        "beforeSubmitPrompt" { $needsGatedJson = $true; $gatedEvent = $event }
        "preToolUse" { $needsGatedJson = $true; $gatedEvent = $event }
        "subagentStart" { $needsGatedJson = $true; $gatedEvent = $event }
    }

    $projectRoot = Get-ProjectRootFromPayload $payload
    if (-not $projectRoot) {
        exit 0
    }

    $ledgerDir = Get-ResourceLedgerDir $projectRoot
    $activePath = Get-ResourceActiveLedgerPath $projectRoot
    $logDir = Join-Path (Join-Path $projectRoot ".cursor") "logs"
    $null = New-Item -ItemType Directory -Path $logDir -Force

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

    function Get-FirstList($data, $keys) {
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

    function Get-SkillNameFromPath([string]$Path) {
        if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
        $normalized = $Path -replace '\\', '/'
        if ($normalized -match '/skills/([^/]+)/SKILL\.md$') {
            return $Matches[1]
        }
        if ($normalized -match '/([^/]+)/SKILL\.md$') {
            return $Matches[1]
        }
        return $null
    }

    function Get-HooksConfigured([string]$Root) {
        $hooksJson = Join-Path (Join-Path $Root ".cursor") "hooks.json"
        if (-not (Test-Path -LiteralPath $hooksJson)) {
            return @()
        }
        try {
            $cfg = Get-Content -LiteralPath $hooksJson -Raw -Encoding UTF8 | ConvertFrom-Json
            $out = New-Object System.Collections.Generic.List[string]
            foreach ($hookName in $cfg.hooks.PSObject.Properties.Name) {
                $entries = @($cfg.hooks.$hookName)
                if ($entries.Count -eq 0) { continue }
                foreach ($entry in $entries) {
                    $cmd = "$($entry.command)"
                    if ([string]::IsNullOrWhiteSpace($cmd)) { continue }
                    $lastToken = ($cmd -split '\s+')[-1] -replace '"', ''
                    $script = [System.IO.Path]::GetFileName($lastToken)
                    if ([string]::IsNullOrWhiteSpace($script)) { continue }
                    $out.Add("${hookName}:${script}")
                }
            }
            return @($out | Select-Object -Unique | Sort-Object)
        } catch {
            return @()
        }
    }

    function Read-ActiveLedger([string]$Path) {
        if (-not (Test-Path -LiteralPath $Path)) { return $null }
        try {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            return $null
        }
    }

    function Write-ActiveLedger([string]$Path, [hashtable]$Data) {
        ($Data | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $Path -Encoding UTF8
    }

    function Add-Unique([System.Collections.Generic.List[string]]$List, [string]$Value) {
        if ([string]::IsNullOrWhiteSpace($Value)) { return }
        if (-not $List.Contains($Value)) {
            $List.Add($Value) | Out-Null
        }
    }

    function Append-TrackingEvent($ledger, [string]$EventName) {
        if (-not $ledger.tracking_events) {
            $ledger | Add-Member -NotePropertyName tracking_events -NotePropertyValue @() -Force
        }
        $events = [System.Collections.Generic.List[string]]::new()
        foreach ($e in @($ledger.tracking_events)) { Add-Unique $events $e }
        Add-Unique $events $EventName
        $ledger.tracking_events = @($events)
    }

    switch ($event) {
        "beforeSubmitPrompt" {
            $generationId = "$($payload.generation_id)"
            $conversationId = "$($payload.conversation_id)"
            $rules = Get-FirstList $payload @(
                "rules", "used_rules", "applied_rules", "matched_rules", "active_rules", "rule_names"
            )
            $skills = Get-FirstList $payload @(
                "skills", "used_skills", "applied_skills", "matched_skills", "selected_skills", "skill_names"
            )

            $ledger = [ordered]@{
                ts               = (Get-Date).ToString("o")
                generation_id    = $generationId
                conversation_id  = $conversationId
                rules            = @($rules)
                skills_payload   = @($skills)
                skills_read      = @()
                subagents        = @()
                hooks_configured = @(Get-HooksConfigured $projectRoot)
                tracking_events  = @("beforeSubmitPrompt")
            }
            Write-ActiveLedger $activePath $ledger
        }

        "preToolUse" {
            $toolName = "$($payload.tool_name)"
            if ($toolName -ne "Read") {
                break
            }

            $toolInput = $payload.tool_input
            $readPath = $null
            if ($toolInput) {
                $readPath = "$($toolInput.path)"
                if ([string]::IsNullOrWhiteSpace($readPath)) {
                    $readPath = "$($toolInput.target_file)"
                }
            }
            if ([string]::IsNullOrWhiteSpace($readPath)) {
                break
            }

            $skillName = Get-SkillNameFromPath $readPath
            if (-not $skillName) {
                break
            }

            $ledger = Read-ActiveLedger $activePath
            if (-not $ledger) {
                $ledger = [PSCustomObject][ordered]@{
                    ts              = (Get-Date).ToString("o")
                    generation_id   = "$($payload.generation_id)"
                    conversation_id = "$($payload.conversation_id)"
                    rules           = @()
                    skills_payload  = @()
                    skills_read     = @()
                    subagents       = @()
                    tracking_events = @()
                }
            }

            $skillsRead = [System.Collections.Generic.List[string]]::new()
            foreach ($s in @($ledger.skills_read)) { Add-Unique $skillsRead $s }
            Add-Unique $skillsRead $skillName
            $ledger.skills_read = @($skillsRead)
            Append-TrackingEvent $ledger "preToolUse:skill_read"
            $ledger.ts = (Get-Date).ToString("o")
            ($ledger | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $activePath -Encoding UTF8
        }

        "subagentStart" {
            $ledger = Read-ActiveLedger $activePath
            if (-not $ledger) {
                $ledger = [PSCustomObject][ordered]@{
                    ts              = (Get-Date).ToString("o")
                    generation_id   = "$($payload.generation_id)"
                    conversation_id = "$($payload.conversation_id)"
                    rules           = @()
                    skills_payload  = @()
                    skills_read     = @()
                    subagents       = @()
                    tracking_events = @()
                }
            }

            $entry = [ordered]@{
                id     = "$($payload.subagent_id)"
                type   = "$($payload.subagent_type)"
                task   = "$($payload.task)"
                status = "started"
                ts     = (Get-Date).ToString("o")
            }
            $subagents = [System.Collections.Generic.List[object]]::new()
            foreach ($s in @($ledger.subagents)) { $subagents.Add($s) | Out-Null }
            $subagents.Add([PSCustomObject]$entry) | Out-Null
            $ledger.subagents = @($subagents)
            Append-TrackingEvent $ledger "subagentStart"
            $ledger.ts = (Get-Date).ToString("o")
            ($ledger | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $activePath -Encoding UTF8
        }

        "subagentStop" {
            $ledger = Read-ActiveLedger $activePath
            if (-not $ledger) {
                break
            }

            $subagentType = "$($payload.subagent_type)"
            $status = "$($payload.status)"
            $task = "$($payload.task)"
            $updated = @()
            $matched = $false
            foreach ($s in @($ledger.subagents)) {
                if (-not $matched -and "$($s.type)" -eq $subagentType -and "$($s.status)" -eq "started") {
                    $updated += [PSCustomObject][ordered]@{
                        id     = $s.id
                        type   = $s.type
                        task   = if ($task) { $task } else { $s.task }
                        status = $status
                        ts     = (Get-Date).ToString("o")
                    }
                    $matched = $true
                } else {
                    $updated += $s
                }
            }
            if (-not $matched) {
                $updated += [PSCustomObject][ordered]@{
                    id     = ""
                    type   = $subagentType
                    task   = $task
                    status = $status
                    ts     = (Get-Date).ToString("o")
                }
            }
            $ledger.subagents = @($updated)
            Append-TrackingEvent $ledger "subagentStop"
            $ledger.ts = (Get-Date).ToString("o")
            ($ledger | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $activePath -Encoding UTF8
        }

        "stop" {
            $ledger = Read-ActiveLedger $activePath
            if (-not $ledger) {
                break
            }

            $summary = [ordered]@{
                ts               = (Get-Date).ToString("o")
                event            = "resource_summary"
                generation_id    = $ledger.generation_id
                conversation_id  = $ledger.conversation_id
                status           = "$($payload.status)"
                rules            = @($ledger.rules)
                skills_payload   = @($ledger.skills_payload)
                skills_read      = @($ledger.skills_read)
                subagents        = @($ledger.subagents)
                hooks_configured = @($ledger.hooks_configured)
                tracking_events  = @($ledger.tracking_events)
            }

            $resourcesLog = Join-Path $logDir ("cursor-resources-{0:yyyy-MM-dd}.jsonl" -f (Get-Date))
            $line = $summary | ConvertTo-Json -Compress -Depth 12
            Add-Content -Path $resourcesLog -Value $line -Encoding UTF8

            $latestPath = Join-Path $ledgerDir "latest.json"
            ($summary | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $latestPath -Encoding UTF8
            Append-TrackingEvent $ledger "stop"
            $ledger.ts = (Get-Date).ToString("o")
            ($ledger | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $activePath -Encoding UTF8
        }
    }
} catch {
    Write-HookError $_
} finally {
    if ($needsGatedJson) {
        switch ($gatedEvent) {
            "beforeSubmitPrompt" { Write-PromptAllow }
            "preToolUse" { Write-PreToolUseAllow }
            "subagentStart" { Write-SubagentAllow }
        }
    }
}

exit 0
