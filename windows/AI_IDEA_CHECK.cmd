@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found on PATH. Install Python 3.11 or newer from an official source.
  exit /b 2
)
python -m tools.windows_preflight --rbz AI_IDEA_V192_ALPHA.rbz
exit /b %errorlevel%
