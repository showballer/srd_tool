@echo off
REM Windows 打包脚本

echo ==========================================
echo CodeFree Desktop - Windows 打包脚本
echo ==========================================

REM 检查 Python 版本
echo.
echo 检查 Python 环境...
python --version

REM 安装依赖
echo.
echo 安装依赖...
pip install -r requirements.txt

REM 安装 Playwright 浏览器
echo.
echo 安装 Playwright Chromium...
playwright install chromium

REM 清理旧的构建
echo.
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "*.spec" del /q *.spec

REM 使用 PyInstaller 打包
echo.
echo 开始打包...
pyinstaller --name="CodeFree Desktop" ^
    --windowed ^
    --onefile ^
    --icon=icon.ico ^
    --add-data="websocket_simulator2_0.py;." ^
    --hidden-import=websockets ^
    --hidden-import=playwright ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --hidden-import=tkinter ^
    --hidden-import=asyncio ^
    --collect-all playwright ^
    gui_app.py

echo.
echo ==========================================
echo 打包完成！
echo ==========================================
echo.
echo 应用程序位置: dist\CodeFree Desktop.exe
echo.
echo 使用方法:
echo 1. 双击 'dist\CodeFree Desktop.exe' 运行
echo.
echo 注意：
echo - 首次运行可能会被 Windows Defender 提示
echo - 请选择"仍要运行"以继续
echo.
pause
