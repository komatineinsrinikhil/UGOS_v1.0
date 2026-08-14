@echo off
title UGOS - Web Page
cd /d "%~dp0"

echo.
echo  ============================================================
echo   UGOS - starting the web page
echo  ============================================================
echo.

set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (where python >nul 2>&1 && set "PY=python")

if not defined PY (
  echo   Python is not installed on this computer.
  echo.
  echo   UGOS needs it to run. Get it from:  https://www.python.org/downloads/
  echo   During install, tick "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
  echo   [!] Ollama does not appear to be running.
  echo       Open Ollama from the Start menu for real answers.
  echo.
)

echo   Your browser will open in a moment.
echo   KEEP THIS WINDOW OPEN while you use UGOS.
echo   Closing it stops UGOS.
echo.

%PY% "ugos_web.py"

echo.
pause
