@echo off
setlocal
cd /d "%~dp0"

:: 1. Clear any stuck background instances
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' } | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1

:: 2. Resolve Python runtime (prefer local virtual environment)
set "PY_BIN="
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    set "PY_BIN=%~dp0.venv\Scripts\pythonw.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_BIN=%~dp0.venv\Scripts\python.exe"
)

if "%PY_BIN%"=="" (
    where pyw >nul 2>&1
    if not errorlevel 1 set "PY_BIN=pyw -3"
)

if "%PY_BIN%"=="" (
    where pythonw >nul 2>&1
    if not errorlevel 1 set "PY_BIN=pythonw"
)

if "%PY_BIN%"=="" (
    where py >nul 2>&1
    if not errorlevel 1 set "PY_BIN=py -3"
)

if "%PY_BIN%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 set "PY_BIN=python"
)

if "%PY_BIN%"=="" (
    if exist "%~dp0SETUP.bat" call "%~dp0SETUP.bat"
    set "PY_BIN=%~dp0.venv\Scripts\pythonw.exe"
)

:: 3. Launch the application silently in the background
start "" %PY_BIN% "%~dp0run.py"
exit /b 0
