#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
控制面板组件 - 现代化版本
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
from ..utils.validators import validate_excel_file
from ..utils.ui_helpers import create_custom_button, create_card_frame, create_icon_button, MODERN_COLORS


class ControlPanel:
    """控制面板组件"""
    
    def __init__(self, parent, gui_app):
        self.parent = parent
        self.gui_app = gui_app
        self.frame = None
        
        # 创建控制面板
        self._create_control_panel()
    
    def _create_control_panel(self):
        """创建现代化控制面板"""
        # 主控制面板框架
        self.frame = create_card_frame(self.parent, "📱 任务控制中心")
        self.frame.columnconfigure(0, weight=1)
        
        # 设备状态和控制区域
        self._create_device_section()
        
        # 单个任务执行区域
        self._create_single_task_section()
        
        # 批量任务执行区域
        self._create_batch_task_section()
    
    def _create_device_section(self):
        """创建设备状态和控制区域"""
        device_frame = create_card_frame(self.frame, "🔌 设备控制")
        device_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        device_frame.columnconfigure(1, weight=1)
        
        # 检测设备按钮
        self.detect_device_btn = create_icon_button(
            device_frame,
            icon="🔍",
            text="检测设备",
            command=self._detect_device,
            style_type="primary"
        )
        self.detect_device_btn.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # 设备状态显示
        self.device_status_frame = tk.Frame(device_frame, bg=MODERN_COLORS['bg_secondary'])
        self.device_status_frame.grid(row=0, column=1, sticky="ew")
        
        # 状态指示器
        self.device_indicator = tk.Label(
            self.device_status_frame,
            text="●",
            font=("Arial", 16),
            fg=MODERN_COLORS['disconnected'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.device_indicator.pack(side="left", padx=(0, 8))
        
        # 状态文本
        self.device_status_label = tk.Label(
            self.device_status_frame,
            text="未连接设备",
            font=("Arial", 10, "bold"),
            fg=MODERN_COLORS['dark_gray'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.device_status_label.pack(side="left")
    
    def _create_single_task_section(self):
        """创建现代化单个任务执行区域"""
        single_frame = create_card_frame(self.frame, "🎯 单个任务执行")
        single_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        single_frame.columnconfigure(0, weight=1)
        
        # 任务输入区域
        input_frame = tk.Frame(single_frame, bg=MODERN_COLORS['bg_secondary'])
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        input_frame.columnconfigure(1, weight=1)
        
        # 输入标签
        tk.Label(
            input_frame,
            text="💭",
            font=("Arial", 16),
            bg=MODERN_COLORS['bg_secondary'],
            fg=MODERN_COLORS['primary']
        ).grid(row=0, column=0, padx=(0, 10))
        
        # 任务输入框
        self.gui_app.task_entry = tk.Entry(
            input_frame,
            font=("Arial", 11),
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark'],
            relief="solid",
            bd=2,
            highlightthickness=1,
            highlightcolor=MODERN_COLORS['primary']
        )
        self.gui_app.task_entry.grid(row=0, column=1, sticky="ew", ipady=8)
        self.gui_app.task_entry.insert(0, "在京东上查快递")
        
        # 任务控制按钮区域
        button_frame = tk.Frame(single_frame, bg=MODERN_COLORS['bg_secondary'])
        button_frame.grid(row=1, column=0, sticky="ew")
        
        # 执行任务按钮
        self.execute_btn = create_icon_button(
            button_frame,
            icon="🚀",
            text="执行任务",
            command=self._execute_single_task,
            style_type="success"
        )
        self.execute_btn.pack(side="left", padx=(0, 10))
        
        # 中断任务按钮
        self.interrupt_btn = create_icon_button(
            button_frame,
            icon="⏹️",
            text="中断任务",
            command=self._interrupt_task,
            style_type="danger"
        )
        self.interrupt_btn.pack(side="left")
        self.interrupt_btn.config(state="disabled")  # 初始禁用
        
        # 保存按钮引用到gui_app
        self.gui_app.execute_button = self.execute_btn
        self.gui_app.interrupt_button = self.interrupt_btn
    
    def _create_batch_task_section(self):
        """创建现代化批量任务执行区域"""
        batch_frame = create_card_frame(self.frame, "📚 批量任务执行")
        batch_frame.grid(row=2, column=0, sticky="ew")
        batch_frame.columnconfigure(0, weight=1)
        batch_frame.rowconfigure(1, weight=1)
        
        # Excel文件选择区域
        self._create_excel_selection(batch_frame)
        
        # 工作表选择区域
        self._create_sheet_selection(batch_frame)
        
        # 列选择区域
        self._create_column_selection(batch_frame)
        
        # 批量任务控制按钮区域
        batch_button_frame = tk.Frame(batch_frame, bg=MODERN_COLORS['bg_secondary'])
        batch_button_frame.grid(row=5, column=0, sticky="ew", pady=(15, 0))
        
        # 批量执行按钮
        self.batch_execute_btn = create_icon_button(
            batch_button_frame,
            icon="⚡",
            text="批量执行",
            command=self._execute_batch_tasks,
            style_type="primary"
        )
        self.batch_execute_btn.pack(side="left", padx=(0, 10))
        
        # 批量任务中断按钮
        self.batch_interrupt_btn = create_icon_button(
            batch_button_frame,
            icon="⏹️",
            text="中断批量任务",
            command=self._interrupt_batch_task,
            style_type="danger"
        )
        self.batch_interrupt_btn.pack(side="left")
        self.batch_interrupt_btn.config(state="disabled")  # 初始禁用
        
        # 保存按钮引用到gui_app
        self.gui_app.batch_button = self.batch_execute_btn
        self.gui_app.batch_interrupt_button = self.batch_interrupt_btn
    
    def _detect_device(self):
        """检测设备连接状态"""
        self.device_indicator.config(fg=MODERN_COLORS['warning_status'])
        self.device_status_label.config(text="正在检测...", fg=MODERN_COLORS['warning_status'])
        
        # 调用设备管理器的检测设备方法
        if hasattr(self.gui_app, 'device_manager'):
            # 使用after方法确保UI更新，然后异步检测设备
            self.gui_app.root.after(100, self._do_device_detection)
        else:
            # 模拟检测结果
            self.gui_app.root.after(1000, lambda: self._update_device_status("未找到设备", False))
    
    def _do_device_detection(self):
        """执行设备检测"""
        try:
            # 调用设备管理器检测设备
            device_info = self.gui_app.device_manager.check_device()
            if device_info and "已连接" in device_info:
                self._update_device_status(device_info, True)
            else:
                self._update_device_status("未连接设备", False)
        except Exception as e:
            self._update_device_status(f"检测失败: {str(e)}", False)
    
    def _update_device_status(self, status_text, is_connected):
        """更新设备状态显示"""
        if is_connected:
            self.device_indicator.config(fg=MODERN_COLORS['connected'])
            self.device_status_label.config(text=status_text, fg=MODERN_COLORS['connected'])
        else:
            self.device_indicator.config(fg=MODERN_COLORS['disconnected'])
            self.device_status_label.config(text=status_text, fg=MODERN_COLORS['disconnected'])
    
    def _create_excel_selection(self, parent):
        """创建现代化Excel文件选择区域"""
        excel_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
        excel_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        excel_frame.columnconfigure(1, weight=1)
        
        # 文件图标和标签
        tk.Label(
            excel_frame,
            text="📄",
            font=("Arial", 16),
            bg=MODERN_COLORS['bg_secondary'],
            fg=MODERN_COLORS['primary']
        ).grid(row=0, column=0, padx=(0, 10))
        
        # Excel文件路径
        self.gui_app.excel_path_var = tk.StringVar(value="验收通过数据/标贝采集需求.xlsx")
        self.gui_app.excel_entry = tk.Entry(
            excel_frame,
            textvariable=self.gui_app.excel_path_var,
            state="readonly",
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark'],
            relief="solid",
            bd=1
        )
        self.gui_app.excel_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), ipady=6)
        
        # 浏览按钮
        browse_btn = create_icon_button(
            excel_frame,
            icon="📁",
            text="浏览",
            command=self._browse_excel_file,
            style_type="secondary"
        )
        browse_btn.grid(row=0, column=2, padx=(0, 10))
        
        # 刷新按钮
        refresh_btn = create_icon_button(
            excel_frame,
            icon="🔄",
            text="刷新",
            command=self._refresh_excel_info,
            style_type="secondary"
        )
        refresh_btn.grid(row=0, column=3)
    
    def _create_sheet_selection(self, parent):
        """创建现代化Sheet选择区域"""
        # Sheet选择标题
        header_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
        header_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="📋",
            font=("Arial", 16),
            bg=MODERN_COLORS['bg_secondary'],
            fg=MODERN_COLORS['primary']
        ).pack(side="left", padx=(0, 8))
        
        tk.Label(
            header_frame,
            text="工作表选择",
            font=("Arial", 11, "bold"),
            bg=MODERN_COLORS['bg_secondary'],
            fg=MODERN_COLORS['dark']
        ).pack(side="left")
        
        # 创建滚动区域用于sheet选择
        sheets_scroll_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
        sheets_scroll_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        sheets_scroll_frame.columnconfigure(0, weight=1)
        
        self.gui_app.sheets_container = tk.Frame(sheets_scroll_frame, bg=MODERN_COLORS['bg_secondary'])
        self.gui_app.sheets_container.grid(row=0, column=0, sticky="ew")
        
        # Sheet选择变量
        self.gui_app.sheet_vars = {}
        self.gui_app.available_sheets = []
        
        # 全选/取消全选按钮
        select_buttons_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
        select_buttons_frame.grid(row=4, column=0, sticky="w", pady=(0, 15))
        
        select_all_btn = create_icon_button(
            select_buttons_frame,
            icon="✅",
            text="全选",
            command=self._select_all_sheets,
            style_type="secondary"
        )
        select_all_btn.pack(side="left", padx=(0, 10))
        
        deselect_all_btn = create_icon_button(
            select_buttons_frame,
            icon="❌",
            text="取消全选",
            command=self._deselect_all_sheets,
            style_type="secondary"
        )
        deselect_all_btn.pack(side="left")
    
    def _create_column_selection(self, parent):
        """创建现代化列选择区域"""
        # 列选择标题
        header_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
        header_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="📊",
            font=("Arial", 16),
            bg=MODERN_COLORS['bg_secondary'],
            fg=MODERN_COLORS['primary']
        ).pack(side="left", padx=(0, 8))
        
        tk.Label(
            header_frame,
            text="数据列选择",
            font=("Arial", 11, "bold"),
            bg=MODERN_COLORS['bg_secondary'],
            fg=MODERN_COLORS['dark']
        ).pack(side="left")
        
        # 列名选择框架
        columns_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'])
        columns_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        columns_frame.columnconfigure(1, weight=1)
        
        # 列选择组合框
        self.gui_app.column_var = tk.StringVar(value="示例query")
        self.gui_app.column_combo = ttk.Combobox(
            columns_frame,
            textvariable=self.gui_app.column_var,
            state="readonly",
            font=("Arial", 10),
            width=25
        )
        self.gui_app.column_combo.grid(row=0, column=0, sticky="w", ipady=4)
    

    
    def _execute_single_task(self):
        """执行单个任务"""
        task_query = self.gui_app.task_entry.get().strip()
        if not task_query:
            messagebox.showwarning("警告", "请输入任务描述！")
            return
        
        if hasattr(self.gui_app, 'task_manager'):
            success = self.gui_app.task_manager.execute_single_task(task_query)
            if not success:
                messagebox.showwarning("警告", "任务无法启动，请检查配置或等待当前任务完成！")
        else:
            messagebox.showerror("错误", "任务管理器未初始化！")
    
    def _execute_batch_tasks(self):
        """执行批量任务"""
        excel_path = self.gui_app.excel_path_var.get()
        if not excel_path or not os.path.exists(excel_path):
            messagebox.showwarning("警告", "请选择有效的Excel文件！")
            return
        
        # 获取选中的sheets
        selected_sheets = [sheet for sheet, var in self.gui_app.sheet_vars.items() if var.get()]
        if not selected_sheets:
            messagebox.showwarning("警告", "请选择至少一个Sheet！")
            return
        
        # 获取选择的列名
        target_column = self.gui_app.column_var.get()
        if not target_column:
            messagebox.showwarning("警告", "请选择要处理的列！")
            return
        
        # 确认执行
        confirmation_msg = f"将执行以下任务：\n" \
                         f"• Sheets: {', '.join(selected_sheets)}\n" \
                         f"• 处理列: {target_column}\n" \
                         f"• 总计: {len(selected_sheets)} 个Sheet\n\n" \
                         f"确认继续？"
        if not messagebox.askyesno("确认执行", confirmation_msg):
            return
        
        if hasattr(self.gui_app, 'task_manager'):
            success = self.gui_app.task_manager.execute_batch_tasks(excel_path, selected_sheets, target_column)
            if not success:
                messagebox.showwarning("警告", "批量任务无法启动，请检查配置或等待当前任务完成！")
        else:
            messagebox.showerror("错误", "任务管理器未初始化！")
    
    def _browse_excel_file(self):
        """浏览Excel文件"""
        filename = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.gui_app.excel_path_var.set(filename)
            # 自动刷新Excel信息
            self._refresh_excel_info()
    
    def _refresh_excel_info(self):
        """刷新Excel文件信息，读取sheets和列名"""
        excel_path = self.gui_app.excel_path_var.get()
        if not excel_path or not os.path.exists(excel_path):
            self.gui_app._log_output("⚠️ Excel文件不存在，无法刷新信息")
            return
        
        try:
            self.gui_app._log_output(f"📊 正在读取Excel文件: {os.path.basename(excel_path)}")
            
            # 读取Excel文件的sheet名称
            excel_file = pd.ExcelFile(excel_path)
            self.gui_app.available_sheets = excel_file.sheet_names
            
            # 清除现有的sheet复选框
            for widget in self.gui_app.sheets_container.winfo_children():
                widget.destroy()
            
            # 重新创建sheet复选框
            self.gui_app.sheet_vars = {}
            for i, sheet in enumerate(self.gui_app.available_sheets):
                var = tk.BooleanVar(value=True)
                self.gui_app.sheet_vars[sheet] = var
                cb = ttk.Checkbutton(self.gui_app.sheets_container, text=sheet, variable=var)
                cb.grid(row=i//3, column=i%3, sticky="w", padx=(0, 20), pady=2)
            
            # 读取第一个sheet的列名
            if self.gui_app.available_sheets:
                first_sheet = excel_file.parse(self.gui_app.available_sheets[0], nrows=0)
                columns = list(first_sheet.columns)
                
                # 更新列名下拉框
                self.gui_app.column_combo['values'] = columns
                
                # 自动选择包含"query"的列
                query_columns = [col for col in columns if 'query' in col.lower()]
                if query_columns:
                    self.gui_app.column_var.set(query_columns[0])
                elif columns:
                    self.gui_app.column_var.set(columns[0])
            
            self.gui_app._log_output(f"✅ 发现 {len(self.gui_app.available_sheets)} 个Sheet: {', '.join(self.gui_app.available_sheets)}")
            
        except Exception as e:
            self.gui_app._log_output(f"❌ 读取Excel文件失败: {e}")
            messagebox.showerror("错误", f"读取Excel文件失败:\n{e}")
    
    def _select_all_sheets(self):
        """全选所有sheets"""
        for var in self.gui_app.sheet_vars.values():
            var.set(True)
        self.gui_app._log_output("✅ 已全选所有Sheets")
    
    def _deselect_all_sheets(self):
        """取消全选所有sheets"""
        for var in self.gui_app.sheet_vars.values():
            var.set(False)
        self.gui_app._log_output("❌ 已取消全选所有Sheets")
    

    
    def grid(self, **kwargs):
        """网格布局"""
        if self.frame:
            self.frame.grid(**kwargs)
    
    def _interrupt_task(self):
        """中断当前任务"""
        if hasattr(self.gui_app, 'task_manager'):
            success = self.gui_app.task_manager.cancel_current_task()
            if not success:
                messagebox.showinfo("提示", "当前没有正在执行的任务")
        else:
            messagebox.showerror("错误", "任务管理器未初始化！")
    
    def _interrupt_batch_task(self):
        """中断批量任务"""
        if hasattr(self.gui_app, 'task_manager'):
            success = self.gui_app.task_manager.cancel_current_task()
            if success:
                messagebox.showinfo("提示", "已向批量任务发送中断信号，请等待当前子任务完成...")
            else:
                messagebox.showinfo("提示", "当前没有正在执行的批量任务")
        else:
            messagebox.showerror("错误", "任务管理器未初始化！")
    
    def _update_task_buttons(self, task_running):
        """更新任务相关按钮的显示状态"""
        if task_running:
            # 任务运行时：禁用执行按钮，启用中断按钮
            if hasattr(self.gui_app, 'execute_button'):
                self.gui_app.execute_button.config(state="disabled")
            if hasattr(self.gui_app, 'batch_button'):
                self.gui_app.batch_button.config(state="disabled")
            if hasattr(self.gui_app, 'interrupt_button'):
                self.gui_app.interrupt_button.config(state="normal")
            if hasattr(self.gui_app, 'batch_interrupt_button'):
                self.gui_app.batch_interrupt_button.config(state="normal")
        else:
            # 任务完成时：启用执行按钮，禁用中断按钮
            if hasattr(self.gui_app, 'execute_button'):
                self.gui_app.execute_button.config(state="normal")
            if hasattr(self.gui_app, 'batch_button'):
                self.gui_app.batch_button.config(state="normal")
            if hasattr(self.gui_app, 'interrupt_button'):
                self.gui_app.interrupt_button.config(state="disabled")
            if hasattr(self.gui_app, 'batch_interrupt_button'):
                self.gui_app.batch_interrupt_button.config(state="disabled")
    
    def get_buttons(self):
        """获取按钮列表（用于状态控制）"""
        buttons = []
        if hasattr(self.gui_app, 'execute_button'):
            buttons.append(self.gui_app.execute_button)
        if hasattr(self.gui_app, 'batch_button'):
            buttons.append(self.gui_app.batch_button)
        if hasattr(self.gui_app, 'interrupt_button'):
            buttons.append(self.gui_app.interrupt_button)
        if hasattr(self.gui_app, 'batch_interrupt_button'):
            buttons.append(self.gui_app.batch_interrupt_button)
        return buttons 