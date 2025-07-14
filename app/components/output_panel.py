#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
输出面板组件
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from ..utils.ui_helpers import format_log_message


class OutputPanel:
    """输出面板组件"""
    
    def __init__(self, parent, gui_app):
        self.parent = parent
        self.gui_app = gui_app
        self.frame = None
        self.output_text = None
        
        # 创建输出面板
        self._create_output_panel()
    
    def _create_output_panel(self):
        """创建输出面板"""
        # 使用tk.LabelFrame替代ttk.LabelFrame以确保白色背景
        self.frame = tk.LabelFrame(self.parent, text="📄 执行日志", 
                                   bg="#FFFFFF", fg="#333333", 
                                   font=("Arial", 11, "bold"),
                                   relief="solid", bd=1, padx=10, pady=10)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        # 创建文本区域和滚动条
        self.output_text = scrolledtext.ScrolledText(
            self.frame, 
            height=15, 
            font=("Consolas", 10),
            bg="#FFFFFF",
            fg="#333333",
            selectbackground="#2196F3",
            selectforeground="white",
            wrap=tk.WORD,
            relief="solid",
            borderwidth=1
        )
        self.output_text.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # 配置文本标签颜色
        self._configure_text_tags()
        
        # 创建按钮区域
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(row=1, column=0, sticky="ew")
        buttons_frame.columnconfigure(2, weight=1)
        
        # 清空日志按钮
        ttk.Button(
            buttons_frame, 
            text="🗑️ 清空日志", 
            command=self._clear_output,
            style="Config.TButton"
        ).grid(row=0, column=0, padx=(0, 10))
        
        # 保存日志按钮
        ttk.Button(
            buttons_frame, 
            text="💾 保存日志", 
            command=self._save_log,
            style="Config.TButton"
        ).grid(row=0, column=1, padx=(0, 10))
        
        # 日志级别显示
        self.log_info_label = ttk.Label(
            buttons_frame,
            text="📊 日志: 0 条",
            font=("Arial", 9),
            foreground="#666666"
        )
        self.log_info_label.grid(row=0, column=2, sticky="e")
        
        # 将输出文本框引用保存到gui_app中
        self.gui_app.output_text = self.output_text
        
        # 日志计数器
        self.log_count = 0
    
    def _configure_text_tags(self):
        """配置文本标签颜色"""
        # 成功信息 - 绿色
        self.output_text.tag_config("success", foreground="#4CAF50", font=("Consolas", 10, "bold"))
        # 错误信息 - 红色
        self.output_text.tag_config("error", foreground="#F44336", font=("Consolas", 10, "bold"))
        # 警告信息 - 橙色
        self.output_text.tag_config("warning", foreground="#FF9800", font=("Consolas", 10, "bold"))
        # 信息 - 蓝色
        self.output_text.tag_config("info", foreground="#2196F3", font=("Consolas", 10, "bold"))
        # 时间戳 - 灰色
        self.output_text.tag_config("timestamp", foreground="#888888", font=("Consolas", 9))
    
    def _save_log(self):
        """保存日志到文件"""
        from tkinter import filedialog
        from datetime import datetime
        
        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialname=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            success = self.save_log_to_file(filename)
            if success:
                self.log_message(f"✅ 日志已保存到: {filename}")
            else:
                self.log_message(f"❌ 保存日志失败")
    
    def _update_log_count(self):
        """更新日志计数显示"""
        if hasattr(self, 'log_info_label'):
            self.log_info_label.config(text=f"📊 日志: {self.log_count} 条")
    
    def _clear_output(self):
        """清空输出"""
        if self.output_text:
            self.output_text.delete(1.0, tk.END)
            self.log_count = 0
            self._update_log_count()
    
    def append_output(self, message):
        """添加输出信息"""
        if self.output_text:
            formatted_message = format_log_message(message)
            
            # 确定消息类型和标签
            tag = self._get_message_tag(message)
            
            # 插入时间戳
            timestamp_part = formatted_message.split(']')[0] + ']'
            message_part = formatted_message[len(timestamp_part):]
            
            # 插入带标签的文本
            self.output_text.insert(tk.END, timestamp_part, "timestamp")
            self.output_text.insert(tk.END, message_part, tag)
            
            self.output_text.see(tk.END)
            
            # 更新日志计数
            self.log_count += 1
            self._update_log_count()
            
            # 限制输出长度
            if self.output_text.get(1.0, tk.END).count('\n') > 1000:
                self.output_text.delete(1.0, "100.0")
                self.log_count = max(0, self.log_count - 100)
                self._update_log_count()
    
    def _get_message_tag(self, message):
        """根据消息内容确定标签"""
        if '✅' in message or '成功' in message:
            return "success"
        elif '❌' in message or '错误' in message or '失败' in message:
            return "error"
        elif '⚠️' in message or '警告' in message:
            return "warning"
        elif '📊' in message or '🚀' in message or '💡' in message:
            return "info"
        else:
            return None
    
    def log_message(self, message):
        """记录日志消息（线程安全）"""
        if hasattr(self.gui_app, 'root'):
            self.gui_app.root.after(0, lambda: self.append_output(message))
    
    def get_text_content(self):
        """获取文本内容"""
        if self.output_text:
            return self.output_text.get(1.0, tk.END)
        return ""
    
    def save_log_to_file(self, filename):
        """保存日志到文件"""
        try:
            content = self.get_text_content()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.log_message(f"❌ 保存日志失败: {e}")
            return False
    
    def grid(self, **kwargs):
        """网格布局"""
        if self.frame:
            self.frame.grid(**kwargs) 