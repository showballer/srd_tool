#!/bin/bash
# macOS 打包脚本

echo "=========================================="
echo "CodeFree Desktop - macOS 打包脚本"
echo "=========================================="

# 检查 Python 版本
echo ""
echo "检查 Python 环境..."
python3 --version

# 安装依赖
echo ""
echo "安装依赖..."
pip3 install -r requirements.txt

# 安装 Playwright 浏览器
echo ""
echo "安装 Playwright Chromium..."
playwright install chromium

# 清理旧的构建
echo ""
echo "清理旧的构建文件..."
rm -rf build dist *.spec

# 使用 PyInstaller 打包
echo ""
echo "开始打包..."
pyinstaller --name="CodeFree Desktop" \
    --windowed \
    --onefile \
    --icon=icon.icns \
    --add-data="websocket_simulator2_0.py:." \
    --hidden-import=websockets \
    --hidden-import=playwright \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --hidden-import=tkinter \
    --hidden-import=asyncio \
    --collect-all playwright \
    gui_app.py

echo ""
echo "=========================================="
echo "打包完成！"
echo "=========================================="
echo ""
echo "应用程序位置: dist/CodeFree Desktop.app"
echo ""
echo "使用方法:"
echo "1. 双击 'dist/CodeFree Desktop.app' 运行"
echo "2. 或者使用命令: open 'dist/CodeFree Desktop.app'"
echo ""
echo "注意："
echo "- 首次运行可能需要在系统偏好设置中允许运行"
echo "- 如果遇到权限问题，请使用: xattr -cr 'dist/CodeFree Desktop.app'"
echo ""
