@echo off
REM Emergency script to kill all CodeFree Desktop processes

echo ==========================================
echo Emergency Stop - CodeFree Desktop
echo ==========================================
echo.
echo Killing all CodeFree Desktop processes...
echo.

REM Kill by process name
taskkill /F /IM "CodeFree Desktop.exe" 2>nul
if errorlevel 1 (
    echo No running CodeFree Desktop processes found.
) else (
    echo Killed CodeFree Desktop.exe
)

REM Also kill any chromium processes that might be hanging
taskkill /F /IM chrome.exe 2>nul
taskkill /F /IM chromium.exe 2>nul
taskkill /F /IM msedge.exe 2>nul

echo.
echo ==========================================
echo All processes terminated
echo ==========================================
echo.
pause
