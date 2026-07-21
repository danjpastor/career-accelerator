@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Data Career Accelerator v10.19.1

if not exist "Data Career Accelerator.lnk" (
    cscript //nologo "create-desktop-shortcut.vbs" /LocalOnly >nul 2>nul
)

set "BOOTSTRAP_PYTHON=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python was not found.
        echo Install Python and select "Add Python to PATH".
        pause
        exit /b 1
    )
    set "BOOTSTRAP_PYTHON=py -3"
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local application environment...
    %BOOTSTRAP_PYTHON% -m venv .venv
    if errorlevel 1 (
        echo Could not create the local application environment.
        pause
        exit /b 1
    )
)

echo Installing application and notebook dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo Registering the dedicated Career Accelerator notebook kernel...
".venv\Scripts\python.exe" -m ipykernel install --user --name career-accelerator --display-name "Python (Career Accelerator)"
if errorlevel 1 (
    echo Dedicated notebook kernel registration failed.
    echo The application environment was created, but notebooks will not run correctly.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import duckdb, yaml, sql, ipykernel"
if errorlevel 1 (
    echo Notebook dependency verification failed.
    pause
    exit /b 1
)

if /I "%~1"=="--setup-only" (
    echo Career Accelerator environment and notebook kernel are ready.
    exit /b 0
)

echo Starting Data Career Accelerator...
".venv\Scripts\python.exe" application\app.py
if errorlevel 1 (
    echo.
    echo The application closed because of an error.
    pause
)

endlocal
