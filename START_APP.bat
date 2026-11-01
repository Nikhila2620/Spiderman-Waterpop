@echo off
setlocal EnableDelayedExpansion
title Spider-Man Waterpop v2.0
cd /d "%~dp0"

echo ============================================================
echo   SPIDER-MAN WATERPOP v2.0
echo ============================================================
echo.

:: Find a system Python that can repair/create .venv.
:: Do NOT use a copied .venv here — it often belongs to another PC.
set "BOOTSTRAP="

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if !errorlevel! equ 0 (
    set "BOOTSTRAP=py -3"
)

if "!BOOTSTRAP!"=="" (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if !errorlevel! equ 0 set "BOOTSTRAP=python"
    )
)

if "!BOOTSTRAP!"=="" (
    echo [ERROR] Python 3.10+ was not found on this computer.
    echo Install it from https://www.python.org/ and tick "Add Python to PATH".
    echo Then double-click START_APP.bat again — no terminal commands needed.
    echo.
    pause
    exit /b 1
)

echo [1/2] Preparing Python environment...
!BOOTSTRAP! "%~dp0scripts\ensure_runtime.py"
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Could not prepare the app. See the message above.
    pause
    exit /b 1
)

if not exist "%~dp0.runtime_python" (
    echo [ERROR] Runtime marker was not created.
    pause
    exit /b 1
)

set /p PY_LAUNCH=<"%~dp0.runtime_python"
if not exist "!PY_LAUNCH!" (
    echo [ERROR] Launch interpreter is missing: !PY_LAUNCH!
    pause
    exit /b 1
)

echo [2/2] Opening Spider-Man Waterpop...
start "" "!PY_LAUNCH!" "%~dp0run.py"
echo [READY] If the dashboard does not appear, check the system tray near the clock.
ping 127.0.0.1 -n 3 >nul
exit /b 0
