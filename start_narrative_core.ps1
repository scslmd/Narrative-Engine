param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Full
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cmd = Join-Path $root "start_narrative_core.cmd"

if (-not (Test-Path $cmd)) {
    Write-Error "start_narrative_core.cmd not found at $cmd"
    exit 1
}

# Use cmd /c to bypass PowerShell execution policy
$args = @('--host', $Host, '--port', $Port)
if ($Full) { $args += '--full' }
cmd /c $cmd $args
