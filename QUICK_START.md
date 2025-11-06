# CodeFree Desktop - 快速入门指南

## 🚀 5分钟快速开始

### 步骤 1: 安装依赖（仅第一次需要）

打开终端，执行：

```bash
cd /Users/yuanyun/workspace/2025/srd/desktop-app
pip3 install -r requirements.txt
playwright install chromium
```

### 步骤 2: 运行应用

```bash
python3 gui_app.py
```

### 步骤 3: 使用半自动登录

1. 在应用中点击"辅助编程"标签页
2. 点击"🌐 半自动登录（推荐）"按钮
3. 浏览器会自动打开登录页面
4. 在浏览器中完成登录（输入账号密码、短信验证码等）
5. 登录成功后，应用会自动提取凭证
6. 浏览器会自动关闭

### 步骤 4: 配置并运行

1. 选择运行模式：
   - **代码补全**：适合快速测试
   - **代码注释生成**：需要指定源文件目录
2. 设置最大任务次数（建议初次使用设置较小值，如 10）
3. 点击"🚀 开始运行"
4. 在控制台中查看运行状态

## 📦 打包成独立应用（可选）

如果想分享给不懂编程的朋友使用，可以打包成独立应用：

### macOS 打包

```bash
./build_mac.sh
```

打包完成后，双击 `dist/CodeFree Desktop.app` 即可运行。

### Windows 打包

在 Windows 系统中：

```cmd
build_windows.bat
```

打包完成后，双击 `dist\CodeFree Desktop.exe` 即可运行。

## ⚠️ 常见问题

### 问题1: "playwright not found"

**解决**：
```bash
pip3 install playwright
playwright install chromium
```

### 问题2: "websockets not found"

**解决**：
```bash
pip3 install websockets requests
```

### 问题3: 半自动登录失败

**解决**：使用"手动模式"：
1. 浏览器访问 https://www.srdcloud.cn/login
2. 登录后按 F12 -> Network 标签
3. 刷新页面，查看任意请求的 Headers
4. 找到 `userid` 和 `sessionid`
5. 将这些值输入到应用的"手动输入"区域
6. 点击"保存凭证"

### 问题4: macOS 无法打开应用

**解决**：
```bash
xattr -cr "dist/CodeFree Desktop.app"
```

## 💡 使用技巧

1. **首次使用**：建议先运行源代码版本（`python3 gui_app.py`），测试无误后再打包
2. **凭证管理**：凭证会在本次会话中保留，关闭应用后会清除
3. **任务次数**：初次使用建议设置 10-20 次，熟悉后再增加
4. **控制台日志**：所有操作都有日志输出，遇到问题可查看控制台

## 🎯 下一步

- 阅读完整文档：[README.md](README.md)
- 了解原理：查看 `../python/README_*.md` 文档
- 自定义功能：修改 `gui_app.py` 源代码

## 🆘 需要帮助？

如果遇到问题：
1. 查看控制台输出的错误信息
2. 阅读 [README.md](README.md) 中的常见问题部分
3. 检查网络连接是否正常
4. 确认凭证是否有效（凭证有时效性）

祝使用愉快！🎉
