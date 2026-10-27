@echo off
setlocal
title Pathwise
cd /d "%~dp0ai-ml"

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py -3"

%PY% --version >nul 2>nul
if errorlevel 1 goto nopython

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY% -m venv .venv
)
if not exist ".venv\Scripts\python.exe" goto novenv

echo Installing requirements - the first time takes a few minutes...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 goto pipfail

start "" cmd /c "timeout /t 6 >nul & start http://localhost:8000"
echo.
echo Pathwise is running at http://localhost:8000
echo Close this window to stop it.
echo.
".venv\Scripts\python.exe" -m uvicorn api.app:app --port 8000
pause
exit /b 0

:nopython
echo Python was not found. Install it from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" during setup. Then run this file again.
pause
exit /b 1

:novenv
echo Could not create the virtual environment.
echo Tip: move the Pathwise folder to a simple path like C:\Pathwise and try again.
pause
exit /b 1

:pipfail
echo Package install failed. Check your internet connection and try again.
pause
exit /b 1
