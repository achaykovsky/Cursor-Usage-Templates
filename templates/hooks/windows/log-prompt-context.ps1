# Log prompt-level context for beforeSubmitPrompt.
# Captures: timestamp, prompt, observed skill/rule fields, and routing.py predictions.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$parseError = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-PromptAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    if (-not $payload) {
        try {
            $null = $raw | ConvertFrom-Json
        } catch {
            $parseError = $_.Exception.Message
        }
    }

    $hookEvent = if ($payload) { $payload.hook_event_name } else { $null }
    if ($hookEvent -and $hookEvent -ne "beforeSubmitPrompt") {
        exit 0
    }

    $projectRoot = Get-ProjectRootFromPayload $payload
    if (-not $projectRoot) {
        $cwdRoot = & git rev-parse --show-toplevel 2>$null
        if ($cwdRoot) { $projectRoot = $cwdRoot }
    }
    if (-not $projectRoot) {
        Write-PromptAllow
        exit 0
    }

    $logDir = Join-Path (Join-Path $projectRoot ".cursor") "logs"
    $null = New-Item -ItemType Directory -Path $logDir -Force -ErrorAction SilentlyContinue
    $logFile = Join-Path $logDir ("cursor-prompt-context-{0:yyyy-MM-dd}.jsonl" -f (Get-Date))

    $prompt = Get-FirstString $payload @(
        "prompt",
        "user_prompt",
        "content",
        "text",
        "input",
        "message"
    )
    if ($prompt.Length -gt 50000) {
        $prompt = $prompt.Substring(0, 50000) + "...[truncated]"
    }
    $prompt = Invoke-RedactText $prompt $projectRoot

    $skills = Get-FirstList $payload @(
        "skills",
        "used_skills",
        "applied_skills",
        "matched_skills",
        "selected_skills",
        "skill_names"
    )

    $rules = Get-FirstList $payload @(
        "rules",
        "used_rules",
        "applied_rules",
        "matched_rules",
        "active_rules",
        "rule_names"
    )

    $predictedSkills = @()
    $predictedRules = @()
    if ($skills.Count -eq 0 -or $rules.Count -eq 0) {
        $prediction = Get-PromptPredictions $prompt $projectRoot
        if ($skills.Count -eq 0) {
            $predictedSkills = @($prediction.predicted_skills)
        }
        if ($rules.Count -eq 0) {
            $predictedRules = @($prediction.predicted_rules)
        }
    }

    $payloadKeys = @()
    if ($payload) {
        $payloadKeys = @($payload.PSObject.Properties.Name | Sort-Object)
    }

    $entry = [ordered]@{
        ts = (Get-Date).ToString("o")
        event = if ($hookEvent) { $hookEvent } else { "beforeSubmitPrompt" }
        conversation_id = $payload.conversation_id
        generation_id = $payload.generation_id
        model = Get-PayloadModel $payload
        prompt = $prompt
        skills = @($skills)
        rules = @($rules)
        predicted_skills = @($predictedSkills)
        predicted_rules = @($predictedRules)
        source = [ordered]@{
            has_payload_json = [bool]$payload
            parse_error = $parseError
            payload_key_count = $payloadKeys.Count
            payload_keys = $payloadKeys
            prompt_field_found = -not [string]::IsNullOrWhiteSpace($prompt)
            prediction_source = "routing.py"
        }
    }

    $line = $entry | ConvertTo-Json -Compress -Depth 8
    Add-Content -Path $logFile -Value $line -Encoding UTF8 -ErrorAction SilentlyContinue
} catch {
    Write-HookError $_
} finally {
    Write-PromptAllow
}

exit 0
