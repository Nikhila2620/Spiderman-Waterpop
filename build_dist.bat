@echo off
setlocal
title Build Spider-Man Waterpop Portable Executable
cd /d "%~dp0"

echo ============================================================
echo   Building Spider-Man Waterpop Portable Distribution
echo ============================================================
echo.

set "PY_EXE="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

:: Ensure PyInstaller is installed
%PY_EXE% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    %PY_EXE% -m pip install pyinstaller
)

echo [INFO] Compiling standalone portable application...
%PY_EXE% -m PyInstaller ^
    --noconsole ^
    --onedir ^
    --name "SpiderManWaterpop" ^
    --icon "%~dp0assets\images\app_icon.ico" ^
    --add-data "%~dp0assets;assets" ^
    --add-data "%~dp0src\web;src/web" ^
    --hidden-import "PySide6.QtWebEngineWidgets" ^
    --hidden-import "PySide6.QtWebEngineCore" ^
    --hidden-import "PySide6.QtWebChannel" ^
    --hidden-import "PySide6.QtSvg" ^
    --hidden-import "PySide6.QtSvgWidgets" ^
    --clean ^
    -y ^
    "%~dp0run.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Check compiler logs above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [SUCCESS] Build complete!
echo Output directory: %~dp0dist\SpiderManWaterpop\
echo Executable:       %~dp0dist\SpiderManWaterpop\SpiderManWaterpop.exe
echo ============================================================
echo.
pause
exit /b 0
