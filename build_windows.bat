@echo off
REM Windows Build Script for CodeFree Desktop

echo ==========================================
echo CodeFree Desktop - Windows Build Script
echo ==========================================

REM Check Python version
echo.
echo Checking Python environment...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
pip install -r requirements.txt
pip install playwright
pip install pyinstaller

REM Clean old build files (Windows only)
echo.
echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist\CodeFree*.exe del /q "dist\CodeFree*.exe"
if exist "CodeFree Desktop.spec" del /q "CodeFree Desktop.spec"

REM Package with PyInstaller (include Playwright browsers)
echo.
echo Starting packaging...
python -m PyInstaller --name="CodeFree Desktop" ^
    --windowed ^
    --onefile ^
    --icon="srd_tool.ico" ^
    --add-data="websocket_simulator2_0.py;." ^
    --add-data="srd_tool.jpg;." ^
    --add-data="src;src" ^
    --hidden-import=websockets ^
    --hidden-import=playwright ^
    --hidden-import=playwright.sync_api ^
    --hidden-import=playwright.async_api ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --hidden-import=tkinter ^
    --hidden-import=asyncio ^
    --collect-all playwright ^
    codefree_desktop.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo Build FAILED!
    echo ==========================================
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo.
echo Application location: dist\CodeFree Desktop.exe
echo Size: Approximately 120-150 MB (uses system Chrome)
echo.
echo Usage:
echo 1. Double-click 'dist\CodeFree Desktop.exe' to run
echo.
echo Note:
echo - Windows Defender may show a warning on first run
echo - Click "More info" then "Run anyway" to continue
echo - First launch may take 10-20 seconds to initialize
echo - Ensure Google Chrome is installed on the target machine
echo.
pause
