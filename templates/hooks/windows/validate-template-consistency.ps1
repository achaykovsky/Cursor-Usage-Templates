# Validate template terminology/policy consistency before submit or after edits.
# Input (stdin): JSON with cwd, workspace_roots, hook_event_name
# Output (stdout): JSON {continue, permission, user_message, agent_message}

$ErrorActionPreference = "SilentlyContinue"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }
$payload = $raw | ConvertFrom-Json
$cwd = $payload.cwd
$roots = $payload.workspace_roots
$root = if ($cwd) { $cwd } elseif ($roots) { $roots[0] } else { $null }
if (-not $root -or -not (Test-Path $root)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }

$templatesPath = Join-Path $root "templates"
if (-not (Test-Path $templatesPath)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }

if (-not (Get-Command rg -ErrorAction SilentlyContinue)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }

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

if ($issues.Count -gt 0) {
    $msg = ($issues | Select-Object -First 3) -join " | "
    $out = @{
        continue = $false
        permission = "deny"
        user_message = "Template consistency check failed: $msg"
        agent_message = "Update docs/rules/skills to canonical terminology and policy."
    } | ConvertTo-Json -Compress
    Write-Output $out
    exit 0
}

Write-Output '{"continue":true,"permission":"allow"}'
exit 0
