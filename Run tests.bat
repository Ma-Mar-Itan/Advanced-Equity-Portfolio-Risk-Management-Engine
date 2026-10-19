@echo off
rem Runs the unit tests (about 10 seconds, no internet needed).
cd /d "%~dp0"
call "%~dp0tools\setup_env.bat" || goto :failed
".venv\Scripts\python.exe" -m pytest tests
pause
goto :eof

:failed
pause
