#!/bin/bash
# macOS 打包脚本

echo "=========================================="
echo "CodeFree Desktop - macOS 打包脚本"
echo "=========================================="

# 检查 Python 版本
echo ""
echo "检查 Python 环境..."
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python)"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ 未找到可用的 Python 解释器，请先安装 Python 3.9+"
    exit 1
fi

echo "使用 Python: $PYTHON_BIN"
"$PYTHON_BIN" --version

# 安装依赖
echo ""
echo "安装依赖..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt
"$PYTHON_BIN" -m pip install pyinstaller

# 安装 Playwright 浏览器
echo ""
echo "安装 Playwright Chromium（离线目录 playwright-browsers）..."
export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/playwright-browsers"
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"
"$PYTHON_BIN" -m playwright install chromium

# 清理旧的构建
echo ""
echo "清理旧的构建文件..."
rm -rf build dist "CodeFree Desktop.spec"

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

"$PYTHON_BIN" -m PyInstaller --clean --noconfirm "CodeFree Desktop Custom.spec"

# PyInstaller 会过滤部分浏览器可执行文件，这里强制同步原始目录
APP_BROWSER_DIR="dist/CodeFree Desktop.app/Contents/Frameworks/playwright-browsers"
if [ -d "$APP_BROWSER_DIR" ]; then
    echo ""
    echo "同步 Playwright 浏览器资源..."
    mkdir -p "$APP_BROWSER_DIR"
    rsync -a --delete "playwright-browsers/" "$APP_BROWSER_DIR/"
fi

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
