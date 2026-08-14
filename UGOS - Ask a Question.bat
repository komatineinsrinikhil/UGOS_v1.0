@echo off
title UGOS - Ask a Question
cd /d "%~dp0"

echo.
echo  ============================================================
echo   UGOS
echo  ============================================================
echo.

REM --- Find Python -------------------------------------------------
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

REM --- Warn if Ollama is not running -------------------------------
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
  echo   [!] Ollama does not appear to be running.
  echo       Open Ollama from the Start menu, then try again.
  echo       UGOS will still start, but cannot answer anything.
  echo.
)

%PY% "run_my_task.py" %*

echo.
echo  ------------------------------------------------------------
echo   Done. Press any key to close.
pause >nul
