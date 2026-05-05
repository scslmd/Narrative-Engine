@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
set PYTHON=%ROOT%\.venv\Scripts\python.exe
set HOST=127.0.0.1
set PORT=8000
set MODE=prod
set SKIP_BUILD=0

:: Resolve Python executable
if not exist "%PYTHON%" set PYTHON=python

:: Parse arguments
:args
if "%~1"=="" goto :done_args
if /i "%~1"=="--host" (
    if "%~2"=="" (
        echo ERROR: --host requires a value
        exit /b 1
    )
    set HOST=%~2
    shift
    shift
    goto :args
)
if /i "%~1"=="--port" (
    if "%~2"=="" (
        echo ERROR: --port requires a value
        exit /b 1
    )
    set PORT=%~2
    shift
    shift
    goto :args
)
if /i "%~1"=="--dev" set MODE=dev
if /i "%~1"=="--skip-build" set SKIP_BUILD=1
shift
goto :args
:done_args

:: Change to project root
cd /d "%ROOT%"

:: Validate Python can import required modules
echo Checking Python environment ...
"%PYTHON%" -c "import uvicorn, app.main" 2>nul
if errorlevel 1 (
    echo ERROR: Missing dependencies
    echo Install with: pip install -e .
    exit /b 1
)

:: ─── Development mode (2 windows, hot-reload) ───
if "%MODE%"=="dev" goto :dev_mode

:: ─── Production mode (single window, built frontend) ───

:: Check npm availability (unless skipping build)
if "%SKIP_BUILD%"=="0" (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ERROR: npm not found. Install Node.js and ensure it's in PATH.
        echo To skip building, use --skip-build.
        exit /b 1
    )
)

:: Build or verify frontend
if "%SKIP_BUILD%"=="1" goto :skip_build
echo [1/2] Building frontend ...
cd /d "%ROOT%frontend"
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Frontend build failed. See errors above.
    exit /b 1
)
cd /d "%ROOT%"
if not exist "%ROOT%frontend\dist\index.html" (
    echo.
    echo ERROR: Frontend build did not produce dist\index.html
    exit /b 1
)
echo   [OK] Frontend built
goto :continue_build

:skip_build
echo [1/2] Skipping frontend build (--skip-build)
if not exist "%ROOT%frontend\dist\index.html" (
    echo ERROR: No existing frontend build. Remove --skip-build or rebuild.
    exit /b 1
)
:continue_build

:: Check if port is already in use
netstat -ano | findstr ":%PORT%.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ERROR: Port %PORT% is already in use.
    echo   - Stop the existing server, or use --port to specify a different port.
    echo   - Find the process: netstat -ano | findstr ":%PORT%"
    echo.
    exit /b 1
)

:: Start uvicorn in current window
echo [2/2] Starting server ...
echo.
echo ============================================
echo   Narrative Engine
echo   URL: http://%HOST%:%PORT%
echo   API: http://%HOST%:%PORT%/docs
echo   Press Ctrl+C to stop
echo ============================================
echo.

"%PYTHON%" -m uvicorn app.main:build_app --factory --host %HOST% --port %PORT%
goto :eof

:: ─── Development mode ───
:dev_mode
echo.
echo Starting in development mode (hot-reload enabled) ...
echo.

:: Check npm availability for frontend dev server
where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found. Install Node.js and ensure it's in PATH.
    exit /b 1
)

:: Start backend with reload
echo [1/2] Starting backend ...
start "Narrative Engine Backend" cmd /k "cd /d ""%ROOT%"" && ""%PYTHON%"" -m uvicorn app.main:build_app --factory --reload --host %HOST% --port %PORT% & pause"

:: Start frontend dev server
echo [2/2] Starting frontend ...
start "Narrative Engine Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm run dev & pause"

echo.
echo ============================================
echo   Narrative Engine (dev mode)
echo   Frontend: http://localhost:5173
echo   Backend:  http://%HOST%:%PORT%
echo   API docs: http://%HOST%:%PORT%/docs
echo ============================================
echo.
echo   Press any key in the Backend or Frontend windows to stop them.
goto :eof
