@echo off
setlocal
cd /d "%~dp0"
python scripts\publish.py %*
exit /b %ERRORLEVEL%
