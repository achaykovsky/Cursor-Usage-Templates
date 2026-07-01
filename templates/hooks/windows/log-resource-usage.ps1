# Resource usage ledger: rules, skills, subagents, hooks.
# Writes logs/resource-ledger/active.json during a generation;
# on stop, appends summary to logs/YYYY-MM-DD/cursor-resources.jsonl.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$needsGatedJson = $false
$gatedEvent = ""

try {
    $payload = Read-HookPayload
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

    $projectRoot = Resolve-ProjectRoot $payload
    if (-not $projectRoot) {
        Write-HookError "log-resource-usage: could not resolve project root"
        exit 0
    }

    $ledgerDir = Get-ResourceLedgerDir $projectRoot
    $activePath = Get-ResourceActiveLedgerPath $projectRoot

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

    function Read-ActiveLedgerObject([string]$Path, $payload, [string]$eventName) {
        $ledger = Read-ActiveLedger $Path
        if (-not $ledger) {
            $ledger = [PSCustomObject][ordered]@{
                ts              = (Get-Date).ToString("o")
                generation_id   = "$($payload.generation_id)"
                conversation_id = "$($payload.conversation_id)"
                model           = $null
                tokens          = $null
                rules           = @()
                skills_payload  = @()
                skills_read     = @()
                subagents       = @()
                tracking_events = @()
            }
        }
        return Update-LedgerModelAndTokens $ledger $payload $eventName
    }

    function Apply-CharTokenEstimate($ledger, [string]$promptText, [string]$responseText) {
        if (-not $ledger) { return $ledger }

        $promptChars = if ($promptText) { $promptText.Length } else { 0 }
        $responseChars = if ($responseText) { $responseText.Length } else { 0 }

        if ($promptChars -gt 0) {
            Set-LedgerProperty $ledger "prompt_chars" $promptChars
        }
        if ($responseChars -gt 0) {
            Set-LedgerProperty $ledger "response_chars" $responseChars
        }

        if ($promptChars -eq 0 -and $responseChars -eq 0) {
            return $ledger
        }

        $existing = @{}
        if ($ledger.tokens) {
            foreach ($prop in $ledger.tokens.PSObject.Properties) {
                $existing[$prop.Name] = $prop.Value
            }
        }

        $hasBilling = ($null -ne $existing.input_tokens) -or ($null -ne $existing.output_tokens) -or ($null -ne $existing.total_tokens)
        if ($hasBilling -and $existing.source -and $existing.source -ne "chars") {
            if ($promptChars -gt 0) { Set-LedgerProperty $ledger "prompt_chars" $promptChars }
            if ($responseChars -gt 0) { Set-LedgerProperty $ledger "response_chars" $responseChars }
            return $ledger
        }

        if ($null -eq $existing.input_tokens -and $promptChars -gt 0) {
            $existing.input_tokens = [long][Math]::Ceiling($promptChars / 4.0)
        }
        if ($null -eq $existing.output_tokens -and $responseChars -gt 0) {
            $existing.output_tokens = [long][Math]::Ceiling($responseChars / 4.0)
        }
        if ($null -eq $existing.total_tokens) {
            $inEst = if ($existing.input_tokens) { [long]$existing.input_tokens } else { 0 }
            $outEst = if ($existing.output_tokens) { [long]$existing.output_tokens } else { 0 }
            if (($inEst + $outEst) -gt 0) {
                $existing.total_tokens = $inEst + $outEst
            }
        }

        $existing.estimated = $true
        $existing.source = "chars"
        if ($promptChars -gt 0) { $existing.prompt_chars = $promptChars }
        if ($responseChars -gt 0) { $existing.response_chars = $responseChars }

        $ledger.tokens = [PSCustomObject]$existing
        return $ledger
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
            $model = Get-PayloadModel $payload
            $prompt = Get-FirstString $payload @(
                "prompt", "user_prompt", "content", "text", "input", "message"
            )
            $agentsRequested = @(Get-AgentsRequestedFromPrompt $prompt $projectRoot)
            $skillsMatched = @(Get-SkillsMatchedFromPrompt $prompt $projectRoot)

            $ledger = [PSCustomObject][ordered]@{
                ts               = (Get-Date).ToString("o")
                generation_id    = $generationId
                conversation_id  = $conversationId
                model            = $model
                tokens           = $null
                rules            = @($rules)
                skills_payload   = @($skills)
                skills_matched   = @($skillsMatched)
                skills_read      = @()
                agents_requested = @($agentsRequested)
                subagents        = @()
                hooks_configured = @(Get-HooksConfigured $projectRoot)
                hooks_executed   = @("beforeSubmitPrompt:log-resource-usage.ps1")
                tracking_events  = @("beforeSubmitPrompt")
            }
            $ledger = Apply-CharTokenEstimate $ledger $prompt ""
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
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
                    hooks_executed  = @()
                    tracking_events = @()
                }
            }

            $ledger = Add-HookExecutedEntry $ledger "preToolUse" "log-resource-usage.ps1"

            if (-not [string]::IsNullOrWhiteSpace($readPath)) {
                $skillName = Get-SkillNameFromPath $readPath
                if ($skillName) {
                    $skillsRead = [System.Collections.Generic.List[string]]::new()
                    foreach ($s in @($ledger.skills_read)) { Add-Unique $skillsRead $s }
                    Add-Unique $skillsRead $skillName
                    $ledger.skills_read = @($skillsRead)
                    Append-TrackingEvent $ledger "preToolUse:skill_read"
                }
            }

            $ledger.ts = (Get-Date).ToString("o")
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
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
            $ledger = Update-LedgerModelAndTokens $ledger $payload "subagentStart"
            $ledger = Add-HookExecutedEntry $ledger "subagentStart" "log-resource-usage.ps1"
            Append-TrackingEvent $ledger "subagentStart"
            $ledger.ts = (Get-Date).ToString("o")
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
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
            $ledger = Update-LedgerModelAndTokens $ledger $payload "subagentStop"
            $ledger = Add-HookExecutedEntry $ledger "subagentStop" "log-resource-usage.ps1"
            Append-TrackingEvent $ledger "subagentStop"
            $ledger.ts = (Get-Date).ToString("o")
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
        }

        "preCompact" {
            $ledger = Read-ActiveLedgerObject $activePath $payload "preCompact"
            $ledger = Add-HookExecutedEntry $ledger "preCompact" "log-resource-usage.ps1"
            Append-TrackingEvent $ledger "preCompact"
            $ledger.ts = (Get-Date).ToString("o")
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
        }

        "afterAgentResponse" {
            $ledger = Read-ActiveLedger $activePath
            if (-not $ledger) {
                $ledger = Read-ActiveLedgerObject $activePath $payload "afterAgentResponse"
            } else {
                $ledger = Update-LedgerModelAndTokens $ledger $payload "afterAgentResponse"
            }

            $responseText = Get-FirstString $payload @("text", "response", "content", "message")
            $promptChars = if ($ledger.prompt_chars) { [int]$ledger.prompt_chars } else { 0 }
            $ledger = Apply-CharTokenEstimate $ledger "" $responseText
            if ($promptChars -gt 0) {
                Set-LedgerProperty $ledger "prompt_chars" $promptChars
            }

            Append-TrackingEvent $ledger "afterAgentResponse"
            $ledger = Add-HookExecutedEntry $ledger "afterAgentResponse" "log-resource-usage.ps1"
            $ledger.ts = (Get-Date).ToString("o")
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
        }

        "stop" {
            $ledger = Read-ActiveLedger $activePath
            if (-not $ledger) {
                break
            }

            $ledger = Update-LedgerModelAndTokens $ledger $payload "stop"

            $summary = [ordered]@{
                ts               = (Get-Date).ToString("o")
                event            = "resource_summary"
                generation_id    = $ledger.generation_id
                conversation_id  = $ledger.conversation_id
                model            = $ledger.model
                tokens           = $ledger.tokens
                prompt_chars     = $ledger.prompt_chars
                response_chars   = $ledger.response_chars
                status           = "$($payload.status)"
                rules            = @($ledger.rules)
                skills_payload   = @($ledger.skills_payload)
                skills_matched   = @($ledger.skills_matched)
                skills_read      = @($ledger.skills_read)
                agents_requested = @($ledger.agents_requested)
                subagents        = @($ledger.subagents)
                hooks_configured = @($ledger.hooks_configured)
                hooks_executed   = @($ledger.hooks_executed)
                tracking_events  = @($ledger.tracking_events)
            }

            $resourcesLog = Get-CursorLogFilePath $projectRoot "cursor-resources"
            $line = $summary | ConvertTo-Json -Compress -Depth 12
            Add-Content -Path $resourcesLog -Value $line -Encoding UTF8

            $latestPath = Join-Path $ledgerDir "latest.json"
            ($summary | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $latestPath -Encoding UTF8
            Append-TrackingEvent $ledger "stop"
            $ledger = Add-HookExecutedEntry $ledger "stop" "log-resource-usage.ps1"
            $ledger.ts = (Get-Date).ToString("o")
            Write-ActiveLedgerAtomic -Path $activePath -Ledger $ledger
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
