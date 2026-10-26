@echo off
rem Shared by the other .bat files: makes sure the private Python environment (.venv) exists.
rem Run from the V2 folder. Returns an error code if Python is missing or the install fails.
if exist ".venv\Scripts\python.exe" exit /b 0

where python > nul 2> nul
if errorlevel 1 goto :nopython

echo First run: creating a private Python environment. This takes a few minutes, once.
python -m venv .venv
if errorlevel 1 goto :nopython
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :installfail
exit /b 0

:nopython
echo Python was not found. Install Python 3.10 or newer from python.org
echo and tick "Add python.exe to PATH" during the installation, then try again.
exit /b 1

:installfail
echo Installing the packages failed. Check your internet connection and try again.
if exist ".venv" rmdir /s /q ".venv"
exit /b 1
