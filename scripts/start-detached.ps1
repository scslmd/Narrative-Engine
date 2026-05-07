# Starts a long-running command as a detached process outside opencode's process tree.
# Uses WScript.Shell COM object to spawn a truly independent process that opencode
# cannot track, avoiding the child-process freeze (opencode issues #25306, #25360).
#
# Before starting, checks for orphaned or already-running server instances via manage-server.ps1.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\start-detached.ps1 -Command "python -m app.main"
#   powershell -ExecutionPolicy Bypass -File scripts\start-detached.ps1 -Command "python -m app.main" -Port 8000

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,

    [int]$Port = 8000,

    [string]$LogDir = "C:\Users\SLuh\AppData\Local\Temp\opencode"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure log directory exists
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$logOut = Join-Path $LogDir "bg-out.log"
$projectRoot = Split-Path $PSScriptRoot -Parent

# Check for existing server instances (kills orphans, refuses if alive)
$manageScript = Join-Path $projectRoot "scripts\manage-server.ps1"
if (Test-Path -LiteralPath $manageScript) {
    & $manageScript -Action ensure -Port $Port
    if (-not $?) {
        exit $LASTEXITCODE
    }
}

# Write a wrapper script that changes to project root and runs the command
$wrapperScript = Join-Path $LogDir "bg-wrapper.ps1"
Set-Content -LiteralPath $wrapperScript -Value @"
Set-Location "$projectRoot"
$Command 2>&1 | Out-File -Append -LiteralPath "$logOut" -Encoding UTF8
"@ -Encoding UTF8

# Use WScript.Shell to spawn a truly detached process (async, hidden window)
$shell = New-Object -ComObject WScript.Shell
$powershellExe = (Get-Process -Id $PID).MainModule.FileName
$cmdLine = "`"$powershellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$wrapperScript`""
$shell.Run($cmdLine, 0, $false) | Out-Null

Write-Host "Detached process started"
Write-Host "Logs: $logOut"
