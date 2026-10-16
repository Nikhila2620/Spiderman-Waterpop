@echo off
setlocal
title Spider-Man Water Buddy Setup

set "SETUP_EXE=%~dp0dist\SpiderManWaterBuddy-v1.0.0-Setup.exe"

if exist "%SETUP_EXE%" (
    start "" "%SETUP_EXE%"
    exit /b 0
)

echo [ERROR] Setup package was not found!
echo Expected location: "%SETUP_EXE%"
echo Please build the installer package before running this script.
pause
exit /b 1
