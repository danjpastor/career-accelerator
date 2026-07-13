@echo off
cd /d "%~dp0"
title Career Accelerator

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3.10 or newer and select "Add Python to PATH".
    pause
    exit /b 1
)

python -m pip install -r requirements.txt --quiet
python scripts\career_accelerator_app.py

if errorlevel 1 (
    echo.
    echo The application closed because of an error.
    pause
)
