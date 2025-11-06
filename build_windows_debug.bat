@echo off
REM Windows Build Script for CodeFree Desktop (DEBUG VERSION)
REM This version shows console output for debugging

echo ==========================================
echo CodeFree Desktop - DEBUG Build
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
pip install -r requirements.txt
pip install playwright
pip install pyinstaller

REM Install Playwright browser (use unified directory name)
echo.
echo Installing Playwright Chromium...
set "PLAYWRIGHT_BROWSERS_PATH=%cd%\playwright-browsers"
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" mkdir "%PLAYWRIGHT_BROWSERS_PATH%"
python -m playwright install chromium

REM Clean old build files
echo.
echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist\CodeFree*.exe del /q "dist\CodeFree*.exe"
if exist "CodeFree Desktop.spec" del /q "CodeFree Desktop.spec"

REM Package with PyInstaller (DEBUG: with console window)
echo.
echo Starting packaging (DEBUG MODE - with console)...
python -m PyInstaller --name="CodeFree Desktop Debug" ^
    --onefile ^
    --add-data="websocket_simulator2_0.py;." ^
    --add-data="srd_tool.jpg;." ^
    --add-data="playwright-browsers;playwright-browsers" ^
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
echo DEBUG Build Complete!
echo ==========================================
echo.
echo Application location: dist\CodeFree Desktop Debug.exe
echo.
echo This is a DEBUG version with console output.
echo You will see error messages if something goes wrong.
echo.
echo Usage:
echo 1. Run from command line: cd dist ^&^& "CodeFree Desktop Debug.exe"
echo 2. Or double-click - a console window will appear
echo.
pause
