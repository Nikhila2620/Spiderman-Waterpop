@echo off
setlocal
title Spider-Man Water Buddy Launcher

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "EXE_PATH=%~dp0dist\SpiderManWaterBuddy\SpiderManWaterBuddy.exe"

if exist "%PYTHON_EXE%" (
    start "" "%PYTHON_EXE%" "%~dp0run.py" --dashboard
    exit /b 0
)

if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%" --dashboard
    exit /b 0
)

echo [ERROR] Neither the Python virtual environment nor the packaged executable was found!
pause
exit /b 1
