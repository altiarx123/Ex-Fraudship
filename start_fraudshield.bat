@echo off
rem start_fraudshield.bat - Launch E-X FraudShield Streamlit app
rem
rem Features:
rem  1. Creates/activates local .venv if missing
rem  2. Installs/updates dependencies from requirements.txt (first run or if FORCE_DEPS=1)
rem  3. Runs `streamlit run app.py` and passes along any extra args
rem  4. Writes a timestamped log (optional) if ENABLE_LOG=1
rem
rem Usage examples:
rem   start_fraudshield.bat
rem   start_fraudshield.bat --server.port 8502
rem   set ENABLE_LOG=1 & start_fraudshield.bat
rem   set FORCE_DEPS=1 & start_fraudshield.bat

setlocal ENABLEDELAYEDEXPANSION

set SCRIPT_DIR=%~dp0
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

set VENV_DIR=%SCRIPT_DIR%.venv
set REQS_FILE=%SCRIPT_DIR%requirements.txt

if "%ENABLE_LOG%"=="1" (
    set LOG_FILE=%SCRIPT_DIR%logs\streamlit_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%_%TIME:~0,2%-%TIME:~3,2%-%TIME:~6,2%.log
    if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"
)

where python >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo [ERROR] Python not found in PATH.
    goto :end
)

if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    set FORCE_DEPS=1
)

call "%VENV_DIR%\Scripts\activate.bat"
if not %ERRORLEVEL%==0 (
    echo [ERROR] Failed to activate virtual environment.
    goto :end
)

python -m pip install --upgrade pip >nul 2>&1

if "%FORCE_DEPS%"=="1" (
    if exist "%REQS_FILE%" (
        echo [INFO] Installing dependencies from requirements.txt ...
        pip install -r "%REQS_FILE%"
    ) else (
        echo [WARN] requirements.txt not found; skipping dependency install.
    )
)

echo [INFO] Starting Streamlit app...
if "%ENABLE_LOG%"=="1" (
    echo [INFO] Logging to %LOG_FILE%
    streamlit run "%SCRIPT_DIR%app.py" %* > "%LOG_FILE%" 2>&1
) else (
    streamlit run "%SCRIPT_DIR%app.py" %*
)

:end
endlocal
