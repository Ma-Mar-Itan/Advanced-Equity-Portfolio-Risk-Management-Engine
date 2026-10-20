@echo off
rem Downloads the latest prices, then rebuilds the analytics, Word report and editable PowerPoint deck.
rem Takes a few minutes and needs internet for a data refresh.
cd /d "%~dp0"
call "%~dp0tools\setup_env.bat" || goto :failed
set PY=.venv\Scripts\python.exe
set CODEX_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe

echo.
echo [1/4] Downloading the latest prices from Yahoo Finance...
"%PY%" -m tools.module1_demo || goto :failed
"%PY%" -m tools.save_snapshot || goto :failed

echo.
echo [2/4] Recomputing every number, table and figure for the report...
"%PY%" -m tools.build_report_assets || goto :failed

echo.
echo [3/4] Rebuilding the Word report...
"%PY%" -m tools.build_report || goto :failed

echo.
echo [4/4] Rebuilding the validated 15-slide PowerPoint...
for %%M in (2 3 4 5 6 7 8) do "%PY%" -m tools.module%%M_demo > nul
if not exist "%CODEX_NODE%" (
  echo The bundled Codex Node runtime is required to build the editable deck.
  goto :failed
)
"%CODEX_NODE%" tools\build_deck_artifact.mjs || goto :failed

echo.
echo Done. QFI_V2_report.docx and QFI_V2_slides.pptx are up to date.
echo Note: the deck is rebuilt from report_assets\results.json with editable charts and tables.
pause
goto :eof

:failed
echo.
echo Something went wrong. See the message above.
pause
