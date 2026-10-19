@echo off
rem Opens the QFI risk dashboard in your browser.
rem First time only: creates a private Python environment and installs the packages (a few minutes).
cd /d "%~dp0"
call "%~dp0tools\setup_env.bat" || goto :failed
echo.
echo Starting the dashboard. It opens in your browser; keep this window open while you use it.
echo Close this window to stop the dashboard.
echo.
start "" /min cmd /c "timeout /t 6 /nobreak > nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app\app.py --server.port 8501
goto :eof

:failed
echo.
echo The dashboard could not start. See the message above.
pause
