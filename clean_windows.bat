@echo off
REM Clean script for Windows build environment

echo ==========================================
echo Cleaning macOS build artifacts...
echo ==========================================

REM Remove macOS build directories
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Remove spec files
if exist "CodeFree Desktop.spec" del /q "CodeFree Desktop.spec"
if exist "*.spec" del /q "*.spec"

REM Remove macOS playwright browsers (will reinstall Windows version)
if exist playwright-browsers rmdir /s /q playwright-browsers

echo.
echo Cleanup complete!
echo.
echo You can now run build_windows.bat
echo.
pause
