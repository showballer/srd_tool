# CodeFree Desktop Application

研发云编程助手 - 跨平台桌面客户端

## 功能特性

- ✅ **半自动登录** - 自动打开浏览器，手动登录后自动提取凭证
- ✅ **代码补全模拟** - WebSocket 通信，模拟代码补全请求
- ✅ **代码注释生成** - 批量生成代码文件的注释
- ✅ **Git 提交模拟** - 自动化 Git 提交操作
- ✅ **跨平台支持** - Mac 和 Windows 双平台
- ✅ **图形界面** - 基于 Tkinter 的友好界面
- ✅ **实时控制台** - 实时查看运行状态和日志

## 快速开始

### 方法一：运行源代码（推荐开发者）

#### 1. 安装依赖

```bash
cd /Users/yuanyun/workspace/2025/srd/desktop-app
pip3 install -r requirements.txt
playwright install chromium
```

#### 2. 运行应用

```bash
python3 gui_app.py
```

### 方法二：打包成独立应用（推荐普通用户）

#### macOS 打包

```bash
cd /Users/yuanyun/workspace/2025/srd/desktop-app
./build_mac.sh
```

打包完成后，应用位于 `dist/CodeFree Desktop.app`

如果遇到权限问题：
```bash
xattr -cr "dist/CodeFree Desktop.app"
```

#### Windows 打包

```cmd
cd C:\path\to\desktop-app
build_windows.bat
```

打包完成后，应用位于 `dist\CodeFree Desktop.exe`

## 使用说明

### 1. 辅助编程模式

#### 半自动登录（推荐）
1. 点击"辅助编程"标签页
2. 点击"半自动登录"按钮
3. 在弹出的浏览器中完成登录（包括短信验证码）
4. 登录成功后，凭证会自动提取并填入界面
5. 选择运行模式：
   - **代码补全**：模拟代码补全请求
   - **代码注释生成**：为源文件生成注释
6. 配置参数后点击"开始运行"

#### 手动输入凭证
1. 打开浏览器访问 https://www.srdcloud.cn/login
2. 登录后按 F12 打开开发者工具
3. 在 Network 标签中找到任意请求
4. 在 Request Headers 中找到 `userid` 和 `sessionid`
5. 将这些值输入到界面中
6. 点击"保存凭证"

### 2. Git 提交模式

1. 切换到"Git 提交"标签页
2. 点击"半自动登录"（会提示导航到仓库页面）
3. 登录后导航到目标仓库页面
4. 应用会自动提取项目ID和仓库ID
5. 配置文件路径和提交次数
6. 点击"开始 Git 提交"

### 3. 控制台输出

- 所有操作的日志都会实时显示在底部的控制台中
- 点击"清空控制台"可以清除历史日志
- 状态栏会显示当前运行状态

## 技术架构

```
desktop-app/
├── gui_app.py                   # GUI 主程序
├── websocket_simulator2_0.py    # 核心逻辑（从 ../python 复制）
├── requirements.txt             # Python 依赖
├── build_mac.sh                 # macOS 打包脚本
├── build_windows.bat            # Windows 打包脚本
└── README.md                    # 本文档
```

### 技术栈

- **GUI 框架**: Tkinter (Python 内置)
- **异步编程**: asyncio, threading
- **WebSocket**: websockets 库
- **HTTP 请求**: requests 库
- **浏览器自动化**: Playwright
- **打包工具**: PyInstaller

## 常见问题

### Q1: macOS 提示"无法打开，因为无法验证开发者"

**解决方法**：
```bash
xattr -cr "dist/CodeFree Desktop.app"
```

或者：系统偏好设置 -> 安全性与隐私 -> 仍要打开

### Q2: Windows Defender 提示病毒

**解决方法**：这是误报，选择"仍要运行"即可。PyInstaller 打包的应用经常被误报。

### Q3: 半自动登录失败

**可能原因**：
- Playwright Chromium 未安装：`playwright install chromium`
- 网络问题：检查是否可以访问 https://www.srdcloud.cn
- 登录超时：登录后刷新页面触发网络请求

**解决方法**：使用手动模式输入凭证

### Q4: 代码注释模式提示"没有可用的源文件"

**解决方法**：检查源文件目录是否存在，目录中是否有代码文件（.ts, .js, .py 等）

### Q5: 打包后体积很大

**说明**：由于包含了 Playwright Chromium 浏览器，应用体积约 150-200MB，这是正常的。

## 开发指南

### 修改源代码后重新打包

```bash
# macOS
./build_mac.sh

# Windows
build_windows.bat
```

### 调试模式运行

直接运行源代码，控制台会显示详细日志：

```bash
python3 gui_app.py
```

### 修改 GUI 界面

编辑 `gui_app.py` 文件中的 `create_*_tab()` 方法来修改界面布局。

## 注意事项

1. **凭证安全**：应用不会保存凭证到文件，仅在运行期间保存在内存中
2. **SSL 证书**：默认禁用 SSL 证书验证以避免证书问题
3. **并发限制**：建议不要同时运行过多任务，避免服务器限流
4. **日志输出**：所有日志都在控制台中，方便排查问题

## 更新日志

### v1.0 (2025-01-06)
- ✅ 初始版本发布
- ✅ 实现图形界面
- ✅ 支持半自动登录
- ✅ 支持代码补全和注释生成
- ✅ 支持 Git 提交模拟
- ✅ 跨平台打包脚本

## 许可证

版权所有 © 2025

## 联系方式

如有问题，请联系开发者或提交 Issue。
