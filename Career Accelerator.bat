@echo off
setlocal
cd /d "%~dp0"
start "" /b wscript.exe "%~dp0Launch-Career-Accelerator-Hidden.vbs"
exit /b 0
