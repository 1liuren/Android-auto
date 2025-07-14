#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
状态栏组件 - 现代化版本
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from ..utils.ui_helpers import MODERN_COLORS, create_gradient_canvas


class StatusBar:
    """现代化状态栏组件"""
    
    def __init__(self, parent, gui_app):
        self.parent = parent
        self.gui_app = gui_app
        self.frame = None
        self.status_label = None
        self.time_label = None
        
        # 创建状态栏
        self._create_status_bar()
        
        # 启动时间更新
        self._update_time()
    
    def _create_status_bar(self):
        """创建现代化状态栏"""
        # 创建主框架
        self.frame = tk.Frame(self.parent, bg=MODERN_COLORS['bg_secondary'], 
                             relief="solid", bd=1, height=50)
        self.frame.columnconfigure(2, weight=1)
        self.frame.pack_propagate(False)  # 保持固定高度
        
        # 左侧状态区域
        left_frame = tk.Frame(self.frame, bg=MODERN_COLORS['bg_secondary'])
        left_frame.grid(row=0, column=0, sticky="w", padx=15, pady=8)
        
        # 状态指示器框架
        status_indicator_frame = tk.Frame(left_frame, bg=MODERN_COLORS['bg_secondary'])
        status_indicator_frame.pack(side="left", padx=(0, 15))
        
        # 状态指示灯（带光晕效果）
        self.status_indicator = tk.Label(
            status_indicator_frame,
            text="●",
            font=("Arial", 14),
            fg=MODERN_COLORS['success'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.status_indicator.pack(side="left", padx=(0, 6))
        
        # 状态文本
        self.status_label = tk.Label(
            status_indicator_frame, 
            text="就绪", 
            font=("Arial", 11, "bold"),
            fg=MODERN_COLORS['dark'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.status_label.pack(side="left")
        
        # 中间设备信息区域
        device_frame = tk.Frame(self.frame, bg=MODERN_COLORS['bg_secondary'])
        device_frame.grid(row=0, column=1, sticky="w", padx=15)
        
        # 设备图标
        device_icon = tk.Label(
            device_frame,
            text="📱",
            font=("Arial", 14),
            bg=MODERN_COLORS['bg_secondary']
        )
        device_icon.pack(side="left", padx=(0, 6))
        
        # 设备信息标签
        self.device_info_label = tk.Label(
            device_frame,
            text="未连接设备",
            font=("Arial", 10),
            fg=MODERN_COLORS['gray'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.device_info_label.pack(side="left")
        
        # 右侧信息区域
        right_frame = tk.Frame(self.frame, bg=MODERN_COLORS['bg_secondary'])
        right_frame.grid(row=0, column=3, sticky="e", padx=15, pady=8)
        
        # 版本标签
        version_frame = tk.Frame(right_frame, bg=MODERN_COLORS['bg_secondary'])
        version_frame.pack(side="right", padx=(15, 0))
        
        version_label = tk.Label(
            version_frame,
            text="v2.0",
            font=("Arial", 9, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_secondary']
        )
        version_label.pack(side="right")
        
        # 时间框架
        time_frame = tk.Frame(right_frame, bg=MODERN_COLORS['bg_secondary'])
        time_frame.pack(side="right", padx=(0, 15))
        
        # 时钟图标
        clock_icon = tk.Label(
            time_frame,
            text="🕐",
            font=("Arial", 12),
            bg=MODERN_COLORS['bg_secondary']
        )
        clock_icon.pack(side="left", padx=(0, 6))
        
        # 时间标签
        self.time_label = tk.Label(
            time_frame, 
            text="",
            font=("Arial", 10),
            fg=MODERN_COLORS['dark_gray'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.time_label.pack(side="left")
        
        # 将状态标签引用保存到gui_app中
        self.gui_app.status_label = self.status_label
        self.gui_app.time_label = self.time_label
        self.gui_app.device_info_label = self.device_info_label
    
    def _update_time(self):
        """更新时间显示"""
        if self.time_label:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.time_label.config(text=current_time)
        
        # 每秒更新一次
        if hasattr(self.gui_app, 'root'):
            self.gui_app.root.after(1000, self._update_time)
    
    def update_status(self, text, color=None, indicator_color=None):
        """更新状态显示"""
        if self.status_label:
            self.status_label.config(text=text)
            if color:
                self.status_label.config(fg=color)
        
        if self.status_indicator and indicator_color:
            self.status_indicator.config(fg=indicator_color)
    
    def set_ready_status(self):
        """设置就绪状态"""
        self.update_status("就绪", MODERN_COLORS['dark'], MODERN_COLORS['success'])
    
    def set_working_status(self, task_type="任务"):
        """设置工作状态"""
        self.update_status(f"正在执行{task_type}...", MODERN_COLORS['dark'], MODERN_COLORS['warning'])
    
    def set_success_status(self, task_type="任务"):
        """设置成功状态"""
        self.update_status(f"{task_type}执行完成", MODERN_COLORS['success'], MODERN_COLORS['success'])
    
    def set_error_status(self, error_msg="错误"):
        """设置错误状态"""
        self.update_status(f"错误: {error_msg}", MODERN_COLORS['danger'], MODERN_COLORS['danger'])
    
    def set_warning_status(self, warning_msg="警告"):
        """设置警告状态"""
        self.update_status(f"警告: {warning_msg}", MODERN_COLORS['warning'], MODERN_COLORS['warning'])
    
    def update_device_info(self, device_info, color=None):
        """更新设备信息显示"""
        if self.device_info_label:
            self.device_info_label.config(text=device_info)
            if color:
                self.device_info_label.config(fg=color)
            elif "已连接" in device_info:
                self.device_info_label.config(fg=MODERN_COLORS['connected'])
            elif "未连接" in device_info:
                self.device_info_label.config(fg=MODERN_COLORS['disconnected'])
            elif "检测" in device_info:
                self.device_info_label.config(fg=MODERN_COLORS['warning_status'])
            else:
                self.device_info_label.config(fg=MODERN_COLORS['gray'])
    
    def get_current_time(self):
        """获取当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def grid(self, **kwargs):
        """布局状态栏"""
        if self.frame:
            self.frame.grid(**kwargs) 