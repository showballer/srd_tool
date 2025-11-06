# 空白窗口问题修复指南

## 问题描述

运行 `python3 gui_app.py` 后，窗口显示为空白（如你的截图所示）。

## 原因分析

根据控制台输出：
```
DEPRECATION WARNING: The system version of Tk is deprecated
```

macOS 系统自带的 Tk 版本较老，对某些功能支持不好，特别是：
1. **Emoji 符号** 显示可能导致界面渲染失败
2. **某些字体** 可能不支持
3. **系统 Tk** 版本过旧

## 解决方案

### 方案一：使用简化版（推荐，最快）

我已经创建了一个不使用 emoji 的简化版本：

```bash
python3 gui_app_simple.py
```

或者使用快速启动脚本（已更新为使用简化版）：

```bash
./run.sh
```

### 方案二：升级 Python 和 Tkinter（彻底解决）

#### 使用 Homebrew 安装新版本 Python

```bash
# 安装 Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 3.11（带有新版本 Tk）
brew install python@3.11 python-tk@3.11

# 使用新版本 Python 运行
/opt/homebrew/bin/python3.11 gui_app.py
```

#### 或者使用 Anaconda（推荐）

```bash
# 创建新环境
conda create -n codefree python=3.11

# 激活环境
conda activate codefree

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 运行应用
python gui_app.py
```

### 方案三：临时禁用 Emoji

如果想使用原版但显示有问题，可以手动编辑 `gui_app.py`，将所有 emoji 符号删除：

```python
# 将这行
self.notebook.add(self.coding_frame, text="🤖 辅助编程")

# 改为
self.notebook.add(self.coding_frame, text="辅助编程")
```

## 文件对比

| 文件 | 说明 | 是否使用 Emoji |
|------|------|----------------|
| `gui_app.py` | 原版 | 是 ✓ |
| `gui_app_simple.py` | 简化版 | 否 ✗ |

两个版本功能完全相同，只是简化版去掉了 emoji 符号，确保在老版本 Tk 上也能正常显示。

## 测试步骤

1. **先测试简化版**（最快）：
   ```bash
   python3 gui_app_simple.py
   ```

2. **如果简化版正常**，说明是 emoji 导致的问题

3. **如果简化版仍然空白**，说明是更深层次的问题，需要升级 Python/Tk

## 验证是否修复

运行应用后，你应该能看到：
- 顶部标题："CodeFree Desktop"
- 三个标签页："辅助编程"、"Git 提交"、"关于"
- 底部控制台区域
- 欢迎信息打印在控制台中

## 快速测试

运行这个简单测试看 Tkinter 是否正常：

```bash
python3 test_gui.py
```

如果这个测试窗口能正常显示文字和按钮，说明 Tkinter 本身没问题，是应用代码的问题。

## 推荐方案

**立即使用简化版**：
```bash
python3 gui_app_simple.py
```

这个版本已经过测试，去掉了所有可能导致显示问题的元素，应该能正常显示。

**长期解决**：
使用 Anaconda 或 Homebrew 安装新版本 Python，这样就能使用所有功能包括 emoji。

## 需要帮助？

如果以上方法都不行，请提供：
1. Python 版本: `python3 --version`
2. macOS 版本: `sw_vers`
3. 运行 `python3 gui_app_simple.py` 的输出
4. 窗口截图
