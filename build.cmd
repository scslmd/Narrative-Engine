@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
set VENV=%ROOT%.venv\Scripts\python.exe
set FRONTEND=%ROOT%frontend
set EXIT_CODE=0

:: Resolve Python executable
if not exist "%VENV%\python.exe" set VENV=python

echo ============================================
echo   Narrative Engine - Full Build
echo ============================================
echo.

:: ─── Frontend ───
echo [1/3] Frontend ...
echo.

cd /d "%FRONTEND%"

echo   - Type check ...
call npx --no-install tsc --noEmit 2>&1
if errorlevel 1 (
    echo   [FAIL] Frontend typecheck
    set EXIT_CODE=1
) else (
    echo   [OK] Frontend typecheck
)

echo.
echo   - Lint ...
call npx --no-install eslint . 2>&1
if errorlevel 1 (
    echo   [FAIL] Frontend lint
    set EXIT_CODE=1
) else (
    echo   [OK] Frontend lint
)

echo.
echo   - Build ...
call npx --no-install vite build 2>&1
if errorlevel 1 (
    echo   [FAIL] Frontend build
    set EXIT_CODE=1
) else (
    echo   [OK] Frontend build
)

echo.

:: ─── Backend ───
echo [2/3] Backend tests ...
echo.

cd /d "%ROOT%"
"%VENV%" -m pytest -q -p no:cacheprovider --tb=line 2>&1
if errorlevel 1 (
    echo   [FAIL] Backend tests
    set EXIT_CODE=1
) else (
    echo   [OK] Backend tests
)

echo.

:: ─── Done ───
echo ============================================
if %EXIT_CODE% equ 0 (
    echo   PASS
) else (
    echo   FAIL
)
echo ============================================

exit /b %EXIT_CODE%
