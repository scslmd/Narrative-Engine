@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
set PYTHON=%ROOT%\.venv\Scripts\python.exe
set HOST=127.0.0.1
set PORT=8000

:: Resolve Python executable
if not exist "%PYTHON%" set PYTHON=python

:: Parse arguments
:args
if "%~1"=="" goto :done_args
if /i "%~1"=="--host" (set HOST=%~2 & shift & shift & goto :args)
if /i "%~1"=="--port" (set PORT=%~2 & shift & shift & goto :args)
if /i "%~1"=="--full" (set FULL=1 & shift & goto :args)
shift & goto :args
:done_args

:: Validate Python can import required modules
echo Checking Python environment ...
%PYTHON% -c "import uvicorn, app.main" 2>nul
if errorlevel 1 (
    echo ERROR: Missing dependencies. Run: %PYTHON% -m pip install -e .
    goto :error
)

:: Start backend
echo Starting backend on %HOST%:%PORT% ...
start "Narrative Engine Backend" cmd /k "%PYTHON% -m uvicorn app.main:build_app --factory --reload --host %HOST% --port %PORT%"

:: Start frontend if --full flag or no arguments
if "%FULL%"=="1" goto :start_frontend
if "%~1"=="" goto :start_frontend
goto :done

:start_frontend
echo Starting frontend on localhost:5173 ...
start "Narrative Engine Frontend" cmd /k "cd /d \"%ROOT%frontend\" && npm install && npm run dev"
goto :done

:error
exit /b 1

:done
echo.
echo Backend: http://%HOST%:%PORT%
echo Frontend: http://localhost:5173
echo.
echo Usage: start_narrative_core.cmd [--host HOST] [--port PORT] [--full]
echo   --full    also starts the frontend (default when called with no args)
echo   --host    bind address (default: 127.0.0.1)
echo   --port    port number (default: 8000)
