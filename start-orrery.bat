@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "NO_PROXY=localhost,127.0.0.1"

if /I "%~1"=="--console" goto console
start "" wscript.exe "%~dp0Start Orrery.vbs"
exit /b 0

:console
set "PY=python"
if exist "%USERPROFILE%\anaconda3\python.exe" set "PY=%USERPROFILE%\anaconda3\python.exe"
"%PY%" --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 was not found.
  exit /b 1
)
"%PY%" -X utf8 "scripts\docsite\serve_orrery.py" --console
exit /b %ERRORLEVEL%
