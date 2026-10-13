@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD where python >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
  echo [ERROR] Python 3 was not found.
  echo Install Python from the official Python website, then try again.
  pause
  exit /b 1
)
%PY_CMD% -X utf8 main.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERROR] Physics + Math Pocket stopped with code %RC%.
  echo Log: %%LOCALAPPDATA%%\PhysicsMathPocket\physics_math_pocket.log
  pause
)
exit /b %RC%
