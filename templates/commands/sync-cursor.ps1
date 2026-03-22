# Sync Cursor config between project .cursor/, templates/, and %USERPROFILE%\.cursor\
#
# Modes:
#   TemplatesToLocal (default) — templates/* → project .cursor/; agents fallback: global → project
#   ToGlobal          — project .cursor/ → global %USERPROFILE%\.cursor\
#   FromGlobal        — global %USERPROFILE%\.cursor\ → project .cursor/
#
# Skips a category when the source has no files (never wipes global/project from an empty source).

param(
    [string] $ProjectRoot = "",
    [ValidateSet("TemplatesToLocal", "ToGlobal", "FromGlobal")]
    [string] $Mode = "TemplatesToLocal"
)

$ErrorActionPreference = "Stop"

if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
}

$LocalCursor = Join-Path $ProjectRoot ".cursor"
$GlobalCursor = Join-Path $env:USERPROFILE ".cursor"

$copied = 0

function Write-SyncLine {
    param([string] $Message)
    Write-Host "  OK  $Message" -ForegroundColor Green
}

function Sync-AgentsDir {
    param(
        [string] $SourceCursorDir,
        [string] $DestCursorDir
    )
    $src = Join-Path $SourceCursorDir "agents"
    if (-not (Test-Path $src)) { return 0 }
    $files = @(Get-ChildItem -Path $src -Filter "*.md" -File -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) { return 0 }

    $dest = Join-Path $DestCursorDir "agents"
    $null = New-Item -ItemType Directory -Path $dest -Force
    Get-ChildItem -Path $dest -Filter "*.md" -File -ErrorAction SilentlyContinue | Remove-Item -Force
    $n = 0
    foreach ($f in $files) {
        Copy-Item -Path $f.FullName -Destination (Join-Path $dest $f.Name) -Force
        Write-SyncLine "agents/$($f.Name)"
        $n++
    }
    return $n
}

function Sync-RulesDir {
    param(
        [string] $SourceCursorDir,
        [string] $DestCursorDir
    )
    $src = Join-Path $SourceCursorDir "rules"
    if (-not (Test-Path $src)) { return 0 }
    $files = @(Get-ChildItem -Path $src -Filter "*.mdc" -File -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) { return 0 }

    $dest = Join-Path $DestCursorDir "rules"
    $null = New-Item -ItemType Directory -Path $dest -Force
    Get-ChildItem -Path $dest -Filter "*.mdc" -File -ErrorAction SilentlyContinue | Remove-Item -Force
    $n = 0
    foreach ($f in $files) {
        Copy-Item -Path $f.FullName -Destination (Join-Path $dest $f.Name) -Force
        Write-SyncLine "rules/$($f.Name)"
        $n++
    }
    return $n
}

function Sync-HooksTree {
    param(
        [string] $SourceCursorDir,
        [string] $DestCursorDir
    )
    $n = 0
    $srcJson = Join-Path $SourceCursorDir "hooks.json"
    if (Test-Path $srcJson) {
        $null = New-Item -ItemType Directory -Path $DestCursorDir -Force
        Copy-Item -Path $srcJson -Destination (Join-Path $DestCursorDir "hooks.json") -Force
        Write-SyncLine "hooks.json"
        $n++
    }

    $srcScripts = Join-Path (Join-Path $SourceCursorDir "hooks") "scripts"
    if (-not (Test-Path $srcScripts)) { return $n }

    $scriptFiles = @(Get-ChildItem -Path $srcScripts -Filter "*.ps1" -File -ErrorAction SilentlyContinue)
    if ($scriptFiles.Count -eq 0) { return $n }

    $destHooks = Join-Path $DestCursorDir "hooks"
    $destScripts = Join-Path $destHooks "scripts"
    $null = New-Item -ItemType Directory -Path $destScripts -Force

    Get-ChildItem -Path $destScripts -Filter "*.ps1" -File -ErrorAction SilentlyContinue | Remove-Item -Force
    foreach ($f in $scriptFiles) {
        Copy-Item -Path $f.FullName -Destination (Join-Path $destScripts $f.Name) -Force
        Write-SyncLine "hooks/scripts/$($f.Name)"
        $n++
    }
    return $n
}

function Sync-SkillsTree {
    param(
        [string] $SourceSkillsRoot,
        [string] $DestSkillsRoot
    )
    if (-not (Test-Path $SourceSkillsRoot)) { return 0 }
    $skillFiles = @(Get-ChildItem -Path $SourceSkillsRoot -Filter "SKILL.md" -Recurse -File -ErrorAction SilentlyContinue)
    if ($skillFiles.Count -eq 0) { return 0 }

    $null = New-Item -ItemType Directory -Path $DestSkillsRoot -Force
    $n = 0
    foreach ($f in $skillFiles) {
        $relPath = $f.FullName.Substring($SourceSkillsRoot.Length + 1)
        $destPath = Join-Path $DestSkillsRoot $relPath
        $destDir = Split-Path -Parent $destPath
        $null = New-Item -ItemType Directory -Path $destDir -Force
        Copy-Item -Path $f.FullName -Destination $destPath -Force
        Write-SyncLine "skills/$relPath"
        $n++
    }
    return $n
}

switch ($Mode) {
    "ToGlobal" {
        Write-Host "Mode: project .cursor/ -> $GlobalCursor" -ForegroundColor Yellow
        $copied += Sync-AgentsDir -SourceCursorDir $LocalCursor -DestCursorDir $GlobalCursor
        $copied += Sync-RulesDir -SourceCursorDir $LocalCursor -DestCursorDir $GlobalCursor
        $copied += Sync-HooksTree -SourceCursorDir $LocalCursor -DestCursorDir $GlobalCursor
        $copied += Sync-SkillsTree `
            -SourceSkillsRoot (Join-Path $LocalCursor "skills") `
            -DestSkillsRoot (Join-Path $GlobalCursor "skills")
    }
    "FromGlobal" {
        Write-Host "Mode: $GlobalCursor -> project .cursor/" -ForegroundColor Yellow
        $copied += Sync-AgentsDir -SourceCursorDir $GlobalCursor -DestCursorDir $LocalCursor
        $copied += Sync-RulesDir -SourceCursorDir $GlobalCursor -DestCursorDir $LocalCursor
        $copied += Sync-HooksTree -SourceCursorDir $GlobalCursor -DestCursorDir $LocalCursor
        $copied += Sync-SkillsTree `
            -SourceSkillsRoot (Join-Path $GlobalCursor "skills") `
            -DestSkillsRoot (Join-Path $LocalCursor "skills")
    }
    "TemplatesToLocal" {
        Write-Host "Mode: templates/ (+ agent fallback) -> project .cursor/" -ForegroundColor Yellow

        # Agents: templates/agents/subagents or global agents -> .cursor/agents
        $AgentsSourceGlobal = Join-Path $GlobalCursor "agents"
        $TemplatesSubagents = Join-Path (Join-Path (Join-Path $ProjectRoot "templates") "agents") "subagents"
        $subagentSource = if (Test-Path $TemplatesSubagents) { $TemplatesSubagents } elseif (Test-Path $AgentsSourceGlobal) { $AgentsSourceGlobal } else { $null }
        if ($subagentSource) {
            $destAgents = Join-Path $LocalCursor "agents"
            $null = New-Item -ItemType Directory -Path $destAgents -Force
            Get-ChildItem -Path $destAgents -Filter "*.md" -File -ErrorAction SilentlyContinue | Remove-Item -Force
            $subagentFiles = Get-ChildItem -Path $subagentSource -Filter "*.md" -File -ErrorAction SilentlyContinue
            foreach ($f in $subagentFiles) {
                Copy-Item -Path $f.FullName -Destination (Join-Path $destAgents $f.Name) -Force
                Write-SyncLine "agents/$($f.Name)"
                $copied++
            }
        }

        $TemplatesRules = Join-Path (Join-Path $ProjectRoot "templates") "rules"
        if (Test-Path $TemplatesRules) {
            $ruleFiles = Get-ChildItem -Path $TemplatesRules -Filter "*.mdc" -File -ErrorAction SilentlyContinue
            if ($ruleFiles) {
                $destRules = Join-Path $LocalCursor "rules"
                $null = New-Item -ItemType Directory -Path $destRules -Force
                foreach ($f in $ruleFiles) {
                    Copy-Item -Path $f.FullName -Destination (Join-Path $destRules $f.Name) -Force
                    Write-SyncLine "rules/$($f.Name)"
                    $copied++
                }
            }
        }

        $TemplatesHooks = Join-Path (Join-Path $ProjectRoot "templates") "hooks"
        $TemplatesHooksScripts = Join-Path $TemplatesHooks "scripts"
        if (Test-Path $TemplatesHooks) {
            $destHooks = Join-Path $LocalCursor "hooks"
            $scriptsDest = Join-Path $destHooks "scripts"
            $null = New-Item -ItemType Directory -Path $destHooks -Force
            $null = New-Item -ItemType Directory -Path $scriptsDest -Force
            $hooksJson = Join-Path $TemplatesHooks "hooks.json"
            if (Test-Path $hooksJson) {
                Copy-Item -Path $hooksJson -Destination (Join-Path $LocalCursor "hooks.json") -Force
                Write-SyncLine "hooks.json"
                $copied++
            }
            if (Test-Path $TemplatesHooksScripts) {
                $hookScripts = Get-ChildItem -Path $TemplatesHooksScripts -Filter "*.ps1" -File -ErrorAction SilentlyContinue
                foreach ($f in $hookScripts) {
                    Copy-Item -Path $f.FullName -Destination (Join-Path $scriptsDest $f.Name) -Force
                    Write-SyncLine "hooks/scripts/$($f.Name)"
                    $copied++
                }
            }
        }

        $TemplatesSkills = Join-Path (Join-Path $ProjectRoot "templates") "skills"
        if (Test-Path $TemplatesSkills) {
            $destSkills = Join-Path $LocalCursor "skills"
            $skillFiles = Get-ChildItem -Path $TemplatesSkills -Filter "SKILL.md" -Recurse -File -ErrorAction SilentlyContinue
            foreach ($f in $skillFiles) {
                $relPath = $f.FullName.Substring($TemplatesSkills.Length + 1)
                $destPath = Join-Path $destSkills $relPath
                $destDir = Split-Path -Parent $destPath
                $null = New-Item -ItemType Directory -Path $destDir -Force
                Copy-Item -Path $f.FullName -Destination $destPath -Force
                Write-SyncLine "skills/$relPath"
                $copied++
            }
        }
    }
}

Write-Host ""
Write-Host "Synced $copied files ($Mode)" -ForegroundColor Cyan
