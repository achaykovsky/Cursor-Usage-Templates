# Log prompt-level context for beforeSubmitPrompt.
# Captures: timestamp, prompt, observed skill/rule fields, and routing.py predictions.

. (Join-Path $PSScriptRoot "hook-common.ps1")

$parseError = $null
$payload = $null
try {
    $stdinBytes = Read-HookStdinBytes
    if (-not $stdinBytes -or $stdinBytes.Length -eq 0) {
        Write-PromptAllow
        exit 0
    }

    $payload = Get-HookPayloadFromBytes $stdinBytes
    if (-not $payload) {
        try {
            $fallbackText = (Get-HookStdinTextCandidates $stdinBytes | Select-Object -First 1)
            if (-not [string]::IsNullOrWhiteSpace($fallbackText)) {
                $null = $fallbackText | ConvertFrom-Json
            }
        } catch {
            $parseError = $_.Exception.Message
        }
    }

    $hookEvent = if ($payload) { $payload.hook_event_name } else { $null }
    if ($hookEvent -and $hookEvent -ne "beforeSubmitPrompt") {
        exit 0
    }

    $projectRoot = Resolve-ProjectRoot $payload
    if (-not $projectRoot) {
        Write-HookError "log-prompt-context: could not resolve project root"
        Write-PromptAllow
        exit 0
    }

    $logFile = Get-CursorLogFilePath $projectRoot "cursor-prompt-context"

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
    Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
    Write-PromptAllow
}

exit 0
