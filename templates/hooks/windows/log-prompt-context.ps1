# Log prompt-level context for beforeSubmitPrompt.
# Captures: timestamp, prompt, observed skill/rule fields, and predicted fallback.

. (Join-Path $PSScriptRoot "hook-common.ps1")

function Get-PredictedSkills([string]$text) {
    if ([string]::IsNullOrWhiteSpace($text)) { return @() }

    $p = $text.ToLowerInvariant()
    $out = New-Object System.Collections.Generic.List[string]

    if ($p -match "fastapi|flask|endpoint|openapi|swagger|api") { $out.Add("api-workflows/implement-or-extend-api-surface") }
    if ($p -match "version|deprecat|backward|breaking change") { $out.Add("api-workflows/check-api-backward-compatibility") }
    if ($p -match "bug|broken|fix|error|exception|failing") { $out.Add("code-workflows/fix-bug-systematically") }
    if ($p -match "refactor|cleanup|rename") { $out.Add("code-workflows/refactor-safely") }
    if ($p -match "test|pytest|coverage|assert") { $out.Add("testing-workflows/add-tests-for-change") }
    if ($p -match "security|secret|owasp|xss|sql injection|auth") { $out.Add("security-workflows/security-scan-changes") }
    if ($p -match "deploy|release|pipeline|ci/cd|terraform|cloudformation") { $out.Add("devops-workflows/implement-ci-cd-pipeline") }
    if ($p -match "doc|readme|adr|documentation") { $out.Add("docs-workflows/keep-docs-in-sync-with-code") }

    return @($out | Select-Object -Unique)
}

function Get-PredictedRules([string]$text) {
    if ([string]::IsNullOrWhiteSpace($text)) { return @("security.mdc", "token-efficiency.mdc", "ai-guardrails.mdc") }

    $p = $text.ToLowerInvariant()
    $out = New-Object System.Collections.Generic.List[string]
    $out.Add("security.mdc")
    $out.Add("token-efficiency.mdc")
    $out.Add("ai-guardrails.mdc")

    if ($p -match "python|pytest|poetry|fastapi|django") { $out.Add("python-backend.mdc") }
    if ($p -match "\bgo\b|golang") { $out.Add("go-backend.mdc") }
    if ($p -match "react|tsx|frontend|ui|ux|css") { $out.Add("frontend.mdc") }
    if ($p -match "api|openapi|endpoint|swagger") { $out.Add("api-contract.mdc") }
    if ($p -match "test|coverage|assert") { $out.Add("testing.mdc") }
    if ($p -match "perf|latency|optimi") { $out.Add("performance.mdc") }
    if ($p -match "doc|readme|adr|markdown") { $out.Add("documentation.mdc") }

    return @($out | Select-Object -Unique)
}

$parseError = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-PromptAllow
        exit 0
    }

    $payload = $null
    try {
        $payload = $raw | ConvertFrom-Json
    } catch {
        $parseError = $_.Exception.Message
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
    if ($skills.Count -eq 0) {
        $predictedSkills = Get-PredictedSkills $prompt
    }

    $predictedRules = @()
    if ($rules.Count -eq 0) {
        $predictedRules = Get-PredictedRules $prompt
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
        prompt = $prompt
        skills = if ($skills.Count -gt 0) { $skills } else { @() }
        rules = if ($rules.Count -gt 0) { $rules } else { @() }
        predicted_skills = $predictedSkills
        predicted_rules = $predictedRules
        source = [ordered]@{
            has_payload_json = [bool]$payload
            parse_error = $parseError
            payload_key_count = $payloadKeys.Count
            payload_keys = $payloadKeys
            prompt_field_found = -not [string]::IsNullOrWhiteSpace($prompt)
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
