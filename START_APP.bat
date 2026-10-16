@echo off
setlocal
title Spider-Man Water Buddy Launcher

set "EXE_PATH=%~dp0dist\SpiderManWaterBuddy\SpiderManWaterBuddy.exe"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%"
    exit /b 0
)

if exist "%PYTHON_EXE%" (
    echo [INFO] Standalone executable not found in dist. Launching via Python virtual environment...
    start "" "%PYTHON_EXE%" "%~dp0run.py"
    exit /b 0
)

echo [ERROR] Neither the packaged executable nor the Python virtual environment was found!
echo Target: "%EXE_PATH%"
pause
exit /b 1
