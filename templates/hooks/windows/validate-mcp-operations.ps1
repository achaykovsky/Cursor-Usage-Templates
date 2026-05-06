# Guard MCP tool execution: allow read-only, ask on risky operations.

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

function Get-FirstString($data, $keys) {
    foreach ($key in $keys) {
        $prop = $data.PSObject.Properties[$key]
        if ($null -eq $prop -or $null -eq $prop.Value) { continue }
        $value = "$($prop.Value)".Trim()
        if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
    }
    return ""
}

$server = Get-FirstString $payload @("server", "server_name", "mcp_server")
$tool = Get-FirstString $payload @("tool_name", "toolName", "name", "mcp_tool_name")

if ([string]::IsNullOrWhiteSpace($tool)) {
    Write-Output '{"continue":true,"permission":"allow"}'
    exit 0
}

# Auth tool should be allowed so users can connect MCP servers.
if ($tool -eq "mcp_auth") {
    Write-Output '{"continue":true,"permission":"allow"}'
    exit 0
}

$readOnlyPattern = "(^|[_-])(get|list|read|fetch|search|query|select|describe|show|view)($|[_-])"
$riskyPattern = "(^|[_-])(create|update|delete|insert|drop|truncate|alter|write|upsert|deploy|publish|push|merge|close|assign|comment|tag|release|apply)($|[_-])"
$isReadOnly = $tool -match $readOnlyPattern
$isRisky = $tool -match $riskyPattern
$isDbServer = $server -match "(sql|postgres|mysql|database|snowflake|bigquery|databricks)"

if ($isRisky -and -not $isReadOnly) {
    $riskType = if ($isDbServer) { "DB-write or schema-change" } else { "state-changing" }
    $userMsg = "MCP tool '$tool' on server '$server' looks $riskType. Approve only if this action is explicitly requested."
    $agentMsg = "Default policy: MCP operations should be read-only unless user explicitly asks for writes/deploy/publish changes."
    $out = @{ continue = $true; permission = "ask"; user_message = $userMsg; agent_message = $agentMsg } | ConvertTo-Json -Compress
    Write-Output $out
    exit 0
}

Write-Output '{"continue":true,"permission":"allow"}'
exit 0
