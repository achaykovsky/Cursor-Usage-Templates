# Output git status/diff and suggest commit groups on session stop. Maps to: prepare-atomic-commit
# Informational only—output goes to Hooks channel. User can run prepare-atomic-commit skill for full analysis.

$ErrorActionPreference = "SilentlyContinue"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
$payload = $raw | ConvertFrom-Json
$roots = $payload.workspace_roots
if (-not $roots) { exit 0 }

$root = $roots[0]
if (-not (Test-Path (Join-Path $root ".git"))) { exit 0 }

Push-Location $root
try {
    $status = git status -sb 2>$null
    $diffStat = git diff --stat 2>$null
    $staged = git diff --cached --stat 2>$null
    $stagedNames = git diff --cached --name-only 2>$null
    $unstagedNames = git diff --name-only 2>$null

    if ($status -or $diffStat -or $staged) {
        Write-Host "`n--- Session stopped. Git summary ---"
        if ($status) { Write-Host $status }
        if ($staged) { Write-Host "`nStaged:"; Write-Host $staged }
        if ($diffStat) { Write-Host "`nUnstaged:"; Write-Host $diffStat }

        # Suggest commit groups (suggest-commit-split)
        $allFiles = @()
        if ($stagedNames) { $allFiles += $stagedNames }
        if ($unstagedNames) { $allFiles += $unstagedNames }
        $allFiles = $allFiles | Select-Object -Unique

        if ($allFiles.Count -gt 1) {
            $groups = @{}
            foreach ($f in $allFiles) {
                $group = "chore"
                if ($f -match 'test[s_]?/|_test\.|\.test\.|spec\.') { $group = "test" }
                elseif ($f -match 'docs?/|README|\.md$') { $group = "docs" }
                elseif ($f -match '\.(py|go|ts|tsx|js|jsx)$' -and $f -notmatch 'test') { $group = "feat" }
                elseif ($f -match '\.(json|yaml|yml)$|pyproject|package\.json') { $group = "chore" }
                if (-not $groups[$group]) { $groups[$group] = @() }
                $groups[$group] += $f
            }
            if ($groups.Keys.Count -gt 1) {
                Write-Host "`n--- Suggested commit split ---"
                foreach ($key in @("feat","fix","docs","test","chore")) {
                    if ($groups[$key]) {
                        $msg = switch ($key) { "feat" {"feat: add or update feature"}; "fix" {"fix: fix bug"}; "docs" {"docs: update documentation"}; "test" {"test: add or update tests"}; default {"chore: update config or misc"}}
                        Write-Host "`n$key`: $msg"
                        $groups[$key] | ForEach-Object { Write-Host "  $_" }
                    }
                }
            }
        }
        Write-Host "`nUse @prepare-atomic-commit for full commit grouping."
    }
} finally { Pop-Location }
exit 0
