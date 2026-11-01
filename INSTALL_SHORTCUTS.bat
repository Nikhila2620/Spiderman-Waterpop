@echo off
setlocal
title Install Spider-Man Waterpop Shortcuts
cd /d "%~dp0"

echo ============================================================
echo   Installing Spider-Man Waterpop Desktop & Start Menu
echo ============================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\install_and_register_app.py"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcuts.ps1"
)

echo.
echo ============================================================
echo   Installation Complete! Look for Spider-Man on your Desktop
echo   and in your Windows Start Menu under "Spider-Man Waterpop"!
echo ============================================================
ping 127.0.0.1 -n 3 >nul
exit /b 0
