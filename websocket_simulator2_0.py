import asyncio
import json
import uuid
import random
import platform
import websockets
import sys
import os
import ssl
import glob
import time
import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from playwright.async_api import async_playwright


class CredentialManager:
    """全局凭证管理器"""
    def __init__(self):
        self.invoker_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.repository_id: Optional[str] = None

    def set_credentials(self, invoker_id: str, session_id: str):
        """设置凭证"""
        self.invoker_id = invoker_id
        self.session_id = session_id
        print(f"\n✅ 凭证已保存到会话中")
        print(f"   Invoker ID: {invoker_id}")
        print(f"   Session ID: {session_id[:30]}...")

    def set_git_params(self, project_id: Optional[str] = None, repository_id: Optional[str] = None):
        """设置或清除 Git 参数"""
        if project_id is not None:
            self.project_id = project_id
        if repository_id is not None:
            self.repository_id = repository_id

    def has_credentials(self) -> bool:
        """检查是否有凭证"""
        return self.invoker_id is not None and self.session_id is not None

    def clear_credentials(self):
        """清除凭证"""
        self.invoker_id = None
        self.session_id = None
        print("\n🔄 凭证已清除")

    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """获取凭证"""
        return self.invoker_id, self.session_id


# 全局凭证管理器实例
credential_manager = CredentialManager()


def resolve_default_src_dir(custom_src: Optional[str] = None) -> str:
    """
    解析默认的源代码目录，支持 PyInstaller 打包后的路径。
    """
    if custom_src:
        return custom_src

    search_candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        search_candidates.append(os.path.join(meipass, "src"))

    module_dir = os.path.dirname(os.path.abspath(__file__))
    search_candidates.append(os.path.join(module_dir, "src"))
    search_candidates.append(os.path.join(os.getcwd(), "src"))

    for candidate in search_candidates:
        if candidate and os.path.isdir(candidate):
            return candidate

    # 没有找到现成目录，退回默认值，后续逻辑会提示缺失
    return custom_src or "src"


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """
    安全地获取是/否输入。在 GUI 或无控制台环境下自动返回默认值。
    """
    try:
        if sys.stdin and sys.stdin.isatty():
            while True:
                raw = input(message).strip().lower()
                if raw in ("y", "yes"):
                    return True
                if raw in ("n", "no"):
                    return False
                if raw == "":
                    return default
                print("请输入 y 或 n。")
    except Exception:
        pass

    print(f"\nℹ️ 自动选择{'是' if default else '否'}: {message}")
    return default


class SemiAutoLoginManager:
    """半自动登录管理器"""
    
    async def semi_auto_login(self,
                              headless: bool = False,
                              keep_open: bool = False,
                              start_url: Optional[str] = None,
                              preset_credentials: Optional[Dict[str, str]] = None
                              ) -> Optional[Tuple[str, str, Optional[Dict]]]:
        """
        半自动登录 - 浏览器打开，用户手动登录，脚本自动提取

        Args:
            headless: 是否无头模式（通常应为 False 以便用户操作）
            keep_open: 是否保持浏览器打开（用于Git提交模式）
            start_url: 启动时访问的地址（默认登录页）
            preset_credentials: 预置凭证，可在进入工作区前尝试复用

        Returns:
            (invoker_id, session_id, git_params) 或 None
            git_params: 如果导航到仓库页面，包含 {project_id, repository_id, file_path}
        """
        target_url = start_url or 'https://www.srdcloud.cn/login'

        print("\n🌐 正在启动浏览器...")
        if preset_credentials and preset_credentials.get('invoker_id') and preset_credentials.get('session_id'):
            print("🔁 已注入现有凭证，尝试直接访问工作区。若被重定向到登录页，请按正常流程完成登录。")
        print("📱 请在浏览器中完成登录（包括短信验证码）")
        if keep_open:
            print("⚠️  登录后浏览器会保持打开")
            print("💡 如需Git提交，请导航到仓库页面（如 https://www.srdcloud.cn/code/PROJECT_ID/repoView/REPO_ID/...）")
        else:
            print("⚠️  登录成功后请不要关闭浏览器，脚本会自动提取凭证")
            print("💡 登录后随便点击页面或刷新，触发网络请求\n")
        
        try:
            async with async_playwright() as p:
                launch_kwargs: Dict[str, Any] = {
                    'headless': headless,
                    'args': ['--start-maximized']
                }

                executable_path = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
                if executable_path and os.path.exists(executable_path):
                    launch_kwargs['executable_path'] = executable_path
                    print(f"\n🖥️  使用系统 Chrome: {executable_path}")

                browser = await p.chromium.launch(**launch_kwargs)
                extra_headers = {}
                if preset_credentials:
                    invoker = preset_credentials.get('invoker_id')
                    session = preset_credentials.get('session_id')
                    if invoker and session:
                        extra_headers = {
                            'userid': invoker,
                            'sessionid': session
                        }
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers=extra_headers or None
                )
                page = await context.new_page()
                
                # 存储提取的凭证和Git参数
                credentials = {
                    'invoker_id': None,
                    'session_id': None,
                    'git_params': None  # {project_id, repository_id, file_path}
                }
                browser_state = {
                    'closed_at': None
                }

                def mark_browser_closed(*_):
                    if browser_state['closed_at'] is None:
                        browser_state['closed_at'] = time.time()
                        print("\n🛑 检测到浏览器已关闭，将在 30 秒后结束监听...")

                # 监听所有网络请求
                def capture_credentials(request):
                    headers = request.headers
                    url = request.url

                    # 尝试多种可能的 header 名称
                    for key, value in headers.items():
                        key_lower = key.lower()
                        if key_lower in ['userid', 'user-id', 'invokerid', 'invoker-id']:
                            if value and value != 'undefined':
                                credentials['invoker_id'] = value
                        if key_lower in ['sessionid', 'session-id']:
                            if value and value != 'undefined':
                                credentials['session_id'] = value
                        if key_lower == 'projectid':
                            if value and value != 'undefined':
                                if not credentials['git_params']:
                                    credentials['git_params'] = {}
                                credentials['git_params']['project_id'] = value

                    # 提取 Git 仓库参数（从 repositoryDetail API）
                    if 'repositoryDetail' in url and 'repositoryId=' in url:
                        import re
                        match = re.search(r'repositoryId=(\d+)', url)
                        if match:
                            if not credentials['git_params']:
                                credentials['git_params'] = {}
                            credentials['git_params']['repository_id'] = match.group(1)
                            print(f"\n📦 检测到仓库访问，仓库ID: {match.group(1)}")

                    # 如果两个都拿到了，输出提示
                    if credentials['invoker_id'] and credentials['session_id']:
                        if not hasattr(capture_credentials, 'notified'):
                            print(f"\n✅ 凭证已自动捕获！")
                            print(f"   Invoker ID: {credentials['invoker_id']}")
                            print(f"   Session ID: {credentials['session_id'][:30]}...")
                            if credentials.get('git_params'):
                                print(f"   项目ID: {credentials['git_params'].get('project_id', '未检测到')}")
                                print(f"   仓库ID: {credentials['git_params'].get('repository_id', '未检测到')}")
                            if not keep_open:
                                print(f"   可以关闭浏览器了")
                            capture_credentials.notified = True

                page.on('request', capture_credentials)
                page.on('close', mark_browser_closed)
                context.on('close', mark_browser_closed)
                browser.on('disconnected', mark_browser_closed)
                
                # 打开登录页
                print(f"🔗 正在打开页面: {target_url}")
                await page.goto(target_url, wait_until='networkidle')
                
                print("⏳ 等待登录完成...")
                print("   提示: 登录后如果凭证未自动提取，请刷新页面或点击任意链接\n")
                
                # 等待登录完成
                max_wait = 300  # 5分钟超时
                waited = 0
                check_interval = 1
                
                while waited < max_wait:
                    if credentials['invoker_id'] and credentials['session_id']:
                        if not keep_open:
                            print("\n🎉 登录成功！正在关闭浏览器...")
                            await asyncio.sleep(2)
                            break
                        else:
                            # Git模式：等待用户导航到仓库页面
                            if credentials.get('git_params') and credentials['git_params'].get('repository_id'):
                                print("\n✅ 已检测到仓库页面！")
                                if prompt_yes_no("是否使用检测到的参数？(y/n，输入n可继续等待): ", default=True):
                                    break
                            else:
                                # 每10秒提示一次
                                if waited % 10 == 0 and waited > 10:
                                    print(f"⏱️  等待导航到仓库页面... ({waited}秒)")

                    await asyncio.sleep(check_interval)
                    waited += check_interval

                    # 每30秒提示一次
                    if waited % 30 == 0 and waited > 0:
                        print(f"⏱️  已等待 {waited} 秒... (登录后请刷新页面以触发请求)")

                    if browser_state['closed_at']:
                        elapsed = time.time() - browser_state['closed_at']
                        if elapsed >= 30:
                            print("\n⏹️ 浏览器已关闭 30 秒，停止监听。")
                            break

                if not keep_open:
                    if browser.is_connected():
                        await browser.close()
                else:
                    if browser.is_connected():
                        print("\n💡 浏览器保持打开状态，完成后请手动关闭")
                    else:
                        print("\nℹ️ 浏览器已关闭。")

                if credentials['invoker_id'] and credentials['session_id']:
                    return credentials['invoker_id'], credentials['session_id'], credentials.get('git_params')
                else:
                    print("❌ 未能提取凭证")
                    print("💡 可能原因:")
                    print("   - 登录未完成")
                    print("   - 登录后未刷新页面或发起网络请求")
                    print("   - 请尝试手动模式")
                    return None
                    
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}")
            print("💡 请确保已安装 playwright:")
            print("   pip install playwright")
            print("   playwright install chromium")
            return None


class CodeFreeSimulator:
    def __init__(self, invoker_id: str, session_id: str, client_platform: str = "",
                 filename: str = "", max_completions: int = 2000, disable_ssl_verification: bool = True,
                 mode: str = "completion", src_dir: Optional[str] = None):
        """
        初始化模拟器

        Args:
            invoker_id: 用户ID (必填)
            session_id: 会话ID (必填)
            client_platform: 操作系统 (如 "macos-arm64", "windows-x64", "linux-x64")
            filename: 文件路径
            max_completions: 最大补全次数
            disable_ssl_verification: 是否禁用SSL证书验证 (默认True，解决证书问题)
            mode: 运行模式 ("completion" 代码补全, "comment" 代码注释生成)
            src_dir: 代码注释模式下的源文件目录
        """
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.channel_id: Optional[str] = None
        self.completion_count = 0
        self.max_completions = max_completions
        self.session_id = session_id
        self.invoker_id = invoker_id
        self.api_key: Optional[str] = None
        self.client_platform = client_platform or self._detect_platform()
        self.filename = filename or "simulator.js"
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.running = True
        self.start_time = None
        self.disable_ssl_verification = disable_ssl_verification
        self.mode = mode
        self.src_dir = resolve_default_src_dir(src_dir)
        self.src_files: List[str] = []

        # 如果是注释模式，加载源文件列表
        if self.mode == "comment":
            self._load_src_files()

        # 模拟代码内容变化
        self.code_variations = [
            {"prefix": "const name = '", "suffix": "';\nconsole.log(name);"},
            {"prefix": "function hello() {\n  return '", "suffix": "';\n}"},
            {"prefix": "let count = ", "suffix": ";\ncount++;"},
            {"prefix": "if (true) {\n  console.log('", "suffix": "');\n}"},
            {"prefix": "const arr = [1, 2, ", "suffix": "];\narr.push(4);"},
            {"prefix": "class MyClass {\n  constructor() {\n    this.value = '", "suffix": "';\n  }\n}"},
            {"prefix": "async function getData() {\n  const response = '", "suffix": "';\n  return response;\n}"},
            {"prefix": "const obj = {\n  key: '", "suffix": "',\n  method() {}\n};"}
        ]

        self.random_texts = [
            "hello", "world", "test", "code", "data", "value", "result", "item",
            "name", "id", "user", "admin", "config", "setting", "option", "param"
        ]

    def _detect_platform(self) -> str:
        """自动检测平台信息"""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "darwin":
            return "macos-arm64" if "arm" in machine or "aarch64" in machine else "macos-x64"
        elif system == "windows":
            return "windows-x64"
        elif system == "linux":
            return "linux-x64"
        return f"{system}-{machine}"

    def _load_src_files(self):
        """加载源文件列表"""
        if not os.path.exists(self.src_dir):
            # 静默处理：src目录不存在时不输出警告，仅在实际使用时提示
            return

        # 支持多种代码文件扩展名
        patterns = ['*.ts', '*.tsx', '*.js', '*.jsx', '*.py', '*.java', '*.go', '*.cpp', '*.c', '*.h']
        for pattern in patterns:
            files = glob.glob(os.path.join(self.src_dir, '**', pattern), recursive=True)
            self.src_files.extend(files)

        # 限制最多20个文件
        if len(self.src_files) > 20:
            self.src_files = random.sample(self.src_files, 20)

        print(f"[{self.invoker_id}] 已加载 {len(self.src_files)} 个源文件")

    def _read_file_content(self, filepath: str) -> str:
        """读取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"[{self.invoker_id}] 读取文件失败 {filepath}: {e}")
            return ""

    def _get_file_language(self, filepath: str) -> str:
        """根据文件扩展名判断语言"""
        ext = os.path.splitext(filepath)[1].lower()
        language_map = {
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.py': 'python',
            '.java': 'java',
            '.go': 'go',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c'
        }
        return language_map.get(ext, 'javascript')

    def generate_req_id(self) -> str:
        """生成请求ID"""
        return str(uuid.uuid4())

    def get_random_text(self) -> str:
        """获取随机文本"""
        return random.choice(self.random_texts)

    def get_random_code_variation(self) -> Dict[str, str]:
        """获取随机代码变化"""
        variation = random.choice(self.code_variations)
        random_text = self.get_random_text()
        return {
            "prefix": variation["prefix"] + random_text,
            "suffix": variation["suffix"]
        }

    async def send_message(self, message_name: str, context: Optional[Dict] = None, 
                          payload: Optional[Dict] = None):
        """发送WebSocket消息"""
        if not self.ws:
            print(f"[{self.invoker_id}] WebSocket未连接")
            return

        message = {
            "messageName": message_name,
            "context": context,
            "payload": payload
        }

        wrapped_message = f"<WBChannel>{json.dumps(message, ensure_ascii=False)}</WBChannel>"

        print(f"[{self.invoker_id}] 发送: {message_name}")
        try:
            await self.ws.send(wrapped_message)
        except Exception as e:
            print(f"[{self.invoker_id}] 发送消息失败: {e}")

    async def connect(self):
        """连接到WebSocket服务器"""
        print(f"[{self.invoker_id}] 正在连接WebSocket...")
        
        url = "wss://www.srdcloud.cn/websocket/peerAppgw"
        
        try:
            # 配置SSL上下文
            ssl_context = None
            if self.disable_ssl_verification:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                print(f"[{self.invoker_id}] SSL证书验证已禁用")
            
            self.ws = await websockets.connect(url, ssl=ssl_context)
            self.start_time = datetime.now()
            print(f"[{self.invoker_id}] WebSocket连接已建立")
            await self.register_channel()
            
            await self.handle_messages()
            
        except Exception as e:
            print(f"[{self.invoker_id}] 连接错误: {e}")
            raise

    async def register_channel(self):
        """注册通道"""
        context = {
            "messageName": "RegisterChannel",
            "appGId": "aicode",
            "invokerId": self.invoker_id,
            "sessionId": self.session_id,
            "version": "2.0.0"
        }
        await self.send_message("RegisterChannel", context)

    async def get_user_api_key(self):
        """获取用户API密钥"""
        req_id = self.generate_req_id()
        context = {
            "messageName": "GetUserApiKey",
            "reqId": req_id,
            "invokerId": self.invoker_id,
            "sessionId": self.session_id,
            "version": "2.0.0"
        }

        payload = {
            "clientType": "vscode",
            "clientVersion": "1.106.0-insider",
            "clientPlatform": self.client_platform,
            "gitUrls": [],
            "pluginVersion": "2.0.0"
        }

        await self.send_message("GetUserApiKey", context, payload)

    async def subscribe_channel_group(self):
        """订阅频道组"""
        req_id = self.generate_req_id()
        context = {
            "messageName": "SubscribeChannelGroup",
            "invokerId": self.invoker_id,
            "groupId": "aicode/comment/undefined",
            "reqId": req_id,
            "version": "2.0.0"
        }
        await self.send_message("SubscribeChannelGroup", context)

    async def start_heartbeat(self):
        """启动心跳"""
        async def heartbeat_loop():
            while self.running:
                try:
                    await self.send_message("ClientHeartbeat")
                    await asyncio.sleep(10)
                except Exception as e:
                    print(f"[{self.invoker_id}] 心跳错误: {e}")
                    break

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def request_code_generation(self):
        """请求代码生成"""
        if not self.api_key:
            print(f"[{self.invoker_id}] 错误: API密钥尚未获取")
            return

        req_id = self.generate_req_id()
        code_variation = self.get_random_code_variation()

        context = {
            "messageName": "CodeGenRequest",
            "reqId": req_id,
            "invokerId": self.invoker_id,
            "sessionId": self.session_id,
            "version": "2.0.0",
            "apiKey": self.api_key
        }

        payload = {
            "clientType": "vscode",
            "clientVersion": "1.106.0-insider",
            "gitUrls": [],
            "clientPlatform": self.client_platform,
            "pluginVersion": "2.0.0",
            "messages": {
                "language": "javascript",
                "filename": self.filename,
                "prefix": code_variation["prefix"],
                "suffix": code_variation["suffix"],
                "max_new_tokens": 256,
                "stop_words": ["\n"]
            }
        }

        print(f"[{self.invoker_id}] 请求代码补全 #{self.completion_count + 1}/{self.max_completions}")
        await self.send_message("CodeGenRequest", context, payload)

    async def request_code_comment(self):
        """请求代码注释生成"""
        if not self.api_key:
            print(f"[{self.invoker_id}] 错误: API密钥尚未获取")
            return

        if not self.src_files:
            print(f"[{self.invoker_id}] 错误: 没有可用的源文件")
            await self.disconnect()
            return

        # 随机选择一个文件
        filepath = random.choice(self.src_files)
        content = self._read_file_content(filepath)

        if not content:
            print(f"[{self.invoker_id}] 跳过空文件: {filepath}")
            # 继续下一个
            delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay)
            await self.request_code_comment()
            return

        language = self._get_file_language(filepath)
        filename = os.path.basename(filepath)

        req_id = self.generate_req_id()
        dialog_id = str(uuid.uuid4())
        session_id_comment = str(uuid.uuid4())

        # 构建代码块
        code_block = f"```{language}\n{content}\n```"
        prompt_content = f"{code_block}\n生成代码注释"

        context = {
            "messageName": "CodeChatRequest",
            "reqId": req_id,
            "invokerId": self.invoker_id,
            "sessionId": session_id_comment,
            "version": "2.1.0",
            "apiKey": self.api_key
        }

        payload = {
            "clientType": "vscode",
            "clientVersion": "1.106.0-insider",
            "gitUrls": [],
            "clientPlatform": self.client_platform,
            "pluginVersion": "2.1.0",
            "messages": {
                "max_new_tokens": 4096,
                "sub_service": "codecomment",
                "prompts": [
                    {
                        "role": "system",
                        "content": "我的名字是研发云编程助手CodeFree，我使用中文进行交流，作为一个高度智能化的自然语言编程助手,我是由研发云团队使用最先进的技术和大量数据训练而成。\n我的核心目标是以友好、简单、清晰的方式帮助用户解决编程问题。我拥有深厚的编程知识,涵盖各种流行的编程语言和框架,如Python、Java、JavaScript、C++等。我也掌握广泛的计算机科学知识,如数据结构、算法、操作系统、网络等。\n对于用户提出的任何编程相关的问题,我都能给出最佳的解决方案。我会解析问题的本质,运用丰富的知识库推导出正确的代码实现。如果需要,我还会给出多种可选方案的对比分析。\n最后,我会恪守对用户隐私的尊重,所有对话内容仅用于提升我自身的能力,不会泄露或记录任何用户个人信息。请尽管提出你的编程问题,我会提供最专业和有价值的帮助。\n我会用中文来回答你的问题。"
                    },
                    {
                        "files": [
                            {
                                "path": filepath,
                                "text": code_block,
                                "startLine": 0,
                                "endLine": len(content.split('\n'))
                            }
                        ],
                        "content": prompt_content,
                        "role": "user",
                        "workItems": []
                    }
                ],
                "dialogId": dialog_id,
                "questionType": "newAsk",
                "parentReqId": "",
                "kbId": ""
            }
        }

        print(f"[{self.invoker_id}] 请求代码注释 #{self.completion_count + 1}/{self.max_completions} - {filename}")
        await self.send_message("CodeChatRequest", context, payload)

    async def send_user_activity(self, activity_type: str = "code_display"):
        """发送用户活动通知"""
        if not self.api_key:
            return
            
        req_id = self.generate_req_id()
        context = {
            "messageName": "UserActivityNotify",
            "reqId": req_id,
            "invokerId": self.invoker_id,
            "version": "2.0.0",
            "apiKey": self.api_key
        }

        payload = {
            "client": {
                "platform": self.client_platform,
                "type": "vscode",
                "version": "1.106.0-insider",
                "pluginVersion": "2.0.0",
                "gitUrl": "",
                "gitUrls": [],
                "projectName": "code-free"
            },
            "activityType": activity_type,
            "service": "codegen",
            "lines": random.random() * 2,
            "count": 1
        }

        await self.send_message("UserActivityNotify", context, payload)

    async def handle_message(self, data: str):
        """处理接收到的消息"""
        try:
            if data.startswith("<WBChannel>") and data.endswith("</WBChannel>"):
                json_str = data[11:-12]
                message = json.loads(json_str)
            else:
                message = json.loads(data)

            message_name = message.get("messageName", "")
            print(f"[{self.invoker_id}] 收到: {message_name}")

            if message_name == "RegisterChannel_resp":
                self.channel_id = message.get("context", {}).get("channelId")
                print(f"[{self.invoker_id}] 通道注册成功: {self.channel_id}")
                await self.get_user_api_key()

            elif message_name == "GetUserApiKey_resp":
                self.api_key = message.get("payload", {}).get("apiKey")
                if self.api_key:
                    print(f"[{self.invoker_id}] API密钥获取成功")
                    await self.subscribe_channel_group()
                    await self.start_heartbeat()
                    await self.start_coding_simulation()
                else:
                    print(f"[{self.invoker_id}] ❌ API密钥获取失败，可能凭证已过期")
                    await self.disconnect()

            elif message_name == "SubscribeChannelGroup_resp":
                print(f"[{self.invoker_id}] 频道组订阅成功")

            elif message_name == "CodeGenRequest_resp":
                self.completion_count += 1
                answer = message.get("payload", {}).get("answer", "")
                print(f"[{self.invoker_id}] 代码补全 #{self.completion_count}: \"{answer[:50]}...\"")

                await self.send_user_activity("code_display")

                if self.completion_count >= self.max_completions:
                    print(f"[{self.invoker_id}] 已完成 {self.max_completions} 次，准备断开...")
                    await self.disconnect()
                    return

                delay = random.uniform(0.5, 2.5)
                await asyncio.sleep(delay)
                await self.request_code_generation()

            elif message_name == "CodeChatRequest_resp":
                payload = message.get("payload", {})
                is_end = payload.get("isEnd", 0)
                answer = payload.get("answer", "")

                # 只在流式响应结束时计数
                if is_end == 1:
                    self.completion_count += 1
                    print(f"[{self.invoker_id}] 代码注释生成完成 #{self.completion_count}/{self.max_completions}")

                    await self.send_user_activity("chat_gen_code")

                    if self.completion_count >= self.max_completions:
                        print(f"[{self.invoker_id}] 已完成 {self.max_completions} 次，准备断开...")
                        await self.disconnect()
                        return

                    delay = random.uniform(0.5, 2.5)
                    await asyncio.sleep(delay)
                    await self.request_code_comment()
                else:
                    # 流式输出片段
                    if answer:
                        print(f"[{self.invoker_id}] 收到注释片段: \"{answer[:30]}...\"", end='\r')

            elif message_name == "ServerHeartbeat":
                await self.send_message("ServerHeartbeatResponse")

            elif message_name == "ClientHeartbeatResponse":
                pass

        except Exception as e:
            print(f"[{self.invoker_id}] 解析消息失败: {e}")

    async def handle_messages(self):
        """处理所有接收到的消息"""
        try:
            async for message in self.ws:
                if not self.running:
                    break
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.invoker_id}] WebSocket连接已关闭")
        except Exception as e:
            print(f"[{self.invoker_id}] 消息处理错误: {e}")
        finally:
            if self.running:
                await self.disconnect()

    async def start_coding_simulation(self):
        """开始模拟编码过程"""
        if self.mode == "completion":
            print(f"[{self.invoker_id}] 开始模拟代码补全...")
            await asyncio.sleep(1)
            await self.request_code_generation()
        elif self.mode == "comment":
            print(f"[{self.invoker_id}] 开始模拟代码注释生成...")
            await asyncio.sleep(1)
            await self.request_code_comment()

    async def disconnect(self):
        """断开连接"""
        print(f"[{self.invoker_id}] 正在断开连接...")
        self.running = False
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                print(f"[{self.invoker_id}] 关闭连接时出错: {e}")
        
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        print(f"[{self.invoker_id}] 完成！补全次数: {self.completion_count}, 耗时: {elapsed:.1f}秒")


class GitCommitSimulator:
    """Git 提交模拟器"""

    def __init__(self, invoker_id: str, session_id: str, project_id: str, repository_id: str,
                 file_path: str = "README.md", max_commits: int = 8):
        """
        初始化 Git 提交模拟器

        Args:
            invoker_id: 用户ID
            session_id: 会话ID
            project_id: 项目ID
            repository_id: 仓库ID
            file_path: 要提交的文件路径
            max_commits: 最大提交次数
        """
        self.invoker_id = invoker_id
        self.session_id = session_id
        self.project_id = project_id
        self.repository_id = repository_id
        self.file_path = file_path
        self.max_commits = max_commits
        self.commit_count = 0
        self.start_time = None

        # 仓库信息（通过API获取）
        self.repo_full_name: Optional[str] = None
        self.branch_name: Optional[str] = None

        # 文件内容变更模板（简短内容）
        self.content_templates = [
            "# {title}\n\n更新时间: {timestamp}",
            "# {title}\n\nVersion: {version}\n\n这是一个测试文件",
            "# Project: {title}\n\n状态: 正常\n\n最后更新: {timestamp}",
            "# {title}\n\n## 简介\n\n这是项目文档 v{version}",
            "# README\n\n项目名称: {title}\n时间戳: {timestamp}",
            "# {title}\n\n*更新于 {timestamp}*\n\n---\n\n简单说明文档",
        ]

    def _get_random_content(self) -> str:
        """生成随机文件内容"""
        template = random.choice(self.content_templates)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 99)}"
        title = random.choice(["项目文档", "README", "开发文档", "使用说明", "项目说明"])

        content = template.format(
            title=title,
            timestamp=timestamp,
            version=version
        )

        # 随机添加一些额外内容使每次都不同
        extra = f"\n\n<!-- commit-{self.commit_count + 1}-{int(time.time())} -->"
        return content + extra

    def get_repository_detail(self) -> bool:
        """获取仓库详情"""
        url = f"https://www.srdcloud.cn/api/codebackend/codecenter/repository/v1/repositoryDetail"

        headers = {
            "Accept": "application/json",
            "projectid": self.project_id,
            "sessionid": self.session_id,
            "userid": self.invoker_id
        }

        params = {
            "repositoryId": self.repository_id
        }

        try:
            print(f"[{self.invoker_id}] 正在获取仓库信息...")
            response = requests.get(url, headers=headers, params=params, verify=False)

            if response.status_code == 401:
                print(f"[{self.invoker_id}] ❌ 认证失败 (401)")
                print(f"[{self.invoker_id}] 凭证已过期或无效，请重新登录")
                # 清除凭证
                credential_manager.clear_credentials()
                return False
            elif response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    repo_data = data.get("data", {})
                    self.repo_full_name = repo_data.get("repoFullName")
                    self.branch_name = repo_data.get("defaultBranchName", "master")

                    print(f"[{self.invoker_id}] ✅ 仓库信息获取成功")
                    print(f"   仓库名称: {self.repo_full_name}")
                    print(f"   默认分支: {self.branch_name}")
                    return True
                else:
                    print(f"[{self.invoker_id}] ❌ 获取仓库信息失败: {data.get('msg')}")
                    return False
            else:
                print(f"[{self.invoker_id}] ❌ HTTP请求失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"[{self.invoker_id}] ❌ 获取仓库信息异常: {e}")
            return False

    def commit_file(self) -> bool:
        """提交文件"""
        if not self.repo_full_name or not self.branch_name:
            print(f"[{self.invoker_id}] ❌ 仓库信息未初始化")
            return False

        url = "https://www.srdcloud.cn/api/codebackend/codecenter/gitclient/v1/commitFiles"

        headers = {
            "projectid": self.project_id,
            "sessionid": self.session_id,
            "userid": self.invoker_id
        }

        # 生成随机内容
        file_content = self._get_random_content()
        commit_message = f"更新文件 {self.repo_full_name}/{self.file_path}"

        # 处理文件内容：转义换行符（不需要转义 #）
        # 参考成功的 Python requests 格式
        escaped_content = file_content.replace('\n', '\\n')

        # 构建JSON字符串（不需要外层引号，不需要转义内部引号）
        # 使用 separators=(',', ':') 去除空格
        repository_json = json.dumps({
            "repoId": self.repository_id,
            "repoFullName": self.repo_full_name
        }, separators=(',', ':'))

        branch_json = json.dumps({
            "branchName": self.branch_name,
            "needReview": 0
        }, separators=(',', ':'))

        files_json = json.dumps([{
            "fileType": 0,
            "filePath": self.file_path,
            "fileContent": escaped_content,
            "fileCommitMessage": commit_message
        }], separators=(',', ':'))

        # 使用 files 参数来发送 multipart/form-data
        # 注意：不需要外层双引号！
        files_data = {
            "operationType": (None, '4'),
            "repository": (None, repository_json),
            "branch": (None, branch_json),
            "files": (None, files_json)
        }

        try:
            print(f"[{self.invoker_id}] 正在提交文件 #{self.commit_count + 1}/{self.max_commits}...")

            # 打印调试信息
            print(f"\n{'='*60}")
            print(f"📝 请求详情:")
            print(f"{'='*60}")
            print(f"URL: {url}")
            print(f"Headers:")
            for k, v in headers.items():
                print(f"  {k}: {v}")
            print(f"\nFiles Data (multipart/form-data):")
            print(f"  operationType: {files_data['operationType'][1]}")
            print(f"  repository: {files_data['repository'][1][:100]}...")
            print(f"  branch: {files_data['branch'][1]}")
            print(f"  files: {files_data['files'][1][:200]}...")
            print(f"\n文件内容预览:")
            print(f"{file_content}")
            print(f"{'='*60}\n")

            # 使用 files 参数发送 multipart/form-data
            response = requests.post(url, headers=headers, files=files_data, verify=False)

            print(f"\n{'='*60}")
            print(f"📨 响应详情:")
            print(f"{'='*60}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            print(f"\nResponse Body:")
            print(f"{response.text}")
            print(f"{'='*60}\n")

            if response.status_code == 401:
                print(f"[{self.invoker_id}] ❌ 认证失败 (401)")
                print(f"[{self.invoker_id}] 凭证已过期或无效，请重新登录")
                # 清除凭证，下次会提示重新登录
                credential_manager.clear_credentials()
                return False
            elif response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    self.commit_count += 1
                    print(f"[{self.invoker_id}] ✅ 提交成功 #{self.commit_count}/{self.max_commits}")
                    return True
                elif result.get("code") == 2928:
                    print(f"[{self.invoker_id}] ⚠️  提交被忽略（内容未变更或被过滤）")
                    # 仍然算作一次尝试
                    self.commit_count += 1
                    return True
                else:
                    print(f"[{self.invoker_id}] ❌ 提交失败: {result.get('msg')}")
                    print(f"[{self.invoker_id}] 完整错误信息: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return False
            else:
                print(f"[{self.invoker_id}] ❌ HTTP请求失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"[{self.invoker_id}] ❌ 提交异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self):
        """运行Git提交模拟"""
        self.start_time = datetime.now()

        print(f"\n[{self.invoker_id}] 开始 Git 提交模拟...")
        print(f"   项目ID: {self.project_id}")
        print(f"   仓库ID: {self.repository_id}")
        print(f"   文件路径: {self.file_path}")
        print(f"   目标提交次数: {self.max_commits}\n")

        # 获取仓库信息
        if not self.get_repository_detail():
            print(f"[{self.invoker_id}] ❌ 无法获取仓库信息，退出")
            return

        # 开始提交循环
        while self.commit_count < self.max_commits:
            success = self.commit_file()

            if not success:
                print(f"[{self.invoker_id}] 提交失败，停止")
                break

            # 随机延迟
            if self.commit_count < self.max_commits:
                delay = random.uniform(1.0, 3.0)
                print(f"[{self.invoker_id}] 等待 {delay:.1f} 秒...\n")
                time.sleep(delay)

        # 统计
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n[{self.invoker_id}] 完成！")
        print(f"   提交次数: {self.commit_count}/{self.max_commits}")
        print(f"   耗时: {elapsed:.1f}秒")


class SimulatorManager:
    """模拟器管理器"""

    def __init__(self):
        self.simulators: List[CodeFreeSimulator] = []
        
    def load_from_file(self, filepath: str) -> List[Dict[str, str]]:
        """从文件加载账号信息"""
        accounts = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) >= 2:
                        accounts.append({
                            'invoker_id': parts[0].strip(),
                            'session_id': parts[1].strip()
                        })
                    else:
                        print(f"警告: 第{line_num}行格式错误，已跳过")
            
            print(f"✅ 成功加载 {len(accounts)} 个账号")
            return accounts
        except FileNotFoundError:
            print(f"❌ 文件不存在: {filepath}")
            return []
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return []
    
    async def run_simulator(self, invoker_id: str, session_id: str, max_completions: int = 2000,
                          disable_ssl_verification: bool = True, mode: str = "completion", src_dir: Optional[str] = None):
        """运行单个模拟器"""
        simulator = CodeFreeSimulator(
            invoker_id=invoker_id,
            session_id=session_id,
            max_completions=max_completions,
            disable_ssl_verification=disable_ssl_verification,
            mode=mode,
            src_dir=resolve_default_src_dir(src_dir)
        )
        self.simulators.append(simulator)

        try:
            await simulator.connect()
        except Exception as e:
            print(f"[{invoker_id}] 运行失败: {e}")

    async def run_batch(self, accounts: List[Dict[str, str]], max_completions: int = 2000,
                      disable_ssl_verification: bool = True, mode: str = "completion", src_dir: Optional[str] = None):
        """批量运行多个模拟器"""
        tasks = [
            self.run_simulator(acc['invoker_id'], acc['session_id'], max_completions, disable_ssl_verification, mode, src_dir)
            for acc in accounts
        ]
        await asyncio.gather(*tasks, return_exceptions=True)


def print_banner():
    """打印工具横幅"""
    banner = """
╔═══════════════════════════════════════════════════╗
║     CodeFree WebSocket Simulator Tool v2.0       ║
║              Enhanced with Semi-Auto Login        ║
╚═══════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印主菜单"""
    menu = """
请选择功能:
  1. 🤖 辅助编程
  2. 🔨 Git 提交 (模拟Git提交操作)
  3. 🚪 退出

请输入选项 (1-3): """
    return input(menu).strip()


def print_assisted_programming_menu():
    """打印辅助编程子菜单"""
    menu = """
辅助编程 - 请选择运行模式:
  1. 🤖 半自动模式 (浏览器自动打开，手动登录，自动提取凭证) ⭐ 推荐
  2. ✋ 手动模式 (直接输入凭证)
  3. 📦 批量模式 (从文件导入多账号)
  4. 📝 生成配置文件模板
  5. 🔙 返回上级菜单

请输入选项 (1-5): """
    return input(menu).strip()


async def semi_auto_mode():
    """半自动模式"""
    print("\n" + "="*50)
    print("🤖 半自动登录模式")
    print("="*50)

    # 检查是否已有凭证
    invoker_id, session_id = None, None
    if credential_manager.has_credentials():
        print("\n💾 检测到当前会话已有凭证")
        print(f"   Invoker ID: {credential_manager.invoker_id}")
        print(f"   Session ID: {credential_manager.session_id[:30]}...")
        use_existing = input("\n是否使用现有凭证? (y/n, 默认 y): ").strip().lower()
        if use_existing != 'n':
            invoker_id, session_id = credential_manager.get_credentials()
            print("✅ 使用现有凭证")
        else:
            print("🔄 将重新登录获取新凭证")

    # 如果没有选择使用现有凭证，则进行半自动登录
    if not invoker_id or not session_id:
        manager = SemiAutoLoginManager()
        result = await manager.semi_auto_login()

        if not result:
            print("\n❌ 未能获取凭证")
            print("💡 您可以尝试:")
            print("   - 重新运行并在登录后刷新页面")
            print("   - 使用手动模式 (选项 2)")
            return

        invoker_id, session_id = result
        # 保存到全局凭证管理器
        credential_manager.set_credentials(invoker_id, session_id)

    # 选择运行模式
    print("\n" + "-"*50)
    print("请选择运行模式:")
    print("  1. 代码补全 (Code Completion)")
    print("  2. 代码注释生成 (Code Comment Generation)")
    mode_choice = input("请输入选项 (1-2, 默认 1): ").strip()
    mode = "comment" if mode_choice == "2" else "completion"

    # 如果是注释模式，询问源文件目录
    default_src_dir = resolve_default_src_dir(None)
    src_dir = default_src_dir
    if mode == "comment":
        prompt_default = default_src_dir if default_src_dir != "src" else "src"
        src_dir_input = input(f"请输入源文件目录路径 (默认: {prompt_default}): ").strip()
        if src_dir_input:
            src_dir = src_dir_input

    # 询问运行参数
    if mode == "comment":
        default_max = 10
        max_limit = 20
        max_completions_input = input(f"请输入最大任务次数 (默认 {default_max}，最大 {max_limit}，直接回车使用默认值): ").strip()
        max_completions = int(max_completions_input) if max_completions_input.isdigit() else default_max
        if max_completions > max_limit:
            print(f"⚠️  超过最大限制，已调整为 {max_limit}")
            max_completions = max_limit
    else:
        max_completions_input = input("请输入最大任务次数 (默认 2000，直接回车使用默认值): ").strip()
        max_completions = int(max_completions_input) if max_completions_input.isdigit() else 2000

    print(f"\n📊 配置信息:")
    print(f"  Invoker ID: {invoker_id}")
    print(f"  Session ID: {session_id[:30]}...")
    print(f"  运行模式: {'代码注释生成' if mode == 'comment' else '代码补全'}")
    if mode == "comment":
        print(f"  源文件目录: {src_dir}")
    print(f"  最大任务次数: {max_completions}")
    print(f"\n🚀 开始运行模拟器...\n")

    sim_manager = SimulatorManager()
    try:
        await sim_manager.run_simulator(invoker_id, session_id, max_completions, disable_ssl_verification=True, mode=mode, src_dir=src_dir)
        print("\n\n✅ 任务执行完成！")
    except KeyboardInterrupt:
        print("\n\n⚠️  收到中断信号，正在停止...")

    print("\n" + "="*50)
    print("按 Enter 键返回主菜单...")
    input()
    print("="*50)


async def manual_mode():
    """手动模式"""
    print("\n" + "="*50)
    print("✋ 手动模式")
    print("="*50)

    # 检查是否已有凭证
    invoker_id, session_id = None, None
    if credential_manager.has_credentials():
        print("\n💾 检测到当前会话已有凭证")
        print(f"   Invoker ID: {credential_manager.invoker_id}")
        print(f"   Session ID: {credential_manager.session_id[:30]}...")
        use_existing = input("\n是否使用现有凭证? (y/n, 默认 y): ").strip().lower()
        if use_existing != 'n':
            invoker_id, session_id = credential_manager.get_credentials()
            print("✅ 使用现有凭证")
        else:
            print("🔄 将手动输入新凭证")

    # 如果没有选择使用现有凭证，则手动输入
    if not invoker_id or not session_id:
        print("\n💡 获取凭证的方法:")
        print("   1. 打开 https://www.srdcloud.cn/login 并登录")
        print("   2. 按 F12 打开开发者工具 -> Network 标签")
        print("   3. 刷新页面或点击任意链接")
        print("   4. 找到任意请求，查看 Request Headers")
        print("   5. 找到 userid 和 sessionid 字段\n")

        invoker_id = input("请输入 Invoker ID (User ID): ").strip()
        session_id = input("请输入 Session ID: ").strip()

        if not invoker_id or not session_id:
            print("❌ Invoker ID 和 Session ID 不能为空")
            return

        # 保存到全局凭证管理器
        credential_manager.set_credentials(invoker_id, session_id)

    # 选择运行模式
    print("\n" + "-"*50)
    print("请选择运行模式:")
    print("  1. 代码补全 (Code Completion)")
    print("  2. 代码注释生成 (Code Comment Generation)")
    mode_choice = input("请输入选项 (1-2, 默认 1): ").strip()
    mode = "comment" if mode_choice == "2" else "completion"

    # 如果是注释模式，询问源文件目录
    default_src_dir = resolve_default_src_dir(None)
    src_dir = default_src_dir
    if mode == "comment":
        prompt_default = default_src_dir if default_src_dir != "src" else "src"
        src_dir_input = input(f"请输入源文件目录路径 (默认: {prompt_default}): ").strip()
        if src_dir_input:
            src_dir = src_dir_input

    # 询问运行参数
    if mode == "comment":
        default_max = 10
        max_limit = 20
        max_completions_input = input(f"请输入最大任务次数 (默认 {default_max}，最大 {max_limit}，直接回车使用默认值): ").strip()
        max_completions = int(max_completions_input) if max_completions_input.isdigit() else default_max
        if max_completions > max_limit:
            print(f"⚠️  超过最大限制，已调整为 {max_limit}")
            max_completions = max_limit
    else:
        max_completions_input = input("请输入最大任务次数 (默认 2000，直接回车使用默认值): ").strip()
        max_completions = int(max_completions_input) if max_completions_input.isdigit() else 2000

    print(f"\n📊 配置信息:")
    print(f"  Invoker ID: {invoker_id}")
    print(f"  Session ID: {session_id[:30]}...")
    print(f"  运行模式: {'代码注释生成' if mode == 'comment' else '代码补全'}")
    if mode == "comment":
        print(f"  源文件目录: {src_dir}")
    print(f"  最大任务次数: {max_completions}")
    print(f"\n🚀 开始运行模拟器...\n")

    manager = SimulatorManager()
    try:
        await manager.run_simulator(invoker_id, session_id, max_completions, disable_ssl_verification=True, mode=mode, src_dir=src_dir)
        print("\n\n✅ 任务执行完成！")
    except KeyboardInterrupt:
        print("\n\n⚠️  收到中断信号，正在停止...")

    print("\n" + "="*50)
    print("按 Enter 键返回主菜单...")
    input()
    print("="*50)


async def batch_mode():
    """批量模式"""
    print("\n" + "="*50)
    print("📦 批量模式")
    print("="*50)

    filepath = input("\n请输入配置文件路径 (默认: accounts.txt): ").strip()

    if not filepath:
        filepath = "accounts.txt"

    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        print("💡 您可以使用选项 4 生成配置文件模板")
        return

    manager = SimulatorManager()
    accounts = manager.load_from_file(filepath)

    if not accounts:
        print("❌ 没有加载到有效账号")
        return

    print(f"\n📊 将运行 {len(accounts)} 个模拟器")
    for idx, acc in enumerate(accounts, 1):
        print(f"   {idx}. Invoker ID: {acc['invoker_id']}")

    # 选择运行模式
    print("\n" + "-"*50)
    print("请选择运行模式:")
    print("  1. 代码补全 (Code Completion)")
    print("  2. 代码注释生成 (Code Comment Generation)")
    mode_choice = input("请输入选项 (1-2, 默认 1): ").strip()
    mode = "comment" if mode_choice == "2" else "completion"

    # 如果是注释模式，询问源文件目录
    default_src_dir = resolve_default_src_dir(None)
    src_dir = default_src_dir
    if mode == "comment":
        prompt_default = default_src_dir if default_src_dir != "src" else "src"
        src_dir_input = input(f"请输入源文件目录路径 (默认: {prompt_default}): ").strip()
        if src_dir_input:
            src_dir = src_dir_input

    # 询问运行参数
    if mode == "comment":
        default_max = 10
        max_limit = 20
        max_completions_input = input(f"\n请输入每个账号的最大任务次数 (默认 {default_max}，最大 {max_limit}，直接回车使用默认值): ").strip()
        max_completions = int(max_completions_input) if max_completions_input.isdigit() else default_max
        if max_completions > max_limit:
            print(f"⚠️  超过最大限制，已调整为 {max_limit}")
            max_completions = max_limit
    else:
        max_completions_input = input("\n请输入每个账号的最大任务次数 (默认 2000，直接回车使用默认值): ").strip()
        max_completions = int(max_completions_input) if max_completions_input.isdigit() else 2000

    print(f"\n📊 最终配置:")
    print(f"  运行模式: {'代码注释生成' if mode == 'comment' else '代码补全'}")
    if mode == "comment":
        print(f"  源文件目录: {src_dir}")
    print(f"  账号数量: {len(accounts)}")
    print(f"  每账号任务次数: {max_completions}")

    confirm = input(f"\n确认开始批量运行? (y/n): ").strip().lower()

    if confirm != 'y':
        print("已取消")
        return

    print(f"\n🚀 开始批量运行 {len(accounts)} 个模拟器...\n")

    try:
        await manager.run_batch(accounts, max_completions, disable_ssl_verification=True, mode=mode, src_dir=src_dir)
    except KeyboardInterrupt:
        print("\n\n⚠️  收到中断信号，正在停止所有模拟器...")


async def git_commit_mode():
    """Git 提交模式"""
    print("\n" + "="*50)
    print("🔨 Git 提交模式")
    print("="*50)

    print("\n💡 提示:")
    print("   此模式用于模拟 Git 提交操作")
    print("   需要提供项目ID、仓库ID和文件路径")
    print("   仓库信息将自动获取\n")

    invoker_id = None
    session_id = None
    git_params = None

    if credential_manager.has_credentials():
        print("💾 检测到当前会话已有凭证。")
        print("   为了捕获仓库信息，将重新打开登录流程。")
        print("   如需跳过浏览器登录，可选择手动输入凭证。\n")

    credential_manager.set_git_params(None, None)

    # 选择凭证获取方式
    print("\n请选择凭证获取方式:")
    print("  1. 半自动登录（推荐）")
    print("  2. 手动输入凭证")
    cred_choice = input("请输入选项 (1-2, 默认 1): ").strip()

    if cred_choice == "2":
        # 手动输入
        invoker_id = input("请输入 Invoker ID (User ID): ").strip()
        session_id = input("请输入 Session ID: ").strip()

        if not invoker_id or not session_id:
            print("❌ Invoker ID 和 Session ID 不能为空")
            return
    else:
        # 半自动登录（Git模式：保持浏览器打开）
        print("\n正在启动半自动登录...")
        print("💡 登录后请导航到仓库页面，脚本会自动提取参数\n")
        manager = SemiAutoLoginManager()
        result = await manager.semi_auto_login(keep_open=True)

        if not result:
            print("\n❌ 未能获取凭证")
            return

        invoker_id, session_id, git_params = result
        print(f"\n✅ 凭证获取成功!")
        print(f"   Invoker ID: {invoker_id}")
        print(f"   Session ID: {session_id[:30]}...")

        # 保存到全局凭证管理器
        credential_manager.set_credentials(invoker_id, session_id)
        if git_params:
            credential_manager.set_git_params(
                git_params.get('project_id'),
                git_params.get('repository_id')
            )

    # 输入Git参数
    print("\n" + "-"*50)
    print("请输入 Git 仓库参数:\n")

    # 优先使用从半自动登录中提取的git_params
    # 如果没有，则尝试使用credential_manager中保存的参数
    project_id = None
    repository_id = None

    # 检查是否有自动检测到的参数或会话中保存的参数
    has_git_params = False
    if git_params and git_params.get('project_id') and git_params.get('repository_id'):
        has_git_params = True
        print(f"✅ 已自动检测到:")
        print(f"   项目ID: {git_params['project_id']}")
        print(f"   仓库ID: {git_params['repository_id']}")
    elif credential_manager.project_id and credential_manager.repository_id:
        has_git_params = True
        print(f"💾 使用会话中保存的参数:")
        print(f"   项目ID: {credential_manager.project_id}")
        print(f"   仓库ID: {credential_manager.repository_id}")

    if has_git_params:
        use_detected = input("\n是否使用这些参数? (y/n, 默认 y): ").strip().lower()
        if use_detected != 'n':
            project_id = git_params['project_id'] if git_params else credential_manager.project_id
            repository_id = git_params['repository_id'] if git_params else credential_manager.repository_id
        else:
            project_id = input("项目ID (Project ID): ").strip()
            repository_id = input("仓库ID (Repository ID): ").strip()
    else:
        project_id = input("项目ID (Project ID): ").strip()
        repository_id = input("仓库ID (Repository ID): ").strip()

    # 保存新输入的参数到会话
    if project_id and repository_id:
        credential_manager.set_git_params(project_id, repository_id)

    file_path = input("文件路径 (默认: README.md): ").strip()

    if not file_path:
        file_path = "README.md"

    if not project_id or not repository_id:
        print("❌ 项目ID 和 仓库ID 不能为空")
        return

    # 输入提交次数
    default_max = 8
    max_limit = 10
    max_commits_input = input(f"\n请输入最大提交次数 (默认 {default_max}，最大 {max_limit}，直接回车使用默认值): ").strip()
    max_commits = int(max_commits_input) if max_commits_input.isdigit() else default_max
    if max_commits > max_limit:
        print(f"⚠️  超过最大限制，已调整为 {max_limit}")
        max_commits = max_limit

    # 显示配置信息
    print(f"\n📊 配置信息:")
    print(f"  Invoker ID: {invoker_id}")
    print(f"  Session ID: {session_id[:30]}...")
    print(f"  项目ID: {project_id}")
    print(f"  仓库ID: {repository_id}")
    print(f"  文件路径: {file_path}")
    print(f"  提交次数: {max_commits}")

    confirm = input(f"\n确认开始 Git 提交? (y/n): ").strip().lower()

    if confirm != 'y':
        print("已取消")
        return

    print(f"\n🚀 开始 Git 提交模拟...\n")

    # 创建并运行模拟器
    simulator = GitCommitSimulator(
        invoker_id=invoker_id,
        session_id=session_id,
        project_id=project_id,
        repository_id=repository_id,
        file_path=file_path,
        max_commits=max_commits
    )

    try:
        # 禁用SSL警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        simulator.run()
        print("\n\n✅ Git 提交任务执行完成！")
    except KeyboardInterrupt:
        print("\n\n⚠️  收到中断信号，正在停止...")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*50)
    print("按 Enter 键返回主菜单...")
    input()
    print("="*50)


def generate_template():
    """生成配置文件模板"""
    print("\n" + "="*50)
    print("📝 生成配置文件模板")
    print("="*50)
    
    template = """# CodeFree 账号配置文件
# 格式: invoker_id,session_id
# 每行一个账号，使用逗号分隔
# 以 # 开头的行为注释

# 示例 1
186812,488eb840-c068-4c75-9df3-a3XXXXX

# 示例 2
# 123456,abcdef12-3456-7890-abcd-efghijklmnop

# 添加更多账号...
"""
    
    filename = input("请输入文件名 (默认: accounts.txt): ").strip()
    if not filename:
        filename = "accounts.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"✅ 配置文件模板已生成: {filename}")
        print(f"📝 请编辑 {filename} 文件，填入你的账号信息")
        print(f"💡 可以使用半自动模式 (选项 1) 获取凭证后手动添加到文件中")
    except Exception as e:
        print(f"❌ 生成文件失败: {e}")


async def assisted_programming_mode():
    """辅助编程模式 - 子菜单处理"""
    while True:
        try:
            choice = print_assisted_programming_menu()

            if choice == '1':
                await semi_auto_mode()
                return
            elif choice == '2':
                await manual_mode()
                return
            elif choice == '3':
                await batch_mode()
                return
            elif choice == '4':
                generate_template()
                print()
            elif choice == '5':
                # 返回上级菜单
                return
            else:
                print("❌ 无效选项，请重新选择\n")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            return


async def main():
    """主函数"""
    print_banner()

    while True:
        try:
            # 显示当前凭证状态
            if credential_manager.has_credentials():
                print(f"\n💾 当前会话凭证: Invoker ID = {credential_manager.invoker_id}")

            choice = print_menu()

            if choice == '1':
                await assisted_programming_mode()
                # 任务完成后继续循环，返回主菜单
            elif choice == '2':
                await git_commit_mode()
                # 任务完成后继续循环，返回主菜单
            elif choice == '3':
                print("\n👋 再见!")
                sys.exit(0)
            else:
                print("❌ 无效选项，请重新选择\n")
        except KeyboardInterrupt:
            print("\n\n⚠️  检测到 Ctrl+C")
            confirm = input("是否退出程序? (y/n): ").strip().lower()
            if confirm == 'y':
                print("\n👋 再见!")
                sys.exit(0)
            else:
                print("\n继续运行...\n")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            print("\n按任意键返回主菜单...")
            input()


if __name__ == "__main__":
    try:
        # 检查依赖
        try:
            import playwright
        except ImportError:
            print("❌ 缺少依赖: playwright")
            print("请运行以下命令安装:")
            print("  pip install playwright")
            print("  playwright install chromium")
            sys.exit(1)
        
        # 运行主程序
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
