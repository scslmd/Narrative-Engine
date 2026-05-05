param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Dev,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cmd = Join-Path $root "start_narrative_core.cmd"

if (-not (Test-Path $cmd)) {
    Write-Error "start_narrative_core.cmd not found at $cmd"
    exit 1
}

# Build argument list
$args = @('--host', $Host, '--port', $Port)
if ($Dev) { $args += '--dev' }
if ($SkipBuild) { $args += '--skip-build' }

cmd /c $cmd $args
