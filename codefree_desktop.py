#!/usr/bin/env python3
"""
CodeFree Desktop Application - 最终优化版
性能优化 + 响应式布局
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import sys
import os

# 导入核心逻辑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from websocket_simulator2_0 import (
    CredentialManager,
    SemiAutoLoginManager,
    CodeFreeSimulator,
    GitCommitSimulator,
    SimulatorManager,
    credential_manager
)

# 配色
COLORS = {
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'success': '#16A34A',
    'danger': '#DC2626',
    'bg': '#F8FAFC',
    'bg_secondary': '#FFFFFF',
    'text': '#0F172A',
    'text_secondary': '#64748B',
    'border': '#E2E8F0',
    'sidebar': '#FFFFFF',
    'sidebar_border': '#CBD5F5',
    'nav_hover': '#EEF2FF',
    'nav_active': '#E0E7FF',
    'console_bg': '#0F172A',
    'console_text': '#E2E8F0',
}


class CodeFreeDesktop:
    """CodeFree 桌面应用 - 性能优化版"""

    def __init__(self, root):
        self.root = root
        self.root.title("CodeFree Desktop")

        # 自适应窗口
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        window_width = max(window_width, 1200)
        window_height = max(window_height, 700)

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 700)

        self.root.config(bg=COLORS['bg'])
        self.is_running = False
        self.current_page = 'coding'

        # 共享凭证变量
        self.invoker_var = tk.StringVar(value=credential_manager.invoker_id or "")
        self.session_var = tk.StringVar(value=credential_manager.session_id or "")

        # 配置样式
        self.setup_styles()
        self.create_ui()
        self.show_welcome()

    def setup_styles(self):
        """配置 ttk 样式 - 使用 ttk 而非 Canvas 提升性能"""
        style = ttk.Style()

        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure('.', font=('Helvetica', 10), foreground=COLORS['text'])
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['text'])
        style.configure('Card.TFrame', background=COLORS['bg_secondary'])

        button_padding = (18, 9)
        style.configure('Primary.TButton',
                        background=COLORS['primary'],
                        foreground='white',
                        borderwidth=0,
                        focusthickness=0,
                        focuscolor='',
                        font=('Helvetica', 11, 'bold'),
                        padding=button_padding)

        style.map('Primary.TButton',
                  background=[('active', COLORS['primary_hover']),
                              ('disabled', '#93C5FD')],
                  foreground=[('disabled', COLORS['console_text'])])

        style.configure('Success.TButton',
                        background=COLORS['success'],
                        foreground='white',
                        borderwidth=0,
                        focusthickness=0,
                        focuscolor='',
                        font=('Helvetica', 11, 'bold'),
                        padding=button_padding)

        style.map('Success.TButton',
                  background=[('active', '#15803D'),
                              ('disabled', '#86EFAC')],
                  foreground=[('disabled', COLORS['console_text'])])

        style.configure('Danger.TButton',
                        background=COLORS['danger'],
                        foreground='white',
                        borderwidth=0,
                        focusthickness=0,
                        focuscolor='',
                        font=('Helvetica', 10, 'bold'),
                        padding=(16, 8))

        style.map('Danger.TButton',
                  background=[('active', '#B91C1C'),
                              ('disabled', '#FCA5A5')],
                  foreground=[('disabled', COLORS['console_text'])])

        style.configure('Modern.TEntry',
                        fieldbackground=COLORS['bg_secondary'],
                        background=COLORS['bg_secondary'],
                        foreground=COLORS['text'],
                        bordercolor=COLORS['border'],
                        lightcolor=COLORS['border'],
                        darkcolor=COLORS['border'],
                        padding=(10, 6))

        style.map('Modern.TEntry',
                  bordercolor=[('focus', COLORS['primary'])],
                  lightcolor=[('focus', COLORS['primary'])],
                  darkcolor=[('focus', COLORS['primary'])])

        style.configure('Modern.TRadiobutton',
                        background=COLORS['bg_secondary'],
                        foreground=COLORS['text'],
                        font=('Helvetica', 10))

        style.map('Modern.TRadiobutton',
                  background=[('active', COLORS['bg_secondary'])],
                  foreground=[('disabled', COLORS['text_secondary'])])

    def create_ui(self):
        """创建 UI"""
        main = tk.Frame(self.root, bg=COLORS['bg'])
        main.pack(fill=tk.BOTH, expand=True)

        # 配置 grid 权重实现响应式
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=0, minsize=240)  # 侧边栏固定
        main.grid_columnconfigure(1, weight=1)  # 内容区自适应
        main.grid_columnconfigure(2, weight=0, minsize=460)  # 控制台固定

        # 左侧边栏
        self.create_sidebar(main)

        # 中间内容区（自适应）
        self.content_area = tk.Frame(main, bg=COLORS['bg'])
        self.content_area.grid(row=0, column=1, sticky='nsew', padx=(0, 0))

        # 右侧控制台
        self.create_console_panel(main)

        # 创建页面
        self.pages = {}
        self.create_coding_page()
        self.create_git_page()
        self.create_about_page()

        self.show_page('coding')

    def create_sidebar(self, parent):
        """侧边栏"""
        sidebar = tk.Frame(
            parent,
            bg=COLORS['sidebar'],
            width=220,
            highlightbackground=COLORS['sidebar_border'],
            highlightthickness=1,
            bd=0
        )
        sidebar.grid(row=0, column=0, sticky='nsew')
        sidebar.grid_propagate(False)

        # Logo
        logo_frame = tk.Frame(sidebar, bg=COLORS['sidebar'], height=88)
        logo_frame.pack(fill=tk.X, padx=20)
        logo_frame.pack_propagate(False)

        tk.Label(logo_frame, text="CodeFree", font=('Helvetica', 20, 'bold'),
                 bg=COLORS['sidebar'], fg=COLORS['primary']).pack(anchor='w', pady=(24, 0))
        tk.Label(logo_frame, text="Desktop Companion", font=('Helvetica', 10),
                 bg=COLORS['sidebar'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(4, 0))

        tk.Frame(sidebar, bg=COLORS['border'], height=1).pack(fill=tk.X, padx=20, pady=16)

        # 导航
        self.nav_items = []
        for page_id, text, icon in [
            ('coding', '辅助编程', '🤖'),
            ('git', 'Git 提交', '📦'),
            ('about', '关于', 'ℹ️'),
        ]:
            self.create_nav_item(sidebar, page_id, text, icon)

        # 状态
        tk.Frame(sidebar, bg=COLORS['border'], height=1).pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(10, 12))

        status_frame = tk.Frame(sidebar, bg=COLORS['sidebar'])
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15)

        self.status_indicator = tk.Label(status_frame, text="●", font=('Helvetica', 10),
                                         bg=COLORS['sidebar'], fg=COLORS['success'])
        self.status_indicator.pack(side=tk.LEFT, padx=(20, 6))

        self.status_label = tk.Label(status_frame, text="就绪", font=('Helvetica', 9),
                                     bg=COLORS['sidebar'], fg=COLORS['text_secondary'])
        self.status_label.pack(side=tk.LEFT)

    def create_nav_item(self, parent, page_id, text, icon):
        """导航项 - 使用简单的 Frame 而非 Canvas"""
        frame = tk.Frame(parent, bg=COLORS['sidebar'])
        frame.pack(fill=tk.X, padx=20, pady=3)

        indicator = tk.Frame(frame, bg=COLORS['sidebar_border'], width=3)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        content = tk.Frame(frame, bg=COLORS['sidebar'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

        item = tk.Frame(content, bg=COLORS['sidebar'], padx=14, pady=10)
        item.pack(fill=tk.X)

        icon_label = tk.Label(item, text=icon, font=('Helvetica', 14),
                              bg=COLORS['sidebar'], fg=COLORS['text_secondary'])
        icon_label.pack(side=tk.LEFT)

        label = tk.Label(item, text=text, font=('Helvetica', 11),
                         bg=COLORS['sidebar'], fg=COLORS['text'])
        label.pack(side=tk.LEFT, padx=(10, 0))

        bg_widgets = [frame, content, item, icon_label, label]

        def set_background(color):
            for widget in bg_widgets:
                widget.config(bg=color)

        frame.set_background = set_background

        # 简化的点击事件
        def on_click(e=None):
            self.show_page(page_id)

        def on_enter(e=None):
            if self.current_page != page_id:
                set_background(COLORS['nav_hover'])

        def on_leave(e=None):
            target = COLORS['nav_active'] if self.current_page == page_id else COLORS['sidebar']
            set_background(target)

        for w in [frame, content, item, label, icon_label]:
            w.bind('<Button-1>', on_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)

        for w in [frame, content, item, label, icon_label]:
            w.configure(cursor='hand2')

        frame.indicator = indicator
        frame.label = label
        frame.icon_label = icon_label
        frame.page_id = page_id
        frame.bg_widgets = bg_widgets
        frame.set_background(COLORS['sidebar'])
        self.nav_items.append(frame)

    def create_console_panel(self, parent):
        """控制台面板"""
        console_panel = tk.Frame(parent, bg=COLORS['bg'])
        console_panel.grid(row=0, column=2, sticky='ns')

        wrapper = tk.Frame(console_panel, bg=COLORS['bg'])
        wrapper.pack(fill=tk.BOTH, expand=True, padx=(20, 24), pady=20)

        console_card = tk.Frame(
            wrapper,
            bg=COLORS['bg_secondary'],
            highlightbackground=COLORS['border'],
            highlightthickness=1,
            bd=0
        )
        console_card.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(console_card, bg=COLORS['bg_secondary'])
        header.pack(fill=tk.X, padx=18, pady=(18, 0))

        tk.Label(header, text="控制台输出", font=('Helvetica', 13, 'bold'),
                 bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(header, text="实时查看运行状态与日志", font=('Helvetica', 9),
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(6, 0))

        tk.Frame(console_card, bg=COLORS['border'], height=1).pack(fill=tk.X, padx=18, pady=(16, 0))

        console_frame = tk.Frame(console_card, bg=COLORS['bg_secondary'])
        console_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(16, 18))

        self.console = scrolledtext.ScrolledText(
            console_frame,
            font=('Menlo', 10),
            bg=COLORS['console_bg'],
            fg=COLORS['console_text'],
            insertbackground=COLORS['console_text'],
            relief=tk.FLAT,
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0,
            padx=14,
            pady=14
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        # 重定向输出
        sys.stdout = self.ConsoleRedirect(self.console)

        # 清空按钮
        btn_frame = tk.Frame(console_card, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, padx=18, pady=(0, 18))

        ttk.Button(btn_frame, text="清空", command=self.clear_console,
                  style='Danger.TButton', width=10).pack(anchor='e')

    def show_page(self, page_id):
        """切换页面"""
        self.current_page = page_id

        # 隐藏所有页面
        for pid, page in self.pages.items():
            page.pack_forget()

        # 显示目标页面
        if page_id in self.pages:
            self.pages[page_id].pack(fill=tk.BOTH, expand=True)

        # 更新导航样式
        for item in self.nav_items:
            if item.page_id == page_id:
                item.indicator.config(bg=COLORS['primary'])
                item.label.config(fg=COLORS['primary'], font=('Helvetica', 11, 'bold'))
                item.icon_label.config(fg=COLORS['primary'])
                item.set_background(COLORS['nav_active'])
            else:
                item.indicator.config(bg=COLORS['sidebar_border'])
                item.label.config(fg=COLORS['text'], font=('Helvetica', 11))
                item.icon_label.config(fg=COLORS['text_secondary'])
                item.set_background(COLORS['sidebar'])

    def create_coding_page(self):
        """辅助编程页面 - 响应式布局"""
        page = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.pages['coding'] = page

        # 使用 grid 布局实现响应式
        page.grid_rowconfigure(0, weight=0)  # 标题
        page.grid_rowconfigure(1, weight=1)  # 内容
        page.grid_columnconfigure(0, weight=1)

        # 标题
        header = tk.Frame(page, bg=COLORS['bg'])
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 10))

        tk.Label(header, text="辅助编程", font=('Helvetica', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(header, text="连接云端模拟器，批量完成补全与注释任务",
                 font=('Helvetica', 10), bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(6, 0))

        # 内容容器
        container = tk.Frame(page, bg=COLORS['bg'])
        container.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 20))

        # 配置容器的响应式
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=0)
        container.grid_columnconfigure(0, weight=1)

        # 卡片1: 凭证
        card1 = self.create_card(container, "凭证设置")
        card1.grid(row=0, column=0, sticky='ew', pady=(0, 15))

        # 半自动登录
        ttk.Button(card1.body, text="半自动登录", command=self.semi_auto_login,
                  style='Success.TButton').pack(pady=(0, 18), anchor='w')

        self.render_credentials_inputs(card1.body)

        # 卡片2: 配置
        card2 = self.create_card(container, "运行配置")
        card2.grid(row=1, column=0, sticky='ew')

        # 运行模式
        tk.Label(card2.body, text="运行模式", font=('Helvetica', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 6))

        mode_frame = tk.Frame(card2.body, bg=COLORS['bg_secondary'])
        mode_frame.pack(fill=tk.X, pady=(0, 12))

        self.mode_var = tk.StringVar(value="completion")
        self.max_tasks_var = tk.StringVar(value="2000")

        for value, text in [('completion', '代码补全'), ('comment', '代码注释')]:
            ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var,
                           value=value, style='Modern.TRadiobutton',
                           command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 18))

        # 任务次数
        tk.Label(card2.body, text="任务次数", font=('Helvetica', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))

        tk.Label(card2.body, text="代码补全最大 2000，代码注释最大 20",
                font=('Helvetica', 8), bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))

        self.max_tasks_entry = ttk.Entry(card2.body, style='Modern.TEntry',
                                         font=('Helvetica', 10), textvariable=self.max_tasks_var)
        self.max_tasks_entry.pack(fill=tk.X, pady=(0, 15), ipady=6)

        # 控制按钮
        btn_frame = tk.Frame(card2.body, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, pady=(16, 0))

        self.start_coding_btn = ttk.Button(btn_frame, text="开始运行",
                                          command=self.start_coding,
                                          style='Primary.TButton', width=15)
        self.start_coding_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_coding_btn = ttk.Button(btn_frame, text="停止",
                                         command=self.stop_task,
                                         style='Danger.TButton', width=10,
                                         state=tk.DISABLED)
        self.stop_coding_btn.pack(side=tk.LEFT)

    def create_git_page(self):
        """Git 页面"""
        page = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.pages['git'] = page

        page.grid_rowconfigure(0, weight=0)
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        # 标题
        header = tk.Frame(page, bg=COLORS['bg'])
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 10))

        tk.Label(header, text="Git 提交", font=('Helvetica', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(header, text="一键配置仓库信息，模拟批量提交",
                 font=('Helvetica', 10), bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(6, 0))

        # 内容
        container = tk.Frame(page, bg=COLORS['bg'])
        container.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 20))
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=0)
        container.grid_columnconfigure(0, weight=1)

        # 凭证卡片
        card1 = self.create_card(container, "凭证设置")
        card1.grid(row=0, column=0, sticky='ew', pady=(0, 15))

        ttk.Button(card1.body, text="半自动登录（Git 模式）",
                  command=self.semi_auto_login_git,
                  style='Success.TButton').pack(pady=14, anchor='w')

        self.render_credentials_inputs(card1.body)

        # Git 参数卡片
        card2 = self.create_card(container, "仓库参数")
        card2.grid(row=1, column=0, sticky='ew')

        fields = [
            ("项目 ID", "project_id_entry", ""),
            ("仓库 ID", "repository_id_entry", ""),
            ("文件路径", "file_path_entry", "README.md"),
            ("提交次数", "max_commits_entry", "8"),
        ]

        for label, attr, default in fields:
            tk.Label(card2.body, text=label, font=('Helvetica', 9),
                    bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
            entry = ttk.Entry(card2.body, style='Modern.TEntry', font=('Helvetica', 10))
            entry.pack(fill=tk.X, pady=(0, 12), ipady=6)
            if default:
                entry.insert(0, default)
            setattr(self, attr, entry)

        # 按钮
        btn_frame = tk.Frame(card2.body, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, pady=(16, 0))

        self.start_git_btn = ttk.Button(btn_frame, text="开始提交",
                                       command=self.start_git,
                                       style='Primary.TButton', width=15)
        self.start_git_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_git_btn = ttk.Button(btn_frame, text="停止",
                                      command=self.stop_task,
                                      style='Danger.TButton', width=10,
                                      state=tk.DISABLED)
        self.stop_git_btn.pack(side=tk.LEFT)

    def create_about_page(self):
        """关于页面"""
        page = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.pages['about'] = page

        page.grid_rowconfigure(0, weight=0)
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        header = tk.Frame(page, bg=COLORS['bg'])
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 10))

        tk.Label(header, text="关于", font=('Helvetica', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(header, text="了解 CodeFree Desktop 的版本与特性",
                 font=('Helvetica', 10), bg=COLORS['bg'],
                 fg=COLORS['text_secondary']).pack(anchor='w', pady=(6, 0))

        container = tk.Frame(page, bg=COLORS['bg'])
        container.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 20))
        container.grid_columnconfigure(0, weight=1)

        card = self.create_card(container, "CodeFree Desktop v1.0")
        card.grid(row=0, column=0, sticky='ew')

        info = """研发云编程助手 - 桌面版

功能特性:
• 半自动登录，自动提取凭证
• 代码补全模拟（最大 2000 次）
• 代码注释生成（最大 20 次）
• Git 提交模拟
• 跨平台支持（Mac & Windows）

使用说明:
1. 左侧菜单选择功能
2. 使用"半自动登录"获取凭证
3. 配置参数后开始运行
4. 右侧控制台查看日志

版权所有 © 2025"""

        tk.Label(card.body, text=info, justify=tk.LEFT, font=('Helvetica', 10),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(pady=10)

    def create_card(self, parent, title):
        """创建卡片"""
        card_frame = tk.Frame(
            parent,
            bg=COLORS['bg_secondary'],
            bd=0,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border'],
            highlightthickness=1
        )

        header = tk.Frame(card_frame, bg=COLORS['bg_secondary'])
        header.pack(fill=tk.X, padx=20, pady=(18, 0))

        tk.Label(header, text=title, font=('Helvetica', 12, 'bold'),
                 bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(anchor='w')

        tk.Frame(card_frame, bg=COLORS['border'], height=1).pack(fill=tk.X, padx=20, pady=(14, 0))

        body = tk.Frame(card_frame, bg=COLORS['bg_secondary'])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(14, 20))

        # 将 body 存储为 card_frame 的属性，方便访问
        card_frame.body = body
        return card_frame

    def render_credentials_inputs(self, parent, intro_text="或手动输入凭证"):
        """渲染共享凭证输入区"""
        tk.Label(parent, text=intro_text, font=('Helvetica', 10),
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 12))

        tk.Label(parent, text="Invoker ID", font=('Helvetica', 9),
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
        ttk.Entry(parent, style='Modern.TEntry', font=('Helvetica', 10),
                  textvariable=self.invoker_var).pack(fill=tk.X, pady=(0, 12), ipady=6)

        tk.Label(parent, text="Session ID", font=('Helvetica', 9),
                 bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
        ttk.Entry(parent, style='Modern.TEntry', font=('Helvetica', 10),
                  textvariable=self.session_var).pack(fill=tk.X, pady=(0, 12), ipady=6)

        ttk.Button(parent, text="保存凭证", command=self.save_credentials,
                   style='Primary.TButton', width=12).pack(anchor='w')

    def clear_console(self):
        self.console.delete(1.0, tk.END)
        print("控制台已清空\n")

    def show_welcome(self):
        print("="*50)
        print("CodeFree Desktop v1.0")
        print("="*50)
        print("\n欢迎使用！\n")

    def update_status(self, text, is_running=False):
        self.status_label.config(text=text)
        color = '#F59E0B' if is_running else COLORS['success']
        self.status_indicator.config(fg=color)

    def semi_auto_login(self):
        print("\n启动半自动登录...\n")

        def login_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            manager = SemiAutoLoginManager()
            result = loop.run_until_complete(manager.semi_auto_login())

            if result:
                invoker_id, session_id, _ = result
                self.root.after(0, lambda: self.invoker_var.set(invoker_id))
                self.root.after(0, lambda: self.session_var.set(session_id))
                credential_manager.set_credentials(invoker_id, session_id)
                self.root.after(0, lambda: messagebox.showinfo("成功", "凭证已自动提取！"))
            else:
                self.root.after(0, lambda: messagebox.showerror("失败", "未能获取凭证"))

            loop.close()

        threading.Thread(target=login_task, daemon=True).start()

    def semi_auto_login_git(self):
        print("\n启动半自动登录（Git 模式）...\n")

        def login_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            manager = SemiAutoLoginManager()
            result = loop.run_until_complete(manager.semi_auto_login(keep_open=True))

            if result:
                invoker_id, session_id, git_params = result
                if git_params:
                    if git_params.get('project_id'):
                        self.root.after(0, lambda: self.project_id_entry.delete(0, tk.END))
                        self.root.after(0, lambda: self.project_id_entry.insert(0, git_params['project_id']))
                    if git_params.get('repository_id'):
                        self.root.after(0, lambda: self.repository_id_entry.delete(0, tk.END))
                        self.root.after(0, lambda: self.repository_id_entry.insert(0, git_params['repository_id']))
                self.root.after(0, lambda: self.invoker_var.set(invoker_id))
                self.root.after(0, lambda: self.session_var.set(session_id))
                credential_manager.set_credentials(invoker_id, session_id)
                if git_params:
                    credential_manager.set_git_params(git_params.get('project_id'), git_params.get('repository_id'))
                self.root.after(0, lambda: messagebox.showinfo("成功", "凭证已自动提取！"))
            else:
                self.root.after(0, lambda: messagebox.showerror("失败", "未能获取凭证"))

            loop.close()

        threading.Thread(target=login_task, daemon=True).start()

    def on_mode_change(self):
        mode = self.mode_var.get()
        if mode == 'comment':
            self.max_tasks_var.set("10")
        elif mode == 'completion' and self.max_tasks_var.get().strip() in ("", "10"):
            self.max_tasks_var.set("2000")

    def save_credentials(self):
        invoker_id = self.invoker_var.get().strip()
        session_id = self.session_var.get().strip()

        if not invoker_id or not session_id:
            messagebox.showerror("错误", "请填写凭证")
            return

        self.invoker_var.set(invoker_id)
        self.session_var.set(session_id)
        credential_manager.set_credentials(invoker_id, session_id)
        messagebox.showinfo("成功", "凭证已保存")

    def start_coding(self):
        if self.is_running:
            return

        invoker_id = self.invoker_var.get().strip()
        session_id = self.session_var.get().strip()

        if not invoker_id or not session_id:
            messagebox.showerror("错误", "请先设置凭证")
            return

        mode = self.mode_var.get()

        try:
            max_tasks = int(self.max_tasks_var.get().strip())
        except ValueError:
            messagebox.showerror("错误", "任务次数必须是数字")
            return

        if mode == 'comment' and max_tasks > 20:
            messagebox.showwarning("警告", "代码注释最大 20")
            max_tasks = 20
            self.max_tasks_var.set("20")
        elif mode == 'completion' and max_tasks > 2000:
            messagebox.showwarning("警告", "代码补全最大 2000")
            max_tasks = 2000

        self.is_running = True
        self.start_coding_btn.config(state=tk.DISABLED)
        self.stop_coding_btn.config(state=tk.NORMAL)
        self.update_status("运行中", True)

        print(f"\n开始运行 - {mode} - {max_tasks}次\n")

        def run_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            manager = SimulatorManager()

            try:
                loop.run_until_complete(
                    manager.run_simulator(invoker_id, session_id, max_tasks, True, mode, "src")
                )
                print("\n✅ 完成\n")
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")
            finally:
                loop.close()
                self.root.after(0, self.task_completed)

        threading.Thread(target=run_task, daemon=True).start()

    def start_git(self):
        if self.is_running:
            return

        project_id = self.project_id_entry.get().strip()
        repository_id = self.repository_id_entry.get().strip()
        file_path = self.file_path_entry.get().strip()

        if not project_id or not repository_id:
            messagebox.showerror("错误", "请填写仓库参数")
            return

        try:
            max_commits = int(self.max_commits_entry.get().strip())
        except ValueError:
            messagebox.showerror("错误", "次数必须是数字")
            return

        self.is_running = True
        self.start_git_btn.config(state=tk.DISABLED)
        self.stop_git_btn.config(state=tk.NORMAL)
        self.update_status("运行中", True)

        print(f"\n开始 Git 提交\n")

        def run_task():
            simulator = GitCommitSimulator(
                invoker_id=credential_manager.invoker_id,
                session_id=credential_manager.session_id,
                project_id=project_id,
                repository_id=repository_id,
                file_path=file_path,
                max_commits=max_commits
            )

            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                simulator.run()
                print("\n✅ 完成\n")
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")
            finally:
                self.root.after(0, self.task_completed)

        threading.Thread(target=run_task, daemon=True).start()

    def stop_task(self):
        print("\n⚠️  停止\n")
        self.task_completed()

    def task_completed(self):
        self.is_running = False
        self.start_coding_btn.config(state=tk.NORMAL)
        self.stop_coding_btn.config(state=tk.DISABLED)
        self.start_git_btn.config(state=tk.NORMAL)
        self.stop_git_btn.config(state=tk.DISABLED)
        self.update_status("就绪", False)

    class ConsoleRedirect:
        def __init__(self, text_widget):
            self.widget = text_widget

        def write(self, string):
            try:
                self.widget.insert(tk.END, string)
                self.widget.see(tk.END)
                self.widget.update_idletasks()
            except:
                pass

        def flush(self):
            pass


def main():
    root = tk.Tk()
    app = CodeFreeDesktop(root)

    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "任务运行中，确定退出？"):
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
