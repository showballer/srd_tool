#!/bin/bash
# 快速启动脚本

cd "$(dirname "$0")"

echo "=========================================="
echo "CodeFree Desktop Application"
echo "=========================================="
echo ""

# 检查依赖
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "缺少依赖，正在安装..."
    pip3 install -r requirements.txt
    playwright install chromium
fi

# 启动应用（使用简化版避免 emoji 显示问题）
echo "启动应用..."
echo "提示: 如果窗口显示空白，请使用简化版: python3 gui_app_simple.py"
echo ""
python3 gui_app_simple.py
