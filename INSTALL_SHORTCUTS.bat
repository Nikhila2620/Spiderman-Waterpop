@echo off
setlocal
title Install Spider-Man Waterpop Shortcuts
cd /d "%~dp0"

echo ============================================================
echo   Installing Spider-Man Waterpop Desktop & Start Menu
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcuts.ps1"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Shortcut installation encountered an issue.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Installation Complete! Look for Spider-Man on your Desktop!
echo ============================================================
timeout /t 3 >nul
exit /b 0
