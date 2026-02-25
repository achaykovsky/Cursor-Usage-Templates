# Sync Cursor config: agents, rules, hooks, skills
# Agents:  templates/agents/subagents or $env:USERPROFILE\.cursor\agents -> .cursor/agents
# Rules:   templates/rules/*.mdc -> .cursor/rules
# Hooks:   templates/hooks/* -> .cursor/hooks.json + .cursor/hooks/scripts/*.ps1
# Skills:  templates/skills/** -> .cursor/skills/**
# Usage:  .\sync-cursor.ps1                    # from project with templates/
#         .\sync-cursor.ps1 -ProjectRoot C:\proj  # global: sync into C:\proj

param([string]$ProjectRoot)

$ErrorActionPreference = "Stop"
$TemplatesRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
if (-not $ProjectRoot) {
    $ProjectRoot = $TemplatesRoot
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}
$RulesDest = Join-Path (Join-Path $ProjectRoot ".cursor") "rules"
$AgentsDest = Join-Path (Join-Path $ProjectRoot ".cursor") "agents"
$HooksDest = Join-Path (Join-Path $ProjectRoot ".cursor") "hooks"
$SkillsDest = Join-Path (Join-Path $ProjectRoot ".cursor") "skills"

$copied = 0

# Agents: .cursor/agents (for Settings > Subagents)
$AgentsSource = Join-Path (Join-Path $env:USERPROFILE ".cursor") "agents"
$TemplatesSubagents = Join-Path (Join-Path (Join-Path $TemplatesRoot "templates") "agents") "subagents"
$subagentSource = if (Test-Path $TemplatesSubagents) { $TemplatesSubagents } elseif (Test-Path $AgentsSource) { $AgentsSource } else { $null }
if ($subagentSource) {
    $null = New-Item -ItemType Directory -Path $AgentsDest -Force
    Get-ChildItem -Path $AgentsDest -Filter "*.md" -File -ErrorAction SilentlyContinue | Remove-Item -Force
    $subagentFiles = Get-ChildItem -Path $subagentSource -Filter "*.md" -File -ErrorAction SilentlyContinue
    foreach ($f in $subagentFiles) {
        Copy-Item -Path $f.FullName -Destination (Join-Path $AgentsDest $f.Name) -Force
        Write-Host "  OK  agents/$($f.Name)" -ForegroundColor Green
        $copied++
    }
}

# Rules: .cursor/rules
$TemplatesRules = Join-Path (Join-Path $TemplatesRoot "templates") "rules"
if (Test-Path $TemplatesRules) {
    $null = New-Item -ItemType Directory -Path $RulesDest -Force
    $ruleFiles = Get-ChildItem -Path $TemplatesRules -Filter "*.mdc" -File -ErrorAction SilentlyContinue
    foreach ($f in $ruleFiles) {
        Copy-Item -Path $f.FullName -Destination (Join-Path $RulesDest $f.Name) -Force
        Write-Host "  OK  rules/$($f.Name)" -ForegroundColor Green
        $copied++
    }
}

# Hooks: .cursor/hooks.json + .cursor/hooks/scripts/
$TemplatesHooks = Join-Path (Join-Path $TemplatesRoot "templates") "hooks"
$TemplatesHooksScripts = Join-Path $TemplatesHooks "scripts"
if (Test-Path $TemplatesHooks) {
    $null = New-Item -ItemType Directory -Path $HooksDest -Force
    $scriptsDest = Join-Path $HooksDest "scripts"
    $null = New-Item -ItemType Directory -Path $scriptsDest -Force
    Copy-Item -Path (Join-Path $TemplatesHooks "hooks.json") -Destination (Join-Path $ProjectRoot ".cursor") -Force -ErrorAction SilentlyContinue
    if (Test-Path (Join-Path $TemplatesHooks "hooks.json")) {
        Write-Host "  OK  hooks.json" -ForegroundColor Green
        $copied++
    }
    if (Test-Path $TemplatesHooksScripts) {
        $hookScripts = Get-ChildItem -Path $TemplatesHooksScripts -Filter "*.ps1" -File -ErrorAction SilentlyContinue
        foreach ($f in $hookScripts) {
            Copy-Item -Path $f.FullName -Destination (Join-Path $scriptsDest $f.Name) -Force
            Write-Host "  OK  hooks/scripts/$($f.Name)" -ForegroundColor Green
            $copied++
        }
    }
}

# Skills: templates/skills/** -> .cursor/skills/**
$TemplatesSkills = Join-Path (Join-Path $TemplatesRoot "templates") "skills"
if (Test-Path $TemplatesSkills) {
    $null = New-Item -ItemType Directory -Path $SkillsDest -Force
    $skillFiles = Get-ChildItem -Path $TemplatesSkills -Filter "SKILL.md" -Recurse -File -ErrorAction SilentlyContinue
    foreach ($f in $skillFiles) {
        $relPath = $f.FullName.Substring($TemplatesSkills.Length + 1)
        $destPath = Join-Path $SkillsDest $relPath
        $destDir = Split-Path -Parent $destPath
        $null = New-Item -ItemType Directory -Path $destDir -Force
        Copy-Item -Path $f.FullName -Destination $destPath -Force
        Write-Host "  OK  skills/$relPath" -ForegroundColor Green
        $copied++
    }
}

Write-Host ""
Write-Host "Synced $copied files to .cursor/" -ForegroundColor Cyan
