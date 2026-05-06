# Guard risky database shell operations. Ask for confirmation or deny obviously destructive patterns.

$ErrorActionPreference = "Stop"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    Write-Output '{"continue":true,"permission":"allow"}'
    exit 0
}

try {
    $payload = $raw | ConvertFrom-Json
} catch {
    Write-Output '{"continue":true,"permission":"allow"}'
    exit 0
}

$cmd = if ($payload.command) { "$($payload.command)".Trim() } else { "" }
if ([string]::IsNullOrWhiteSpace($cmd)) {
    Write-Output '{"continue":true,"permission":"allow"}'
    exit 0
}

$isDbContext = $cmd -match '(?i)\b(psql|mysql|mariadb|sqlite3|sqlcmd|mongosh|mongo|alembic|flyway|liquibase|dbmate|prisma|typeorm|knex|sequelize)\b'
if (-not $isDbContext -and $cmd -notmatch '(?i)\b(select|insert|update|delete|drop|truncate|alter|create\s+table)\b') {
    Write-Output '{"continue":true,"permission":"allow"}'
    exit 0
}

$denyPatterns = @(
    '(?i)\bdrop\s+database\b',
    '(?i)\btruncate\s+table\b',
    '(?i)\bdrop\s+table\b',
    '(?i)\bdelete\s+from\s+\w+\s*;?\s*$',
    '(?i)\balembic\s+downgrade\s+-1\b',
    '(?i)\bflyway\s+clean\b',
    '(?i)\bliquibase\s+rollback\b',
    '(?i)\bprisma\s+migrate\s+reset\b'
)

foreach ($pattern in $denyPatterns) {
    if ($cmd -match $pattern) {
        $out = @{
            continue = $false
            permission = "deny"
            user_message = "Blocked: destructive database operation detected."
            agent_message = "DB safety hook blocked a destructive command. Ask the user explicitly and provide a safer plan (backup + rollback + scoped target)."
        } | ConvertTo-Json -Compress
        Write-Output $out
        exit 0
    }
}

$askPatterns = @(
    '(?i)\bdelete\s+from\b',
    '(?i)\bupdate\s+\w+\s+set\b',
    '(?i)\binsert\s+into\b',
    '(?i)\balter\s+table\b',
    '(?i)\bcreate\s+table\b',
    '(?i)\bmigrate\b',
    '(?i)\bapply\b'
)

foreach ($pattern in $askPatterns) {
    if ($cmd -match $pattern) {
        $out = @{
            continue = $true
            permission = "ask"
            user_message = "Database write/schema command detected. Confirm this action is explicitly requested and scoped to the intended environment."
            agent_message = "DB safety hook: require explicit user approval for write/schema operations. Prefer read-only validation first."
        } | ConvertTo-Json -Compress
        Write-Output $out
        exit 0
    }
}

Write-Output '{"continue":true,"permission":"allow"}'
exit 0
