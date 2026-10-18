@echo off
:: ============================================================
:: PinkbikeDeals — Build Script
:: Creates a standalone Windows application
:: ============================================================

echo.
echo  ====================================
echo   PinkbikeDeals Build Script
echo  ====================================
echo.

:: Change to the directory containing this batch file
cd /d "%~dp0"

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found on PATH.
    echo  Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Install/upgrade PyInstaller
echo  [1/3] Installing build tools...
pip install pyinstaller --upgrade --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

:: Install project dependencies
echo  [2/3] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Build
echo  [3/3] Building PinkbikeDeals.exe...
echo.
pyinstaller PinkbikeDeals.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed! Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo  ====================================
echo   BUILD SUCCESSFUL
echo  ====================================
echo.
echo  Your application is ready at:
echo    dist\PinkbikeDeals\PinkbikeDeals.exe
echo.
echo  To run: double-click PinkbikeDeals.exe
echo  To distribute: copy the entire dist\PinkbikeDeals\ folder
echo.

:: Create a desktop shortcut
echo  Creating desktop shortcut...
python -c "
import os, winreg
try:
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    exe_path = os.path.join(os.getcwd(), 'dist', 'PinkbikeDeals', 'PinkbikeDeals.exe')
    shortcut_path = os.path.join(desktop, 'PinkbikeDeals.lnk')
    # Use PowerShell to create shortcut
    ps_cmd = f'''$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('{shortcut_path}'); $s.TargetPath = '{exe_path}'; $s.WorkingDirectory = '{os.path.dirname(exe_path)}'; $s.Description = 'PinkbikeDeals - Used Bike Deal Finder'; $s.Save()'''
    os.system(f'powershell -Command \"{ps_cmd}\"')
    print(f'  Shortcut created: {shortcut_path}')
except Exception as e:
    print(f'  Could not create shortcut: {e}')
" 2>nul

echo.
pause
