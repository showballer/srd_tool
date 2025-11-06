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
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

# 安装 Playwright 浏览器
echo ""
echo "安装 Playwright Chromium（离线目录 playwright-browsers）..."
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/playwright-browsers"
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"
python3 -m playwright install chromium

# 清理旧的构建
echo ""
echo "清理旧的构建文件..."
rm -rf build dist *.spec

# 使用 PyInstaller 打包
echo ""
echo "开始打包..."

# 检查 playwright-browsers 是否存在
if [ ! -d "playwright-browsers" ]; then
    echo "❌ 错误: playwright-browsers 目录不存在"
    echo "请先运行浏览器安装步骤"
    exit 1
fi

# 检查 chromium 是否存在
CHROMIUM_COUNT=$(find playwright-browsers -name "chromium-*" -type d | wc -l)
if [ $CHROMIUM_COUNT -eq 0 ]; then
    echo "❌ 错误: playwright-browsers 中没有 Chromium 浏览器"
    echo "请先运行: python3 -m playwright install chromium"
    exit 1
fi

echo "✅ 找到 Chromium 浏览器，继续打包..."

python3 -m PyInstaller --name="CodeFree Desktop" \
    --windowed \
    --onedir \
    --add-data="websocket_simulator2_0.py:." \
    --add-data="srd_tool.jpg:." \
    --add-data="playwright-browsers:playwright-browsers" \
    --hidden-import=websockets \
    --hidden-import=playwright \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --hidden-import=tkinter \
    --hidden-import=asyncio \
    --collect-all playwright \
    --noconfirm \
    --codesign-identity="-" \
    codefree_desktop.py

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
