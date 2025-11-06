#!/usr/bin/env python3
"""
CodeFree Desktop Application - Final Modern UI
最终优化版：三栏布局，更紧凑的设计
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
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


# 现代化配色方案
COLORS = {
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'success': '#10B981',
    'success_hover': '#059669',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'bg': '#F9FAFB',
    'bg_secondary': '#FFFFFF',
    'text': '#1F2937',
    'text_secondary': '#6B7280',
    'border': '#E5E7EB',
    'input_bg': '#FFFFFF',
    'sidebar': '#F3F4F6',
}

# 圆角半径
RADIUS = 8


class ModernButton(tk.Canvas):
    """现代化圆角按钮"""
    def __init__(self, parent, text, command, bg=COLORS['primary'],
                 fg='white', width=120, height=36, hover_bg=None):
        super().__init__(parent, width=width, height=height,
                        bg=parent['bg'], highlightthickness=0)

        self.command = command
        self.text = text
        self.default_bg = bg
        self.hover_bg = hover_bg if hover_bg else COLORS['primary_hover']
        self.fg = fg
        self.width = width
        self.height = height

        self.rect = self.create_rounded_rect(0, 0, width, height, radius=RADIUS, fill=bg)
        self.text_id = self.create_text(width/2, height/2, text=text,
                                       fill=fg, font=('Helvetica', 10, 'bold'))

        self.bind('<Button-1>', lambda e: self.command())
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def create_rounded_rect(self, x1, y1, x2, y2, radius=8, **kwargs):
        points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
                 x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
                 x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, e):
        self.itemconfig(self.rect, fill=self.hover_bg)

    def on_leave(self, e):
        self.itemconfig(self.rect, fill=self.default_bg)

    def set_state(self, state):
        if state == 'disabled':
            self.itemconfig(self.rect, fill='#D1D5DB')
            self.unbind('<Button-1>')
            self.unbind('<Enter>')
            self.unbind('<Leave>')
        else:
            self.itemconfig(self.rect, fill=self.default_bg)
            self.bind('<Button-1>', lambda e: self.command())
            self.bind('<Enter>', self.on_enter)
            self.bind('<Leave>', self.on_leave)


class ModernEntry(tk.Frame):
    """现代化圆角输入框"""
    def __init__(self, parent, placeholder='', **kwargs):
        super().__init__(parent, bg=COLORS['border'], bd=0, relief=tk.FLAT)

        # 创建圆角效果的容器
        inner = tk.Frame(self, bg=COLORS['input_bg'])
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.entry = tk.Entry(inner,
                            font=('Helvetica', 10),
                            bg=COLORS['input_bg'],
                            fg=COLORS['text'],
                            relief=tk.FLAT,
                            insertbackground=COLORS['primary'],
                            bd=0,
                            **kwargs)
        self.entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        if placeholder:
            self.placeholder = placeholder
            self.entry.insert(0, placeholder)
            self.entry.config(fg=COLORS['text_secondary'])
            self.entry.bind('<FocusIn>', self.on_focus_in)
            self.entry.bind('<FocusOut>', self.on_focus_out)

    def on_focus_in(self, e):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=COLORS['text'])

    def on_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=COLORS['text_secondary'])

    def get(self):
        val = self.entry.get()
        return '' if val == getattr(self, 'placeholder', '') else val

    def delete(self, first, last):
        self.entry.delete(first, last)

    def insert(self, index, string):
        self.entry.insert(index, string)


class CodeFreeApp:
    """现代化三栏布局主应用"""

    def __init__(self, root):
        self.root = root
        self.root.title("CodeFree Desktop")

        # 设置窗口 - 自适应屏幕大小
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # 使用屏幕的 85% 大小
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)

        # 确保最小尺寸
        window_width = max(window_width, 1200)
        window_height = max(window_height, 700)

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 700)

        self.root.config(bg=COLORS['bg'])
        self.is_running = False
        self.current_page = 'coding'

        self.create_ui()
        self.show_welcome()

    def create_ui(self):
        """创建三栏布局UI"""

        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)

        # 左侧边栏 (200px)
        self.create_sidebar(main_container)

        # 中间内容区 (自适应)
        self.content_area = tk.Frame(main_container, bg=COLORS['bg'])
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧控制台 (固定 400px)
        self.create_console_panel(main_container)

        # 创建页面
        self.pages = {}
        self.create_coding_page()
        self.create_git_page()
        self.create_about_page()

        self.show_page('coding')

    def create_sidebar(self, parent):
        """创建侧边栏"""
        sidebar = tk.Frame(parent, bg=COLORS['sidebar'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(sidebar, bg=COLORS['sidebar'], height=70)
        logo_frame.pack(fill=tk.X)
        logo_frame.pack_propagate(False)

        tk.Label(logo_frame, text="CodeFree", font=('Helvetica', 18, 'bold'),
                bg=COLORS['sidebar'], fg=COLORS['primary']).pack(pady=(20, 0))
        tk.Label(logo_frame, text="Desktop", font=('Helvetica', 10),
                bg=COLORS['sidebar'], fg=COLORS['text_secondary']).pack()

        tk.Frame(sidebar, bg=COLORS['border'], height=1).pack(fill=tk.X, pady=12)

        # 导航
        self.nav_items = []
        nav_items = [
            ('coding', '辅助编程', '🤖'),
            ('git', 'Git 提交', '📦'),
            ('about', '关于', 'ℹ️'),
        ]

        for page_id, text, icon in nav_items:
            self.create_nav_item(sidebar, page_id, text, icon)

        # 底部状态
        status_frame = tk.Frame(sidebar, bg=COLORS['sidebar'])
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15)

        self.status_indicator = tk.Canvas(status_frame, width=8, height=8,
                                         bg=COLORS['sidebar'], highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(15, 6))
        self.status_circle = self.status_indicator.create_oval(1, 1, 7, 7,
                                                               fill=COLORS['success'], outline='')

        self.status_label = tk.Label(status_frame, text="就绪", font=('Helvetica', 9),
                                     bg=COLORS['sidebar'], fg=COLORS['text_secondary'])
        self.status_label.pack(side=tk.LEFT)

    def create_nav_item(self, parent, page_id, text, icon):
        """创建导航项 - 移除 cursor='hand2'"""
        frame = tk.Frame(parent, bg=COLORS['sidebar'])
        frame.pack(fill=tk.X, padx=12, pady=2)

        indicator = tk.Frame(frame, bg=COLORS['sidebar'], width=3)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        content = tk.Frame(frame, bg=COLORS['sidebar'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        item_container = tk.Frame(content, bg=COLORS['sidebar'])
        item_container.pack(fill=tk.X, pady=8)

        tk.Label(item_container, text=icon, font=('Helvetica', 14),
                bg=COLORS['sidebar']).pack(side=tk.LEFT, padx=(6, 8))

        label = tk.Label(item_container, text=text, font=('Helvetica', 11),
                        bg=COLORS['sidebar'], fg=COLORS['text'])
        label.pack(side=tk.LEFT)

        def on_click(e=None):
            self.show_page(page_id)

        for widget in [frame, content, item_container, label]:
            widget.bind('<Button-1>', on_click)

        frame.indicator = indicator
        frame.label = label
        frame.page_id = page_id
        self.nav_items.append(frame)

    def create_console_panel(self, parent):
        """创建右侧控制台面板"""
        console_panel = tk.Frame(parent, bg=COLORS['bg_secondary'], width=500)
        console_panel.pack(side=tk.RIGHT, fill=tk.Y)
        console_panel.pack_propagate(False)

        # 标题
        header = tk.Frame(console_panel, bg=COLORS['bg_secondary'], height=50)
        header.pack(fill=tk.X, padx=15, pady=(15, 0))
        header.pack_propagate(False)

        tk.Label(header, text="控制台输出", font=('Helvetica', 13, 'bold'),
                bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(anchor='w')

        # 控制台
        console_container = tk.Frame(console_panel, bg=COLORS['bg_secondary'])
        console_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.console = scrolledtext.ScrolledText(
            console_container,
            font=('Monaco', 9),
            bg='#1E1E1E',
            fg='#D4D4D4',
            insertbackground='#FFFFFF',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        # 重定向输出
        sys.stdout = self.ConsoleRedirect(self.console)

        # 清空按钮
        btn_frame = tk.Frame(console_panel, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ModernButton(btn_frame, "清空", self.clear_console,
                    bg=COLORS['text_secondary'], width=80, height=32).pack(anchor='w')

    def show_page(self, page_id):
        """显示页面"""
        self.current_page = page_id

        for pid, page in self.pages.items():
            page.pack_forget()

        if page_id in self.pages:
            self.pages[page_id].pack(fill=tk.BOTH, expand=True)

        for item in self.nav_items:
            if item.page_id == page_id:
                item.indicator.config(bg=COLORS['primary'])
                item.label.config(fg=COLORS['primary'], font=('Helvetica', 11, 'bold'))
            else:
                item.indicator.config(bg=COLORS['sidebar'])
                item.label.config(fg=COLORS['text'], font=('Helvetica', 11))

    def create_coding_page(self):
        """创建辅助编程页面"""
        page = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.pages['coding'] = page

        # 紧凑的标题
        header = tk.Frame(page, bg=COLORS['bg'], height=45)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))
        header.pack_propagate(False)

        tk.Label(header, text="辅助编程", font=('Helvetica', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')

        # 滚动容器
        canvas = tk.Canvas(page, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=COLORS['bg'])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=580)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 凭证卡片
        card1 = self.create_card(scrollable, "凭证设置")

        btn_frame = tk.Frame(card1, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        ModernButton(btn_frame, "半自动登录", self.semi_auto_login,
                    bg=COLORS['success'], hover_bg=COLORS['success_hover'],
                    width=140, height=38).pack(pady=8)

        tk.Label(btn_frame, text="浏览器自动打开，登录后自动提取凭证",
                font=('Helvetica', 9), bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']).pack()

        tk.Frame(card1, bg=COLORS['border'], height=1).pack(fill=tk.X, pady=15)

        tk.Label(card1, text="手动输入", font=('Helvetica', 10, 'bold'),
                bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(anchor='w', pady=(0, 10))

        tk.Label(card1, text="Invoker ID", font=('Helvetica', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
        self.invoker_entry = ModernEntry(card1, width=50)
        self.invoker_entry.pack(fill=tk.X, pady=(0, 12))

        tk.Label(card1, text="Session ID", font=('Helvetica', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
        self.session_entry = ModernEntry(card1, width=50)
        self.session_entry.pack(fill=tk.X, pady=(0, 12))

        ModernButton(card1, "保存", self.save_credentials,
                    bg=COLORS['primary'], width=100, height=34).pack(anchor='w')

        # 配置卡片
        card2 = self.create_card(scrollable, "运行配置")

        tk.Label(card2, text="运行模式", font=('Helvetica', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 6))

        mode_frame = tk.Frame(card2, bg=COLORS['bg_secondary'])
        mode_frame.pack(fill=tk.X, pady=(0, 12))

        self.mode_var = tk.StringVar(value="completion")

        for value, text in [('completion', '代码补全'), ('comment', '代码注释')]:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode_var,
                              value=value, font=('Helvetica', 10),
                              bg=COLORS['bg_secondary'], fg=COLORS['text'],
                              selectcolor=COLORS['bg_secondary'],
                              activebackground=COLORS['bg_secondary'])
            rb.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(card2, text="任务次数", font=('Helvetica', 9),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))

        # 任务次数提示
        hint_frame = tk.Frame(card2, bg=COLORS['bg_secondary'])
        hint_frame.pack(fill=tk.X, pady=(0, 4))

        tk.Label(hint_frame, text="代码补全最大 2000，代码注释最大 20",
                font=('Helvetica', 8), bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']).pack(anchor='w')

        self.max_tasks_entry = ModernEntry(card2, width=30)
        self.max_tasks_entry.pack(fill=tk.X, pady=(0, 15))
        self.max_tasks_entry.insert(0, "2000")

        # 控制按钮
        btn_container = tk.Frame(card2, bg=COLORS['bg_secondary'])
        btn_container.pack(fill=tk.X, pady=(8, 0))

        self.start_coding_btn = ModernButton(btn_container, "开始运行", self.start_coding,
                                            bg=COLORS['primary'], width=110, height=38)
        self.start_coding_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_coding_btn = ModernButton(btn_container, "停止", self.stop_task,
                                           bg=COLORS['danger'], width=80, height=38)
        self.stop_coding_btn.pack(side=tk.LEFT)
        self.stop_coding_btn.set_state('disabled')

        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))
        scrollbar.pack(side="right", fill="y")

    def create_git_page(self):
        """创建 Git 页面"""
        page = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.pages['git'] = page

        header = tk.Frame(page, bg=COLORS['bg'], height=45)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))
        header.pack_propagate(False)

        tk.Label(header, text="Git 提交", font=('Helvetica', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')

        canvas = tk.Canvas(page, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=COLORS['bg'])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=580)
        canvas.configure(yscrollcommand=scrollbar.set)

        card1 = self.create_card(scrollable, "凭证设置")

        ModernButton(card1, "半自动登录（Git 模式）", self.semi_auto_login_git,
                    bg=COLORS['success'], hover_bg=COLORS['success_hover'],
                    width=180, height=38).pack(pady=10)

        card2 = self.create_card(scrollable, "仓库参数")

        fields = [
            ("项目 ID", "project_id_entry", ""),
            ("仓库 ID", "repository_id_entry", ""),
            ("文件路径", "file_path_entry", "README.md"),
            ("提交次数", "max_commits_entry", "8"),
        ]

        for label, attr, default in fields:
            tk.Label(card2, text=label, font=('Helvetica', 9),
                    bg=COLORS['bg_secondary'], fg=COLORS['text_secondary']).pack(anchor='w', pady=(0, 4))
            entry = ModernEntry(card2, width=50)
            entry.pack(fill=tk.X, pady=(0, 12))
            if default:
                entry.insert(0, default)
            setattr(self, attr, entry)

        btn_container = tk.Frame(card2, bg=COLORS['bg_secondary'])
        btn_container.pack(fill=tk.X, pady=(8, 0))

        self.start_git_btn = ModernButton(btn_container, "开始提交", self.start_git,
                                         bg=COLORS['primary'], width=110, height=38)
        self.start_git_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_git_btn = ModernButton(btn_container, "停止", self.stop_task,
                                        bg=COLORS['danger'], width=80, height=38)
        self.stop_git_btn.pack(side=tk.LEFT)
        self.stop_git_btn.set_state('disabled')

        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))
        scrollbar.pack(side="right", fill="y")

    def create_about_page(self):
        """创建关于页面"""
        page = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.pages['about'] = page

        header = tk.Frame(page, bg=COLORS['bg'], height=45)
        header.pack(fill=tk.X, padx=20, pady=(15, 10))
        header.pack_propagate(False)

        tk.Label(header, text="关于", font=('Helvetica', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')

        content = tk.Frame(page, bg=COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        card = self.create_card(content, "CodeFree Desktop v1.0")

        info = """研发云编程助手 - 桌面版

功能特性:
• 半自动登录，自动提取凭证
• 代码补全模拟
• 代码注释生成
• Git 提交模拟
• 跨平台支持（Mac & Windows）

使用说明:
1. 选择左侧菜单切换功能
2. 使用"半自动登录"获取凭证
3. 配置参数后开始运行
4. 在右侧控制台查看日志

版权所有 © 2025"""

        tk.Label(card, text=info, justify=tk.LEFT, font=('Helvetica', 10),
                bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(pady=10)

    def create_card(self, parent, title):
        """创建圆角卡片"""
        # 外层容器（圆角边框效果）
        card_outer = tk.Frame(parent, bg=COLORS['border'])
        card_outer.pack(fill=tk.X, pady=(0, 15))

        # 内层容器
        card = tk.Frame(card_outer, bg=COLORS['bg_secondary'])
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # 标题
        header = tk.Frame(card, bg=COLORS['bg_secondary'])
        header.pack(fill=tk.X, padx=18, pady=(15, 12))

        tk.Label(header, text=title, font=('Helvetica', 12, 'bold'),
                bg=COLORS['bg_secondary'], fg=COLORS['text']).pack(anchor='w')

        # 内容
        body = tk.Frame(card, bg=COLORS['bg_secondary'])
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 15))

        return body

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
        color = COLORS['warning'] if is_running else COLORS['success']
        self.status_indicator.itemconfig(self.status_circle, fill=color)

    def semi_auto_login(self):
        print("\n启动半自动登录...\n")

        def login_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            manager = SemiAutoLoginManager()
            result = loop.run_until_complete(manager.semi_auto_login())

            if result:
                invoker_id, session_id, _ = result
                self.root.after(0, lambda: self.invoker_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.invoker_entry.insert(0, invoker_id))
                self.root.after(0, lambda: self.session_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.session_entry.insert(0, session_id))
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
                credential_manager.set_credentials(invoker_id, session_id)
                if git_params:
                    credential_manager.set_git_params(git_params.get('project_id'), git_params.get('repository_id'))
                self.root.after(0, lambda: messagebox.showinfo("成功", "凭证已自动提取！"))
            else:
                self.root.after(0, lambda: messagebox.showerror("失败", "未能获取凭证"))

            loop.close()

        threading.Thread(target=login_task, daemon=True).start()

    def save_credentials(self):
        invoker_id = self.invoker_entry.get().strip()
        session_id = self.session_entry.get().strip()

        if not invoker_id or not session_id:
            messagebox.showerror("错误", "请填写完整的凭证信息")
            return

        credential_manager.set_credentials(invoker_id, session_id)
        messagebox.showinfo("成功", "凭证已保存")

    def start_coding(self):
        if self.is_running:
            messagebox.showwarning("警告", "任务正在运行中")
            return

        invoker_id = self.invoker_entry.get().strip()
        session_id = self.session_entry.get().strip()

        if not invoker_id or not session_id:
            messagebox.showerror("错误", "请先设置凭证")
            return

        mode = self.mode_var.get()
        src_dir = "src"  # 固定使用 src 目录

        try:
            max_tasks = int(self.max_tasks_entry.get().strip())
        except ValueError:
            messagebox.showerror("错误", "任务次数必须是数字")
            return

        # 根据模式限制任务次数
        if mode == 'comment' and max_tasks > 20:
            messagebox.showwarning("警告", "代码注释模式最大任务次数为 20")
            max_tasks = 20
            self.max_tasks_entry.delete(0, tk.END)
            self.max_tasks_entry.insert(0, "20")
        elif mode == 'completion' and max_tasks > 2000:
            messagebox.showwarning("警告", "代码补全模式最大任务次数为 2000")
            max_tasks = 2000

        self.is_running = True
        self.start_coding_btn.set_state('disabled')
        self.stop_coding_btn.set_state('normal')
        self.update_status("运行中", True)

        print(f"\n{'='*50}")
        print(f"开始运行")
        print(f"{'='*50}")
        print(f"模式: {'代码注释' if mode == 'comment' else '代码补全'}")
        print(f"任务: {max_tasks} 次\n")

        def run_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            manager = SimulatorManager()

            try:
                loop.run_until_complete(
                    manager.run_simulator(invoker_id, session_id, max_tasks, True, mode, src_dir)
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
            messagebox.showwarning("警告", "任务正在运行中")
            return

        project_id = self.project_id_entry.get().strip()
        repository_id = self.repository_id_entry.get().strip()
        file_path = self.file_path_entry.get().strip()

        if not project_id or not repository_id:
            messagebox.showerror("错误", "请填写项目 ID 和仓库 ID")
            return

        try:
            max_commits = int(self.max_commits_entry.get().strip())
        except ValueError:
            messagebox.showerror("错误", "提交次数必须是数字")
            return

        self.is_running = True
        self.start_git_btn.set_state('disabled')
        self.stop_git_btn.set_state('normal')
        self.update_status("运行中", True)

        print(f"\n{'='*50}")
        print(f"开始 Git 提交")
        print(f"{'='*50}\n")

        def run_task():
            invoker_id = credential_manager.invoker_id
            session_id = credential_manager.session_id

            simulator = GitCommitSimulator(
                invoker_id=invoker_id,
                session_id=session_id,
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
        print("\n⚠️  停止中...\n")
        self.task_completed()

    def task_completed(self):
        self.is_running = False
        self.start_coding_btn.set_state('normal')
        self.stop_coding_btn.set_state('disabled')
        self.start_git_btn.set_state('normal')
        self.stop_git_btn.set_state('disabled')
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
    app = CodeFreeApp(root)

    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "任务正在运行，确定退出？"):
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.update()
    root.mainloop()


if __name__ == "__main__":
    main()
