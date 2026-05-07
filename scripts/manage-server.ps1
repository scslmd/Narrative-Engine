param(
    [ValidateSet('check', 'kill', 'ensure')]
    [string]$Action = 'check',

    [int]$Port = 8000,

    [string]$LogDir = "C:\Users\SLuh\AppData\Local\Temp\opencode"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent
$stateDir = Join-Path $projectRoot "data\state"
$pidFile = Join-Path $stateDir ".narrative_server.pid"
$healthUrl = "http://127.0.0.1:$Port/health/"

# Ensure state directory exists
if (-not (Test-Path -LiteralPath $stateDir)) {
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
}

# --- Find server processes ---
$serverPids = @()
$allPython = @(Get-Process python -EA SilentlyContinue)
foreach ($p in $allPython) {
    try {
        $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -EA SilentlyContinue
        if ($cim.CommandLine -match '\-m\s+app\.main') {
            $serverPids += $p.Id
        }
    } catch {}
}

# --- Check health endpoint ---
$healthAlive = $false
try {
    $r = curl.exe -s --max-time 3 $healthUrl 2>$null
    if ($r -match '"status"' -or $r -match 'ok' -or $r -match 'healthy') {
        $healthAlive = $true
    }
} catch {}

# --- Determine status ---
$status = 'stopped'
if ($serverPids.Count -gt 0 -and $healthAlive) {
    $status = 'running'
} elseif ($serverPids.Count -gt 0 -and -not $healthAlive) {
    $status = 'orphaned'
}

# --- Clean stale PID file ---
if (Test-Path -LiteralPath $pidFile) {
    try {
        $filePid = [int]((Get-Content -LiteralPath $pidFile -Raw).Trim())
        $pidStillAlive = Get-Process -Id $filePid -EA SilentlyContinue
        if (-not $pidStillAlive) {
            Remove-Item -LiteralPath $pidFile -EA SilentlyContinue
        }
    } catch {
        Remove-Item -LiteralPath $pidFile -EA SilentlyContinue
    }
}

# --- Execute action ---
switch ($Action) {
    'check' {
        switch ($status) {
            'running' {
                Write-Host "Server is running (PID(s): $($serverPids -join ', '))"
                Write-Host "Health: $healthUrl"
                exit 0
            }
            'orphaned' {
                Write-Host "Orphaned server process detected (PID(s): $($serverPids -join ', '))"
                Write-Host "Use -Action kill to remove, or -Action ensure to clean and start."
                exit 1
            }
            'stopped' {
                Write-Host "No server running on port $Port"
                exit 0
            }
        }
    }

    'kill' {
        if ($status -eq 'stopped') {
            Write-Host "Nothing to kill"
            if (Test-Path -LiteralPath $pidFile) {
                Remove-Item -LiteralPath $pidFile -EA SilentlyContinue
            }
            exit 0
        }

        foreach ($procId in $serverPids) {
            try {
                Stop-Process -Id $procId -Force
                Write-Host "Killed process $procId"
            } catch {
                Write-Host "Could not kill process $procId (may have already exited)"
            }
        }

        if (Test-Path -LiteralPath $pidFile) {
            try {
                $filePid = [int]((Get-Content -LiteralPath $pidFile -Raw).Trim())
                Stop-Process -Id $filePid -Force -EA SilentlyContinue
            } catch {}
            Remove-Item -LiteralPath $pidFile -EA SilentlyContinue
        }

        Start-Sleep 1
        Write-Host "Server stopped"
        exit 0
    }

    'ensure' {
        if ($status -eq 'running') {
            Write-Host "ERROR: Server already running on port $Port (PID(s): $($serverPids -join ', '))"
            Write-Host "  Stop it first: powershell -ExecutionPolicy Bypass -File scripts\manage-server.ps1 -Action kill -Port $Port"
            exit 3
        }

        if ($status -eq 'orphaned') {
            Write-Host "Cleaning orphaned process(es): $($serverPids -join ', ')"
            foreach ($procId in $serverPids) {
                try {
                    Stop-Process -Id $procId -Force
                } catch {}
            }
            Start-Sleep 1
        }

        if (Test-Path -LiteralPath $pidFile) {
            Remove-Item -LiteralPath $pidFile -EA SilentlyContinue
        }
        exit 0
    }
}
