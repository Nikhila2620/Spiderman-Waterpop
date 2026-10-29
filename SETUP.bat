@echo off
setlocal enabledelayedexpansion
title Spider-Man Waterpop - Environment Setup
cd /d "%~dp0"

echo ============================================================
echo   Spider-Man Waterpop v2.0 - Quick Setup & Installation
echo ============================================================
echo.

:: 1. Detect Python (>= 3.10)
set "SYS_PYTHON="

:: Check py -3 first
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if !errorlevel! equ 0 (
    set "SYS_PYTHON=py -3"
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if !errorlevel! equ 0 (
            set "SYS_PYTHON=python"
        )
    )
)

if "%SYS_PYTHON%"=="" (
    echo [ERROR] Python 3.10+ is not installed or not found on PATH!
    echo Please download and install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Detected system Python: %SYS_PYTHON%

:: 2. Create virtual environment if missing
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment in .venv...
    %SYS_PYTHON% -m venv "%~dp0.venv"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo [OK] Virtual environment already exists (.venv).
)

:: 3. Install dependencies
echo [INFO] Installing required packages (PySide6)...
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if !errorlevel! neq 0 (
    echo [ERROR] Package installation failed! Please check your internet connection.
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully.

:: 4. Create desktop and start menu shortcuts
echo [INFO] Creating Desktop and Start Menu shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcuts.ps1"
if !errorlevel! neq 0 (
    echo [WARN] Shortcut creation encountered a minor issue.
) else (
    echo [OK] Shortcuts created!
)

echo.
echo ============================================================
echo   Setup Complete!
echo   You can now launch the app anytime via START_APP.bat
echo   or by using the Spider-Man shortcut on your Desktop.
echo ============================================================
echo.
pause
exit /b 0
