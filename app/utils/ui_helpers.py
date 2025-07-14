#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI辅助函数 - 现代化版本
"""

import tkinter as tk
from tkinter import ttk
import os
import webbrowser
from datetime import datetime


# 现代化颜色方案
MODERN_COLORS = {
    # 主色调
    'primary': '#667eea',           # 现代蓝色
    'primary_dark': '#5a67d8',      # 深蓝色
    'primary_light': '#7c88f0',     # 浅蓝色
    
    # 功能色
    'success': '#48bb78',           # 绿色
    'warning': '#ed8936',           # 橙色
    'danger': '#f56565',            # 红色
    'info': '#4299e1',              # 信息蓝
    
    # 中性色
    'light': '#ffffff',             # 改为白色
    'light_gray': '#ffffff',        # 改为白色
    'gray': '#a0aec0',              # 中灰（保留用于文字颜色）
    'dark_gray': '#4a5568',         # 深灰（保留用于文字颜色）
    'dark': '#2d3748',              # 深色（保留用于文字颜色）
    'white': '#ffffff',             # 白色
    
    # 背景色
    'bg_primary': '#ffffff',        # 主背景 - 纯白色
    'bg_secondary': '#ffffff',      # 卡片背景
    'bg_accent': '#667eea10',       # 轻微彩色背景
    
    # 状态色
    'connected': '#48bb78',         # 连接成功
    'disconnected': '#f56565',      # 断开连接
    'warning_status': '#ed8936',    # 警告状态
}

def setup_modern_styles():
    """设置现代化界面样式"""
    style = ttk.Style()
    
    # 设置主题
    try:
        style.theme_use('alt')
    except:
        pass
    
    # 卡片样式
    style.configure("Card.TFrame",
                   background=MODERN_COLORS['bg_secondary'],
                   relief="solid",
                   borderwidth=1)
    
    # 现代化标签框架
    style.configure("Modern.TLabelFrame",
                   background=MODERN_COLORS['bg_secondary'],
                   borderwidth=1,
                   relief="solid")
    
    # 现代化标签框架的标签
    style.configure("Modern.TLabelFrame.Label",
                   background=MODERN_COLORS['bg_secondary'],
                   font=("Arial", 11, "bold"),
                   foreground=MODERN_COLORS['primary'])
    
    # 现代化标签
    style.configure("Title.TLabel",
                   background=MODERN_COLORS['bg_secondary'],
                   font=("Arial", 14, "bold"),
                   foreground=MODERN_COLORS['dark'])
    
    style.configure("Subtitle.TLabel",
                   background=MODERN_COLORS['bg_secondary'],
                   font=("Arial", 10),
                   foreground=MODERN_COLORS['dark_gray'])
    
    style.configure("Status.TLabel",
                   background=MODERN_COLORS['bg_secondary'],
                   font=("Arial", 9),
                   foreground=MODERN_COLORS['gray'])
    
    # 现代化输入框
    style.configure("Modern.TEntry",
                   fieldbackground=MODERN_COLORS['white'],
                   borderwidth=2,
                   focuscolor=MODERN_COLORS['primary'],
                   relief="solid")
    
    # 现代化按钮基础样式
    style.configure("Modern.TButton",
                   padding=(15, 8),
                   font=("Arial", 10),
                   relief="flat",
                   borderwidth=0)

def create_card_frame(parent, title=None, padding="15"):
    """创建现代化卡片式框架"""
    if title:
        # 使用tk.LabelFrame确保白色背景
        frame = tk.LabelFrame(parent, text=title, 
                             bg="#FFFFFF", fg="#333333", 
                             font=("Arial", 11, "bold"),
                             relief="solid", bd=1, padx=15, pady=15)
    else:
        frame = tk.Frame(parent, bg="#FFFFFF", 
                        relief="solid", bd=1)
        # 添加内边距
        inner_frame = tk.Frame(frame, bg="#FFFFFF")
        inner_frame.pack(fill="both", expand=True, padx=15, pady=15)
        frame = inner_frame
    
    # 配置列权重
    frame.columnconfigure(0, weight=1)
    
    return frame

def create_gradient_canvas(parent, color1, color2, width=400, height=100):
    """创建渐变背景画布"""
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
    
    # 创建渐变效果
    for i in range(height):
        # 计算渐变比例
        ratio = i / height
        
        # 计算颜色值
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        
        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)
        
        color = f"#{r:02x}{g:02x}{b:02x}"
        
        canvas.create_line(0, i, width, i, fill=color, width=1)
    
    return canvas

def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_icon_button(parent, icon, text, command, style_type="primary", **kwargs):
    """创建带图标的现代化按钮"""
    # 选择样式
    styles = {
        'primary': {
            'bg': MODERN_COLORS['primary'],
            'fg': MODERN_COLORS['white'],
            'activebackground': MODERN_COLORS['primary_dark'],
            'activeforeground': MODERN_COLORS['white'],
        },
        'success': {
            'bg': MODERN_COLORS['success'],
            'fg': MODERN_COLORS['white'],
            'activebackground': '#38a169',
            'activeforeground': MODERN_COLORS['white'],
        },
        'warning': {
            'bg': MODERN_COLORS['warning'],
            'fg': MODERN_COLORS['white'],
            'activebackground': '#dd7a1f',
            'activeforeground': MODERN_COLORS['white'],
        },
        'danger': {
            'bg': MODERN_COLORS['danger'],
            'fg': MODERN_COLORS['white'],
            'activebackground': '#e53e3e',
            'activeforeground': MODERN_COLORS['white'],
        },
        'secondary': {
            'bg': MODERN_COLORS['white'],
            'fg': MODERN_COLORS['dark'],
            'activebackground': MODERN_COLORS['light_gray'],
            'activeforeground': MODERN_COLORS['dark'],
        }
    }
    
    style_config = styles.get(style_type, styles['primary'])
    
    # 基础样式
    base_style = {
        'font': ('Arial', 10, 'bold'),
        'relief': 'flat',
        'bd': 0,
        'padx': 15,
        'pady': 10,
        'cursor': 'hand2',
        'text': f"{icon} {text}" if icon else text
    }
    
    # 合并样式
    base_style.update(style_config)
    base_style.update(kwargs)
    
    button = tk.Button(parent, command=command, **base_style)
    
    # 添加悬停效果
    def on_enter(e):
        button.config(bg=style_config['activebackground'])
    
    def on_leave(e):
        button.config(bg=style_config['bg'])
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    
    return button

def create_status_indicator(parent, status="ready"):
    """创建状态指示器"""
    status_colors = {
        'ready': MODERN_COLORS['success'],
        'working': MODERN_COLORS['warning'],
        'error': MODERN_COLORS['danger'],
        'offline': MODERN_COLORS['gray']
    }
    
    frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
    
    # 状态圆点
    indicator = tk.Label(
        frame,
        text="●",
        font=("Arial", 16),
        fg=status_colors.get(status, MODERN_COLORS['gray']),
        bg=MODERN_COLORS['bg_secondary']
    )
    indicator.pack(side="left", padx=(0, 8))
    
    return frame, indicator

def setup_styles():
    """设置界面样式（保留向后兼容）"""
    setup_modern_styles()


def set_buttons_state(buttons, enabled):
    """设置按钮状态
    
    Args:
        buttons: 按钮列表或单个按钮
        enabled: 是否启用
    """
    state = "normal" if enabled else "disabled"
    
    if isinstance(buttons, (list, tuple)):
        for button in buttons:
            if button:
                button.config(state=state)
    else:
        if buttons:
            buttons.config(state=state)


def open_url(url):
    """打开URL"""
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"无法打开URL {url}: {e}")


def open_directory(path):
    """打开目录"""
    try:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            os.startfile(abs_path)
        else:
            print(f"目录不存在: {abs_path}")
    except Exception as e:
        try:
            # Linux/Mac
            os.system(f'open "{os.path.abspath(path)}"')
        except Exception as e2:
            print(f"无法打开目录 {path}: {e}, {e2}")


def format_log_message(message):
    """格式化日志消息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] {message}\n"


def safe_filename(text, max_length=30):
    """生成安全的文件名"""
    # 替换非法字符
    illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    safe_text = text
    for char in illegal_chars:
        safe_text = safe_text.replace(char, '_')
    
    # 限制长度
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]
    
    return safe_text


def create_labeled_entry(parent, label_text, variable=None, **kwargs):
    """创建带标签的输入框
    
    Args:
        parent: 父组件
        label_text: 标签文本
        variable: tkinter变量
        **kwargs: Entry组件的其他参数
    
    Returns:
        tuple: (frame, label, entry)
    """
    frame = ttk.Frame(parent)
    label = ttk.Label(frame, text=label_text)
    label.grid(row=0, column=0, sticky="w")
    
    entry_kwargs = {"width": 30}
    entry_kwargs.update(kwargs)
    
    if variable:
        entry_kwargs["textvariable"] = variable
    
    entry = ttk.Entry(frame, **entry_kwargs)
    entry.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
    frame.columnconfigure(0, weight=1)
    
    return frame, label, entry


def create_button_frame(parent, buttons_config):
    """创建按钮框架
    
    Args:
        parent: 父组件
        buttons_config: 按钮配置列表，格式: [(text, command, style), ...]
    
    Returns:
        tuple: (frame, buttons_list)
    """
    frame = ttk.Frame(parent)
    buttons = []
    
    for i, (text, command, style) in enumerate(buttons_config):
        button = ttk.Button(frame, text=text, command=command, style=style)
        button.grid(row=0, column=i, padx=(0 if i == 0 else 5, 0))
        buttons.append(button)
    
    return frame, buttons


def validate_file_path(file_path):
    """验证文件路径是否有效"""
    if not file_path:
        return False, "文件路径不能为空"
    
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"路径不是文件: {file_path}"
    
    return True, "文件路径有效"


def validate_directory_path(dir_path):
    """验证目录路径是否有效"""
    if not dir_path:
        return False, "目录路径不能为空"
    
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True, "目录路径有效"
    except Exception as e:
        return False, f"无法创建目录: {e}"


def create_custom_button(parent, text, command, style_type="action", **kwargs):
    """创建自定义按钮，确保有背景色"""
    import tkinter as tk
    
    # 定义按钮样式
    styles = {
        'action': {
            'bg': '#1565C0',
            'fg': '#FFFFFF',
            'activebackground': '#0D47A1',
            'activeforeground': '#FFFFFF',
            'font': ('Arial', 10, 'bold'),
            'relief': 'raised',
            'bd': 2,
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2'
        },
        'warning': {
            'bg': '#FF9800',
            'fg': '#FFFFFF',
            'activebackground': '#E68900',
            'activeforeground': '#FFFFFF',
            'font': ('Arial', 9, 'bold'),
            'relief': 'raised',
            'bd': 2,
            'padx': 10,
            'pady': 6,
            'cursor': 'hand2'
        },
        'success': {
            'bg': '#4CAF50',
            'fg': '#FFFFFF',
            'activebackground': '#45A049',
            'activeforeground': '#FFFFFF',
            'font': ('Arial', 9, 'bold'),
            'relief': 'raised',
            'bd': 2,
            'padx': 10,
            'pady': 6,
            'cursor': 'hand2'
        },
        'danger': {
            'bg': '#F44336',
            'fg': '#FFFFFF',
            'activebackground': '#D32F2F',
            'activeforeground': '#FFFFFF',
            'font': ('Arial', 9, 'bold'),
            'relief': 'raised',
            'bd': 2,
            'padx': 10,
            'pady': 6,
            'cursor': 'hand2'
        },
        'config': {
            'bg': '#FFFFFF',
            'fg': '#333333',
            'activebackground': '#FFFFFF',
            'activeforeground': '#333333',
            'font': ('Arial', 9),
            'relief': 'raised',
            'bd': 1,
            'padx': 8,
            'pady': 4,
            'cursor': 'hand2'
        },
        'default': {
            'bg': '#FFFFFF',
            'fg': '#333333',
            'activebackground': '#FFFFFF',
            'activeforeground': '#333333',
            'font': ('Arial', 9),
            'relief': 'raised',
            'bd': 1,
            'padx': 8,
            'pady': 6,
            'cursor': 'hand2'
        }
    }
    
    style_config = styles.get(style_type, styles['default'])
    style_config.update(kwargs)
    
    # 创建tkinter Button而不是ttk Button
    button = tk.Button(
        parent,
        text=text,
        command=command,
        **style_config
    )
    
    return button 