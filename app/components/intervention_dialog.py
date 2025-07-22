#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人工介入对话框组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
try:
    from app.utils.ui_helpers import MODERN_COLORS, create_custom_button
except ImportError:
    # 备用颜色方案
    MODERN_COLORS = {
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8f9fa',
        'primary': '#007bff',
        'dark': '#333333',
        'success': '#28a745',
        'danger': '#dc3545'
    }
    def create_custom_button(parent, text, command=None, style_type='primary', width=None, **kwargs):
        """备用按钮创建函数"""
        # 定义按钮样式
        styles = {
            'primary': {'bg': '#007bff', 'fg': 'white'},
            'success': {'bg': '#28a745', 'fg': 'white'},
            'danger': {'bg': '#dc3545', 'fg': 'white'},
            'action': {'bg': '#1565C0', 'fg': 'white'}
        }
        
        style_config = styles.get(style_type, styles['primary'])
        
        btn_config = {
            'text': text,
            'command': command,
            'font': ('Arial', 10, 'bold'),
            'relief': 'flat',
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2',
            **style_config,
            **kwargs
        }
        
        if width:
            btn_config['width'] = width
            
        return tk.Button(parent, **btn_config)


class InterventionDialog:
    """人工介入对话框"""
    
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback
        self.dialog = None
        self.result = None
        
        # 对话框变量
        self.intervention_prompt_var = tk.StringVar()
        self.restart_step_var = tk.StringVar(value="1")
        
    def show_dialog(self, current_step=1):
        """显示人工介入对话框
        
        Args:
            current_step: 当前执行到的步骤数
        """
        # 创建模态对话框
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🛠️ 人工介入 - 任务纠错")
        self.dialog.geometry("700x650")  # 增加对话框尺寸以容纳所有内容
        self.dialog.resizable(True, True)  # 允许调整大小
        self.dialog.configure(bg=MODERN_COLORS['bg_primary'])
        
        # 设置为模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 创建界面
        self._create_dialog_content(current_step)
        
        # 等待对话框关闭
        self.dialog.wait_window()
        
        return self.result
    
    def _create_simple_dialog_content(self, current_step):
        """创建简化版本的对话框内容（备用方案）"""
        try:
            # 主框架
            main_frame = tk.Frame(self.dialog, bg='#ffffff')
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # 标题
            title_label = tk.Label(
                main_frame,
                text="🛠️ 人工介入 - 任务纠错",
                font=("Arial", 14, "bold"),
                fg='#007bff',
                bg='#ffffff'
            )
            title_label.pack(pady=(0, 20))
            
            # 说明文本
            info_text = f"任务已执行到第 {current_step} 步，需要人工介入进行纠错。\n\n请提供补充说明和重新开始的步骤号："
            info_label = tk.Label(
                main_frame,
                text=info_text,
                font=("Arial", 10),
                fg='#333333',
                bg='#ffffff',
                justify="left"
            )
            info_label.pack(pady=(0, 15))
            
            # 补充说明输入
            prompt_label = tk.Label(main_frame, text="补充说明：", font=("Arial", 10, "bold"), bg='#ffffff')
            prompt_label.pack(anchor="w", pady=(0, 5))
            
            prompt_text = tk.Text(
                main_frame,
                height=6,
                width=60,
                font=("Arial", 10),
                wrap="word",
                relief="solid",
                bd=1
            )
            prompt_text.pack(fill="x", pady=(0, 15))
            
            # 步骤输入
            step_label = tk.Label(main_frame, text="重新开始步骤：", font=("Arial", 10, "bold"), bg='#ffffff')
            step_label.pack(anchor="w", pady=(0, 5))
            
            step_entry = tk.Entry(
                main_frame,
                textvariable=self.restart_step_var,
                font=("Arial", 10),
                width=10,
                relief="solid",
                bd=1
            )
            step_entry.pack(anchor="w", pady=(0, 20))
            
            # 按钮区域
            button_frame = tk.Frame(main_frame, bg='#ffffff')
            button_frame.pack(fill="x", pady=(10, 0))
            
            # 确认按钮
            confirm_btn = tk.Button(
                button_frame,
                text="✓ 确认介入",
                command=lambda: self._confirm_intervention(prompt_text.get("1.0", "end-1c")),
                bg='#28a745',
                fg='white',
                font=("Arial", 10, "bold"),
                padx=20,
                pady=8,
                relief="flat"
            )
            confirm_btn.pack(side="right", padx=(10, 0))
            
            # 取消按钮
            cancel_btn = tk.Button(
                button_frame,
                text="✗ 取消",
                command=self._cancel_intervention,
                bg='#dc3545',
                fg='white',
                font=("Arial", 10, "bold"),
                padx=20,
                pady=8,
                relief="flat"
            )
            cancel_btn.pack(side="right")
            
            # 强制更新界面
            self.dialog.update_idletasks()
            
        except Exception as e:
            print(f"创建简化对话框时出错: {e}")
            # 最后的备用方案：使用messagebox
            self._use_messagebox_fallback(current_step)
    
    def _use_messagebox_fallback(self, current_step):
        """使用messagebox作为最后的备用方案"""
        try:
            # 使用简单的输入对话框
            import tkinter.simpledialog as simpledialog
            
            # 获取补充说明
            intervention_prompt = simpledialog.askstring(
                "人工介入 - 补充说明",
                f"任务已执行到第 {current_step} 步，需要人工介入。\n\n请输入补充说明：",
                parent=self.dialog
            )
            
            if not intervention_prompt:
                self.result = None
                self.dialog.destroy()
                return
            
            # 获取重新开始步骤
            restart_step = simpledialog.askinteger(
                "人工介入 - 重新开始步骤",
                "请输入从第几步重新开始（必须大于等于1）：",
                minvalue=1,
                initialvalue=1,
                parent=self.dialog
            )
            
            if restart_step is None:
                self.result = None
                self.dialog.destroy()
                return
            
            # 确认操作
            confirm_msg = f"确认人工介入操作？\n\n补充说明：{intervention_prompt}\n重新开始步骤：{restart_step}"
            if messagebox.askyesno("确认人工介入", confirm_msg, parent=self.dialog):
                self.result = {
                    'intervention_prompt': intervention_prompt,
                    'restart_step': restart_step
                }
            else:
                self.result = None
            
            self.dialog.destroy()
            
        except Exception as e:
            print(f"备用方案也失败了: {e}")
            self.result = None
            self.dialog.destroy()
    
    def _center_dialog(self):
        """将对话框居中显示"""
        self.dialog.update_idletasks()
        
        # 获取父窗口位置和大小
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算对话框位置
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_dialog_content(self, current_step):
        """创建对话框内容"""
        try:
            # 主框架
            main_frame = tk.Frame(self.dialog, bg=MODERN_COLORS.get('bg_primary', '#ffffff'))
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # 标题区域
            self._create_title_section(main_frame)
            
            # 说明区域
            self._create_info_section(main_frame, current_step)
            
            # 输入区域
            self._create_input_section(main_frame)
            
            # 按钮区域
            self._create_button_section(main_frame)
            
            # 强制更新界面
            self.dialog.update_idletasks()
            
        except Exception as e:
            print(f"创建对话框内容时出错: {e}")
            # 创建简化版本的对话框
            self._create_simple_dialog_content(current_step)
    
    def _create_title_section(self, parent):
        """创建标题区域"""
        title_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        title_frame.pack(fill="x", pady=(0, 20))
        
        # 图标和标题
        title_label = tk.Label(
            title_frame,
            text="🛠️ 人工介入 - 任务纠错",
            font=("Arial", 16, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_primary']
        )
        title_label.pack()
        
        # 分隔线
        separator = ttk.Separator(title_frame, orient="horizontal")
        separator.pack(fill="x", pady=(10, 0))
    
    def _create_info_section(self, parent, current_step):
        """创建说明区域"""
        info_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'], relief="solid", bd=1)
        info_frame.pack(fill="x", pady=(0, 20))
        
        # 说明文本
        info_text = f"""
📋 任务执行过程中遇到问题，需要人工介入进行纠错：

🔄 当前执行状态：
   • 已执行到第 {current_step} 步
   • 任务已暂停，等待人工指导

✏️ 请提供以下信息：
   1. 补充说明：描述问题或提供额外的操作指导
   2. 重新开始步骤：指定从哪一步重新开始执行

⚠️ 注意事项：
   • 指定步骤及其后续的历史记录和文件将被清理
   • 请手动将设备页面调整到指定步骤的状态
   • 确认页面状态正确后，任务将继续执行
        """
        
        info_label = tk.Label(
            info_frame,
            text=info_text.strip(),
            font=("Arial", 10),
            fg=MODERN_COLORS['dark'],
            bg=MODERN_COLORS['bg_secondary'],
            justify="left",
            anchor="nw"
        )
        info_label.pack(fill="both", expand=True, padx=15, pady=15)
    
    def _create_input_section(self, parent):
        """创建输入区域"""
        input_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        input_frame.pack(fill="x", pady=(0, 20))
        
        # 补充说明输入
        prompt_label = tk.Label(
            input_frame,
            text="📝 补充说明（必填）：",
            font=("Arial", 11, "bold"),
            fg=MODERN_COLORS['dark'],
            bg=MODERN_COLORS['bg_primary']
        )
        prompt_label.pack(anchor="w", pady=(0, 5))
        
        # 多行文本输入框
        prompt_frame = tk.Frame(input_frame, bg=MODERN_COLORS['bg_primary'])
        prompt_frame.pack(fill="x", pady=(0, 15))
        
        self.prompt_text = tk.Text(
            prompt_frame,
            height=4,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark'],
            relief="solid",
            bd=2,
            wrap="word"
        )
        self.prompt_text.pack(side="left", fill="both", expand=True)
        
        # 滚动条
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.prompt_text.yview)
        prompt_scrollbar.pack(side="right", fill="y")
        self.prompt_text.config(yscrollcommand=prompt_scrollbar.set)
        
        # 重新开始步骤输入
        step_label = tk.Label(
            input_frame,
            text="🔄 从第几步重新开始（必填）：",
            font=("Arial", 11, "bold"),
            fg=MODERN_COLORS['dark'],
            bg=MODERN_COLORS['bg_primary']
        )
        step_label.pack(anchor="w", pady=(0, 5))
        
        step_entry = tk.Entry(
            input_frame,
            textvariable=self.restart_step_var,
            font=("Arial", 11),
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark'],
            relief="solid",
            bd=2,
            width=10
        )
        step_entry.pack(anchor="w")
        
        # 添加验证
        step_entry.config(validate="key", validatecommand=(self.dialog.register(self._validate_step_input), "%P"))
    
    def _validate_step_input(self, value):
        """验证步骤输入"""
        if value == "":
            return True
        try:
            step = int(value)
            return step >= 1
        except ValueError:
            return False
    
    def _create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        button_frame.pack(fill="x")
        
        # 按钮容器
        btn_container = tk.Frame(button_frame, bg=MODERN_COLORS['bg_primary'])
        btn_container.pack(anchor="e")
        
        # 取消按钮
        cancel_btn = create_custom_button(
            btn_container,
            text="❌ 取消",
            command=self._cancel_intervention,
            style_type="danger",
            width=12
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        # 确认按钮
        confirm_btn = create_custom_button(
            btn_container,
            text="✅ 确认介入",
            command=lambda: self._confirm_intervention(),
            style_type="success",
            width=12
        )
        confirm_btn.pack(side="left")
    
    def _cancel_intervention(self):
        """取消人工介入"""
        self.result = None
        if self.dialog:
            self.dialog.destroy()
    
    def _confirm_intervention(self, prompt_text=None):
        """确认人工介入"""
        # 获取输入内容
        if prompt_text is not None:
            intervention_prompt = prompt_text.strip()
        elif hasattr(self, 'prompt_text'):
            intervention_prompt = self.prompt_text.get("1.0", "end-1c").strip()
        else:
            intervention_prompt = ""
        
        restart_step = self.restart_step_var.get().strip()
        
        # 验证输入
        if not intervention_prompt:
            messagebox.showerror("错误", "请输入补充说明！", parent=self.dialog)
            return
        
        if not restart_step:
            messagebox.showerror("错误", "请输入重新开始的步骤数！", parent=self.dialog)
            return
        
        try:
            restart_step_num = int(restart_step)
            if restart_step_num < 1:
                messagebox.showerror("错误", "步骤数必须大于等于1！", parent=self.dialog)
                return
        except ValueError:
            messagebox.showerror("错误", "步骤数必须是有效的数字！", parent=self.dialog)
            return
        
        # 显示详细的确认对话框
        self._show_confirmation_dialog(intervention_prompt, restart_step_num)
    
    def _show_confirmation_dialog(self, intervention_prompt, restart_step_num):
        """显示确认对话框"""
        # 创建确认对话框
        confirm_dialog = tk.Toplevel(self.dialog)
        confirm_dialog.title("🔍 确认人工介入")
        confirm_dialog.geometry("500x400")
        confirm_dialog.resizable(False, False)
        confirm_dialog.configure(bg='#ffffff')
        
        # 设置为模态对话框
        confirm_dialog.transient(self.dialog)
        confirm_dialog.grab_set()
        
        # 主框架
        main_frame = tk.Frame(confirm_dialog, bg='#ffffff')
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="🔍 确认人工介入操作",
            font=("Arial", 14, "bold"),
            fg='#2c3e50',
            bg='#ffffff'
        )
        title_label.pack(pady=(0, 20))
        
        # 内容区域
        content_frame = tk.Frame(main_frame, bg='#f8f9fa', relief="solid", bd=1)
        content_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # 补充说明
        prompt_label = tk.Label(
            content_frame,
            text="📝 补充说明：",
            font=("Arial", 11, "bold"),
            fg='#2c3e50',
            bg='#f8f9fa'
        )
        prompt_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        prompt_text = tk.Text(
            content_frame,
            height=6,
            font=("Arial", 10),
            bg='#ffffff',
            fg='#2c3e50',
            relief="solid",
            bd=1,
            wrap="word",
            state="normal"
        )
        prompt_text.pack(fill="x", padx=15, pady=(0, 15))
        prompt_text.insert("1.0", intervention_prompt)
        prompt_text.config(state="disabled")
        
        # 重新开始步骤
        step_label = tk.Label(
            content_frame,
            text=f"🔄 从第 {restart_step_num} 步重新开始",
            font=("Arial", 11, "bold"),
            fg='#e74c3c',
            bg='#f8f9fa'
        )
        step_label.pack(anchor="w", padx=15, pady=(0, 15))
        
        # 警告信息
        warning_label = tk.Label(
            content_frame,
            text="⚠️ 注意：第{}步及其后续的历史记录和文件将被清理\n请确保已手动将设备页面调整到第{}步的状态".format(restart_step_num, restart_step_num),
            font=("Arial", 10),
            fg='#e67e22',
            bg='#f8f9fa',
            justify="left"
        )
        warning_label.pack(anchor="w", padx=15, pady=(0, 15))
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(fill="x")
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="❌ 取消",
            font=("Arial", 11, "bold"),
            bg='#e74c3c',
            fg='white',
            relief="flat",
            padx=20,
            pady=8,
            command=lambda: confirm_dialog.destroy()
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        # 确认按钮
        confirm_btn = tk.Button(
            button_frame,
            text="✅ 确认执行",
            font=("Arial", 11, "bold"),
            bg='#27ae60',
            fg='white',
            relief="flat",
            padx=20,
            pady=8,
            command=lambda: self._execute_intervention(confirm_dialog, intervention_prompt, restart_step_num)
        )
        confirm_btn.pack(side="right")
        
        # 居中显示
        confirm_dialog.update_idletasks()
        x = (confirm_dialog.winfo_screenwidth() - confirm_dialog.winfo_reqwidth()) // 2
        y = (confirm_dialog.winfo_screenheight() - confirm_dialog.winfo_reqheight()) // 2
        confirm_dialog.geometry(f"+{x}+{y}")
    
    def _execute_intervention(self, confirm_dialog, intervention_prompt, restart_step_num):
        """执行人工介入"""
        self.result = {
            'intervention_prompt': intervention_prompt,
            'restart_step': restart_step_num
        }
        confirm_dialog.destroy()
        if self.dialog:
            self.dialog.destroy()


def show_intervention_dialog(parent, current_step=1, callback=None):
    """显示人工介入对话框的便捷函数
    
    Args:
        parent: 父窗口
        current_step: 当前执行到的步骤数
        callback: 回调函数
    
    Returns:
        dict: 包含intervention_prompt和restart_step的字典，如果取消则返回None
    """
    dialog = InterventionDialog(parent, callback)
    return dialog.show_dialog(current_step)
