@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3.10 or newer and enable "Add Python to PATH".
    pause
    exit /b 1
)

python -m pip install -r requirements.txt --quiet
python scripts\career_tracker_gui.py

if errorlevel 1 (
    echo.
    echo The tracker closed because of an error.
    pause
)
