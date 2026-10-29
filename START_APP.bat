@echo off
setlocal enabledelayedexpansion
title Spider-Man Waterpop v2.0
cd /d "%~dp0"

:: 1. Detect Python interpreter (prefer local .venv)
set "PYTHON_EXE="
set "PYTHONW_EXE="

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
    if exist "%~dp0.venv\Scripts\pythonw.exe" (
        set "PYTHONW_EXE=%~dp0.venv\Scripts\pythonw.exe"
    )
) else (
    :: Try Windows py launcher first (avoids WindowsApps stub)
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=py -3"
        set "PYTHONW_EXE=pyw -3"
    ) else (
        where python >nul 2>&1
        if !errorlevel! equ 0 (
            python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
            if !errorlevel! equ 0 (
                set "PYTHON_EXE=python"
                where pythonw >nul 2>&1
                if !errorlevel! equ 0 set "PYTHONW_EXE=pythonw"
            )
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo ============================================================
    echo [ERROR] No compatible Python (3.10+) installation found!
    echo ============================================================
    echo Please run SETUP.bat in this folder to automatically set up
    echo the virtual environment and install dependencies.
    echo.
    pause
    exit /b 1
)

:: 2. Verify PySide6 is installed
%PYTHON_EXE% -c "import PySide6" >nul 2>&1
if !errorlevel! neq 0 (
    echo ============================================================
    echo [ERROR] Required dependencies (PySide6) are missing!
    echo ============================================================
    echo Would you like to run SETUP.bat now to install them?
    set /p "RUN_SETUP=Run SETUP.bat now? (Y/N): "
    if /i "!RUN_SETUP!"=="Y" (
        call "%~dp0SETUP.bat"
        exit /b 0
    ) else (
        echo Please run SETUP.bat before starting the application.
        pause
        exit /b 1
    )
)

:: 3. Launch application in background
set "LAUNCHER=%PYTHON_EXE%"
if not "%PYTHONW_EXE%"=="" set "LAUNCHER=%PYTHONW_EXE%"

start "" %LAUNCHER% "%~dp0run.py" %*
exit /b 0
