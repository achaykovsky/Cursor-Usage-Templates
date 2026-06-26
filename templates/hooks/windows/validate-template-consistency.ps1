# Validate template terminology/policy consistency before submit or after edits.
# Input (stdin): JSON with cwd, workspace_roots, hook_event_name
# Output (stdout): JSON {continue, permission, user_message, agent_message}

. (Join-Path $PSScriptRoot "hook-common.ps1")

$hookEvent = ""
$payload = $null
try {
    $raw = Read-HookStdin
    if ([string]::IsNullOrWhiteSpace($raw)) {
        Write-PromptAllow
        exit 0
    }

    $payload = Get-HookPayload $raw
    if (-not $payload) {
        Write-PromptAllow
        exit 0
    }

    $hookEvent = "$($payload.hook_event_name)"
    $cwd = $payload.cwd
    $roots = $payload.workspace_roots
    $root = if ($cwd) { "$cwd" } elseif ($roots -and $roots.Count -gt 0) { "$($roots[0])" } else { $null }
    if (-not $root -or -not (Test-Path $root)) {
        if ($hookEvent -eq "beforeSubmitPrompt") { Write-PromptAllow }
        exit 0
    }

    $templatesPath = Join-Path $root "templates"
    if (-not (Test-Path $templatesPath)) {
        if ($hookEvent -eq "beforeSubmitPrompt") { Write-PromptAllow }
        exit 0
    }

    if (-not (Get-Command rg -ErrorAction SilentlyContinue)) {
        if ($hookEvent -eq "beforeSubmitPrompt") { Write-PromptAllow }
        exit 0
    }

    $patterns = @(
        @{ pattern = '@agent\(FRONTEND\)'; message = "Legacy @agent(FRONTEND) reference found. Use FE_* invokes."; scope = "templates" },
        @{ pattern = '\| FRONTEND \|'; message = "Legacy FRONTEND table entry found. Use FE_* agents."; scope = "templates" },
        @{ pattern = 'frontend_engineer\.md'; message = "Legacy frontend_engineer.md reference found. Use fe_ui_engineer.md."; scope = "templates" },
        @{ pattern = 'authoritative security pass'; message = "Use 'primary in-template security review step' wording."; scope = "templates/skills" },
        @{ pattern = 'tabIndex for focus order'; message = "Use semantic DOM order guidance (avoid positive tabIndex)."; scope = "templates/rules" },
        @{ pattern = 'dev-secret-change-in-prod'; message = "Insecure secret default found in templates."; scope = "templates" }
    )

    $issues = @()
    foreach ($p in $patterns) {
        $target = Join-Path $root $p.scope
        if (-not (Test-Path $target)) { continue }
        $match = rg -n --glob "*.md" --glob "*.mdc" --glob "*.json" $p.pattern $target 2>$null | Select-Object -First 1
        if ($match) {
            $issues += "$($p.message) ($match)"
        }
    }

    if ($issues.Count -gt 0 -and $hookEvent -eq "beforeSubmitPrompt") {
        $msg = ($issues | Select-Object -First 3) -join " | "
        Write-HookJson @{
            continue      = $false
            permission    = "deny"
            user_message  = "Template consistency check failed: $msg"
            agent_message = "Update docs/rules/skills to canonical terminology and policy."
        }
        exit 0
    }

    if ($hookEvent -eq "beforeSubmitPrompt") {
        Write-PromptAllow
    }
} catch {
    Write-HookError $_
    if ($hookEvent -eq "beforeSubmitPrompt") {
        Write-PromptAllow
    }
} finally {
    Register-HookExecution -Payload $payload -ScriptFileName (Split-Path -Leaf $PSCommandPath)
}

exit 0
