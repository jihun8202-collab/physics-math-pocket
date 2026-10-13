@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
title Physics + Math Pocket Setup Builder
set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD where python >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
  echo [ERROR] Python 3 was not found.
  pause
  exit /b 1
)
%PY_CMD% -X utf8 build_release.py
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [DONE] release\PhysicsMathPocket_Setup_3.0.0.exe
) else (
  echo [FAILED] Read build_release.log for details.
)
pause
exit /b %RC%
