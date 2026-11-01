@echo off
setlocal EnableDelayedExpansion
title Spider-Man Waterpop Setup
cd /d "%~dp0"

echo ============================================================
echo   Installing Spider-Man Waterpop v2.0
echo ============================================================
echo.

:: Source copies have no compiled Setup.exe payload. Prepare a local
:: venv, install shortcuts, then start the app — no terminal required.
call "%~dp0START_APP.bat"
if !errorlevel! neq 0 exit /b 1

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\register_windows_app.py"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcuts.ps1"
)

echo.
echo Shortcuts are on your Desktop and Start Menu.
echo You can open the app later by double-clicking those — no command needed.
echo.
pause
exit /b 0
