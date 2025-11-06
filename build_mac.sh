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
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
"$PYTHON_BIN" -m pip install -r requirements.txt
"$PYTHON_BIN" -m pip install pyinstaller

# 清理旧的构建
echo ""
echo "清理旧的构建文件..."
rm -rf build dist "CodeFree Desktop.spec"

# 使用 PyInstaller 打包
echo ""
echo "开始打包..."

"$PYTHON_BIN" -m PyInstaller --clean --noconfirm "CodeFree Desktop Custom.spec"

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
echo "- 运行前请确保目标机器已安装最新版 Google Chrome"
echo ""
