@echo off
set ROOT=%~dp0
set PYTHON=%ROOT%\.venv\Scripts\python.exe
if exist "%PYTHON%" goto run
set PYTHON=python
:run
cd /d "%ROOT%"
%PYTHON% -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
