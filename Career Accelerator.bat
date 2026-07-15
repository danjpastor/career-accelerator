@echo off
setlocal
cd /d "%~dp0"
title Career Accelerator v9.3.9

if not exist "Career Accelerator.lnk" (
    cscript //nologo "create-desktop-shortcut.vbs" /LocalOnly >nul 2>nul
)

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install Python and select "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local application environment...
    python -m venv .venv
)

echo Installing application dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo Starting Career Accelerator...
".venv\Scripts\python.exe" app.py

if errorlevel 1 (
    echo.
    echo The application closed because of an error.
    pause
)
endlocal
