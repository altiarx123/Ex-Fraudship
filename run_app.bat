@echo off
rem run_app.bat - Start the app stack on Windows
rem
rem Behavior:
rem  - If Docker is in PATH, runs `docker compose up --build` in a new PowerShell window.
rem  - Otherwise starts three dev windows:
rem      * Mock Backend (backend_mock) on port 8000
rem      * Frontend (Vite) at project root
rem      * Python Backend (backend) using a local venv

setlocal ENABLEDELAYEDEXPANSION

rem Resolve script directory (no trailing backslash)
set SCRIPT_DIR=%~dp0
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

where docker >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Docker detected. Starting services with Docker Compose (clean compose)...
    start "Docker Compose" powershell -NoExit -Command "Set-Location -LiteralPath '%SCRIPT_DIR%'; docker compose -f docker-compose.yml up --build"
    goto end
)

echo Docker not found. Falling back to local dev servers.

rem Start Mock Backend (opens new PowerShell window)
start "Mock Backend" powershell -NoExit -Command "Set-Location -LiteralPath '%SCRIPT_DIR%\backend_mock'; npx kill-port 8000; npm install --no-audit; npm start"

rem Start Frontend (Vite) (opens new PowerShell window)
start "Frontend" powershell -NoExit -Command "Set-Location -LiteralPath '%SCRIPT_DIR%'; npm install --no-audit; npm run dev"

rem Start Python Backend (venv). This will create a venv if missing, install requirements and run uvicorn.
start "Python Backend" powershell -NoExit -Command "Set-Location -LiteralPath '%SCRIPT_DIR%\backend'; if (!(Test-Path -LiteralPath '.venv')) { python -m venv .venv }; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; python -m pip install -r requirements.txt; python -m uvicorn backend.main:app --reload --port 8000"

:end
endlocal
echo Launched startup windows. Check each window for logs.
