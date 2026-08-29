@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "NO_PROXY=localhost,127.0.0.1"
set "PY=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PY=%USERPROFILE%\anaconda3\python.exe"

"%PY%" --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 was not found. Install Python and run this file again.
  pause
  exit /b 1
)

echo Starting Orrery local Maintenance control...
echo Loopback only. Personal Mode stays zero-network. Press Ctrl+C to stop it.
"%PY%" -X utf8 "scripts\docsite\serve_orrery_control.py" --open
set "ORRERY_CONTROL_EXIT=%ERRORLEVEL%"

if not "%ORRERY_CONTROL_EXIT%"=="0" (
  echo.
  echo [ERROR] Orrery local control exited with code %ORRERY_CONTROL_EXIT%.
  pause
)

exit /b %ORRERY_CONTROL_EXIT%
