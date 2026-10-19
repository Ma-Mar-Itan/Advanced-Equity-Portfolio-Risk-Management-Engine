@echo off
rem Downloads the latest prices, then rebuilds every chart, the Word report and the PowerPoint deck.
rem Takes a few minutes. Needs internet, and Google Chrome for saving the charts as images.
cd /d "%~dp0"
call "%~dp0tools\setup_env.bat" || goto :failed
set PY=.venv\Scripts\python.exe

echo.
echo [1/4] Downloading the latest prices from Yahoo Finance...
"%PY%" -m tools.module1_demo || goto :failed

echo.
echo [2/4] Recomputing every number, table and figure for the report...
"%PY%" -m tools.build_report_assets || goto :failed

echo.
echo [3/4] Rebuilding the Word report...
"%PY%" -m tools.build_report || goto :failed

echo.
echo [4/4] Redrawing the slide charts and rebuilding the PowerPoint...
for %%M in (2 3 4 5 6 7 8) do "%PY%" -m tools.module%%M_demo > nul
"%PY%" -m tools.build_deck || goto :failed

echo.
echo Done. QFI_V2_report.docx and QFI_V2_slides.pptx are up to date.
echo Note: the charts and the report's numbers update automatically; the slide text in slide_notes.md
echo is hand-written, so reread it if the numbers moved.
pause
goto :eof

:failed
echo.
echo Something went wrong. See the message above.
pause
