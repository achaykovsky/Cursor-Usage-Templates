# Block destructive shell commands. Maps to: suggest-commands-dont-run-destructive
# Input (stdin): JSON with command, cwd, hook_event_name
# Output (stdout): JSON with continue, permission, user_message, agent_message (Cursor uses snake_case)

$ErrorActionPreference = "Stop"
$raw = [System.Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { Write-Output '{"continue":true,"permission":"allow"}'; exit 0 }
$payload = $raw | ConvertFrom-Json
$cmd = if ($payload.command) { $payload.command.Trim() } else { "" }

$blocked = @(
    { $cmd -match 'rm\s+-rf\s+/' },           # rm -rf /
    { $cmd -match 'rm\s+-rf\s+/\s' },
    { $cmd -match 'rm\s+-rf\s+\$' },           # rm -rf $ (variable expansion)
    { $cmd -match ':\s*\(\s*\)\s*\{\s*:\s*\|' },  # fork bomb
    { $cmd -match 'git\s+reset\s+--hard\s+origin' },
    { $cmd -match 'DROP\s+(TABLE|DATABASE)\s+' },  # SQL DROP
    { $cmd -match 'DELETE\s+FROM\s+\w+\s*;?\s*$' } # DELETE FROM without WHERE (simple heuristic)
)

foreach ($pred in $blocked) {
    if (& $pred) {
        $out = @{
            continue = $false
            permission = "deny"
            user_message = "Blocked: destructive command not allowed."
            agent_message = "Command blocked by hook. Use suggest-commands-dont-run-destructive: suggest the command for the user to run instead."
        } | ConvertTo-Json -Compress
        Write-Output $out
        exit 0
    }
}

$out = @{ continue = $true; permission = "allow" } | ConvertTo-Json -Compress
Write-Output $out
