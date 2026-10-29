@echo off
setlocal
title Spider-Man Waterpop Setup
cd /d "%~dp0"

echo ============================================================
echo   Installing Spider-Man Waterpop v2.0
echo ============================================================
echo.

set "SETUP_EXE=%~dp0dist\SpiderManWaterBuddy-v2.0.0-Setup.exe"

if exist "%SETUP_EXE%" (
    echo [INFO] Launching standalone installer...
    start "" "%SETUP_EXE%"
    exit /b 0
)

:: If standalone installer is not built, install desktop and start menu shortcuts
echo [INFO] Installing Desktop and Start Menu shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcuts.ps1"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Shortcut installation failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Installation Complete!
echo   Double-click START_APP.bat or use the desktop shortcut.
echo ============================================================
timeout /t 3 >nul
exit /b 0
