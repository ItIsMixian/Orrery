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

echo Starting the local project documentation site...
echo Keep this window open while using the site. Press Ctrl+C to stop it.
"%PY%" -X utf8 "scripts\docsite\serve.py"
set "DOCSITE_EXIT=%ERRORLEVEL%"

if not "%DOCSITE_EXIT%"=="0" (
  echo.
  echo [ERROR] The documentation site exited with code %DOCSITE_EXIT%.
  pause
)

exit /b %DOCSITE_EXIT%
