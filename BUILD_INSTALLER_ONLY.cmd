@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD where python >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (echo [ERROR] Python 3 was not found.& pause & exit /b 1)
%PY_CMD% -X utf8 build_release.py --installer-only
set "RC=%ERRORLEVEL%"
echo.
pause
exit /b %RC%
