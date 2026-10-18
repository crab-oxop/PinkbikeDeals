@echo off
:: PinkbikeDeals — Windows launcher
:: Double-click this file to launch the desktop GUI
:: Or drag it to a terminal to use CLI commands

:: Change to the directory containing this batch file
cd /d "%~dp0"

:: Launch the GUI
python run.py %*

:: If python isn't found, try py launcher
if errorlevel 1 (
    py run.py %*
)
pause
