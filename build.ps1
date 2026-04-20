param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\build.ps1 [-SkipFrontend] [-SkipBackend] [-Help]"
    Write-Host ""
    Write-Host "Full build: frontend (typecheck + lint + build) and backend tests."
    Write-Host ""
    Write-Host "Flags:"
    Write-Host "  -SkipFrontend    Skip frontend checks"
    Write-Host "  -SkipBackend     Skip backend tests"
    Write-Host "  -Help            Show this help"
    exit 0
}

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root ".venv\Scripts\python.exe"
$frontend = Join-Path $root "frontend"
$exitCode = 0

# Resolve Python
if (-not (Test-Path (Join-Path $venv "python.exe"))) {
    $python = "python"
} else {
    $python = $venv
}

if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  Frontend" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""

    Push-Location $frontend

    # Type check
    Write-Host "  - Type check ..."
    try {
        npx --no-install tsc --noEmit
        Write-Host "  [OK] Frontend typecheck" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] Frontend typecheck" -ForegroundColor Red
        $exitCode = 1
    }
    Write-Host ""

    # Lint
    Write-Host "  - Lint ..."
    try {
        npx --no-install eslint .
        Write-Host "  [OK] Frontend lint" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] Frontend lint" -ForegroundColor Red
        $exitCode = 1
    }
    Write-Host ""

    # Build
    Write-Host "  - Build ..."
    try {
        npx --no-install vite build
        Write-Host "  [OK] Frontend build" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] Frontend build" -ForegroundColor Red
        $exitCode = 1
    }
    Write-Host ""

    Pop-Location
}

if (-not $SkipBackend) {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  Backend Tests" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "  - Running pytest ..."
    Push-Location $root
    try {
        & $python -m pytest -q -p no:cacheprovider --tb=line
        Write-Host ""
        Write-Host "  [OK] Backend tests" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "  [FAIL] Backend tests" -ForegroundColor Red
        $exitCode = 1
    }
    Pop-Location
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
if ($exitCode -eq 0) {
    Write-Host "  PASS" -ForegroundColor Green
} else {
    Write-Host "  FAIL" -ForegroundColor Red
}
Write-Host "============================================" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })
Write-Host ""

exit $exitCode
