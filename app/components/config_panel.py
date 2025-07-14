#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置面板组件
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
import subprocess
from ..utils.ui_helpers import open_url, create_custom_button
from ..dialogs.common_apps_dialog import CommonAppsDialog


class ConfigPanel:
    """配置面板组件"""
    
    def __init__(self, parent, gui_app):
        self.parent = parent
        self.gui_app = gui_app
        self.frame = None
        
        # 创建配置面板
        self._create_config_panel()
    
    def _create_config_panel(self):
        """创建配置面板"""
        # 使用tk.LabelFrame替代ttk.LabelFrame以确保白色背景
        self.frame = tk.LabelFrame(self.parent, text="⚙️ 配置管理", 
                                   bg="#FFFFFF", fg="#333333", 
                                   font=("Arial", 11, "bold"),
                                   relief="solid", bd=1, padx=10, pady=10)
        self.frame.columnconfigure(0, weight=1)
        
        # 输出目录配置
        self._create_output_settings()
        
        # AI模型配置
        self._create_ai_settings()
        
        # 隐私保护配置
        self._create_privacy_settings()
        
        # 应用包名配置
        self._create_app_package_settings()
        
        # 定制按钮区域
        self._create_custom_buttons()
        
        # 配置按钮
        self._create_config_buttons()
        
        # 帮助信息
        self._create_help_section()
    
    def _create_output_settings(self):
        """创建输出设置区域"""
        output_frame = tk.LabelFrame(self.frame, text="📁 输出设置", 
                                     bg="#FFFFFF", fg="#333333", 
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        output_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        # 单个任务输出目录
        ttk.Label(output_frame, text="单个任务输出:").grid(row=0, column=0, sticky="w")
        self.gui_app.output_dir_var = tk.StringVar(value="output")
        self.gui_app.output_entry = ttk.Entry(output_frame, textvariable=self.gui_app.output_dir_var)
        self.gui_app.output_entry.grid(row=0, column=1, sticky="ew", padx=(10, 5))
        
        ttk.Button(
            output_frame, 
            text="📁", 
            command=self._browse_output_dir,
            style="Config.TButton"
        ).grid(row=0, column=2)
        
        # 批量任务输出目录
        ttk.Label(output_frame, text="批量任务输出:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.gui_app.batch_output_dir_var = tk.StringVar(value="batch_output")
        self.gui_app.batch_output_entry = ttk.Entry(output_frame, textvariable=self.gui_app.batch_output_dir_var)
        self.gui_app.batch_output_entry.grid(row=1, column=1, sticky="ew", padx=(10, 5), pady=(10, 0))
        
        ttk.Button(
            output_frame, 
            text="📁", 
            command=self._browse_batch_output_dir,
            style="Config.TButton"
        ).grid(row=1, column=2, pady=(10, 0))
        
        # 输出设置说明
        info_label = ttk.Label(
            output_frame,
            text="💡 单个任务输出: 存放单次执行的结果\n💡 批量任务输出: 存放批量执行的结果",
            font=("Arial", 8),
            foreground="#666666",
            justify="left"
        )
        info_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))
    
    def _create_ai_settings(self):
        """创建AI模型设置区域"""
        ai_frame = tk.LabelFrame(self.frame, text="AI模型设置", 
                                 bg="#FFFFFF", fg="#333333", 
                                 font=("Arial", 10, "bold"), padx=10, pady=10)
        ai_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ai_frame.columnconfigure(1, weight=1)
        
        ttk.Label(ai_frame, text="API Key:").grid(row=0, column=0, sticky="w")
        self.gui_app.api_key_var = tk.StringVar()
        api_entry = ttk.Entry(ai_frame, textvariable=self.gui_app.api_key_var, show="*")
        api_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
        
        ttk.Label(ai_frame, text="最大执行次数:").grid(row=1, column=0, sticky="w")
        self.gui_app.max_steps_var = tk.StringVar()
        max_steps_entry = ttk.Entry(ai_frame, textvariable=self.gui_app.max_steps_var, width=10)
        max_steps_entry.grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # 初始化设备ID变量
        self.gui_app.device_id_var = tk.StringVar()
    
    def _create_privacy_settings(self):
        """创建隐私保护设置区域"""
        privacy_frame = tk.LabelFrame(self.frame, text="🔐 隐私保护", 
                                      bg="#FFFFFF", fg="#333333", 
                                      font=("Arial", 10, "bold"), padx=10, pady=10)
        privacy_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        privacy_frame.columnconfigure(0, weight=1)
        
        # 启用隐私保护选项
        self.gui_app.privacy_enabled_var = tk.BooleanVar(value=True)
        privacy_check = ttk.Checkbutton(
            privacy_frame, 
            text="🛡️ 启用隐私保护 (电话号码假名化)",
            variable=self.gui_app.privacy_enabled_var,
            style="Config.TCheckbutton"
        )
        privacy_check.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # 隐私保护说明
        privacy_info = ttk.Label(
            privacy_frame,
            text="隐私保护功能将自动检测手机号并假名化",
            font=("Arial", 9),
            foreground="gray",
            wraplength=300
        )
        privacy_info.grid(row=1, column=0, sticky="w")
    
    def _create_app_package_settings(self):
        """创建应用包名配置区域"""
        app_package_frame = tk.LabelFrame(self.frame, text="应用包名映射", 
                                          bg="#FFFFFF", fg="#333333", 
                                          font=("Arial", 10, "bold"), padx=10, pady=10)
        app_package_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        app_package_frame.columnconfigure(0, weight=1)
        
        # 添加新映射区域
        self._create_add_mapping_section(app_package_frame)
        
        # 现有映射列表区域
        self._create_mapping_list_section(app_package_frame)
        
        # 操作按钮区域
        self._create_mapping_buttons_section(app_package_frame)
    
    def _create_add_mapping_section(self, parent):
        """创建添加映射区域"""
        add_frame = ttk.Frame(parent)
        add_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=1)
        
        ttk.Label(add_frame, text="应用名:").grid(row=0, column=0, sticky="w")
        self.gui_app.new_app_name_var = tk.StringVar()
        app_name_entry = ttk.Entry(add_frame, textvariable=self.gui_app.new_app_name_var, width=15)
        app_name_entry.grid(row=0, column=1, sticky="ew", padx=(5, 10))
        
        ttk.Label(add_frame, text="包名:").grid(row=0, column=2, sticky="w")
        self.gui_app.new_package_name_var = tk.StringVar()
        package_name_entry = ttk.Entry(add_frame, textvariable=self.gui_app.new_package_name_var, width=25)
        package_name_entry.grid(row=0, column=3, sticky="ew", padx=(5, 10))
        
        ttk.Button(
            add_frame, 
            text="➕ 添加", 
            command=self._add_app_package,
            style="Config.TButton"
        ).grid(row=0, column=4, padx=(5, 0))
    
    def _create_mapping_list_section(self, parent):
        """创建映射列表区域"""
        list_frame = tk.LabelFrame(parent, text="现有映射", 
                                   bg="#FFFFFF", fg="#333333", 
                                   font=("Arial", 9, "bold"), padx=5, pady=5)
        list_frame.grid(row=1, column=0, sticky="ew")
        list_frame.columnconfigure(0, weight=1)
        
        # 创建Treeview显示现有映射
        columns = ('app_name', 'package_name')
        self.gui_app.app_package_tree = ttk.Treeview(
            list_frame, 
            columns=columns, 
            show='headings', 
            height=6
        )
        self.gui_app.app_package_tree.heading('app_name', text='应用名')
        self.gui_app.app_package_tree.heading('package_name', text='包名')
        self.gui_app.app_package_tree.column('app_name', width=120)
        self.gui_app.app_package_tree.column('package_name', width=250)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            list_frame, 
            orient="vertical", 
            command=self.gui_app.app_package_tree.yview
        )
        self.gui_app.app_package_tree.configure(yscrollcommand=scrollbar.set)
        
        self.gui_app.app_package_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 绑定双击事件用于编辑
        self.gui_app.app_package_tree.bind('<Double-1>', self._on_app_package_double_click)
    
    def _create_mapping_buttons_section(self, parent):
        """创建映射操作按钮区域"""
        delete_button_frame = ttk.Frame(parent)
        delete_button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(
            delete_button_frame, 
            text="🗑️ 删除选中", 
            command=self._delete_selected_app_package,
            style="Config.TButton"
        ).grid(row=0, column=0)
        
        ttk.Button(
            delete_button_frame, 
            text="🔄 重置为默认", 
            command=self._reset_app_packages,
            style="Config.TButton"
        ).grid(row=0, column=1, padx=(10, 0))
        
        # 添加常用应用快速添加按钮
        ttk.Button(
            delete_button_frame, 
            text="📱 常用应用", 
            command=self._show_common_apps,
            style="Config.TButton"
        ).grid(row=0, column=2, padx=(10, 0))
        
        # 初始化应用包名映射数据
        self.gui_app.app_packages = {}
    
    def _create_custom_buttons(self):
        """创建定制按钮区域"""
        custom_frame = tk.LabelFrame(self.frame, text="🛠️ 快捷工具", 
                                     bg="#FFFFFF", fg="#333333", 
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        custom_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        custom_frame.columnconfigure(0, weight=1)
        custom_frame.columnconfigure(1, weight=1)
        custom_frame.columnconfigure(2, weight=1)
        
        # 第一行按钮
        row1_frame = ttk.Frame(custom_frame)
        row1_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        row1_frame.columnconfigure(0, weight=1)
        row1_frame.columnconfigure(1, weight=1)
        row1_frame.columnconfigure(2, weight=1)
        
        ttk.Button(
            row1_frame,
            text="📂 打开单个输出",
            command=self._open_single_output,
            style="Config.TButton"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        ttk.Button(
            row1_frame,
            text="📊 打开批量输出",
            command=self._open_batch_output,
            style="Config.TButton"
        ).grid(row=0, column=1, sticky="ew", padx=5)
        
        clean_button = create_custom_button(
            row1_frame,
            text="🗑️ 清理输出目录",
            command=self._clean_output_dirs,
            style_type="warning"
        )
        clean_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        
        # 第二行按钮
        row2_frame = ttk.Frame(custom_frame)
        row2_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(5, 5))
        row2_frame.columnconfigure(0, weight=1)
        row2_frame.columnconfigure(1, weight=1)
        row2_frame.columnconfigure(2, weight=1)
        
        ttk.Button(
            row2_frame,
            text="🔍 检查设备",
            command=self._check_device,
            style="Config.TButton"
        ).grid(row=0, column=1, sticky="ew", padx=5)
        
        # 第三行按钮
        row3_frame = ttk.Frame(custom_frame)
        row3_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        row3_frame.columnconfigure(0, weight=1)
        row3_frame.columnconfigure(1, weight=1)
        row3_frame.columnconfigure(2, weight=1)
        
        ttk.Button(
            row3_frame,
            text="📤 导出配置",
            command=self._export_config,
            style="Config.TButton"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        ttk.Button(
            row3_frame,
            text="📥 导入配置",
            command=self._import_config,
            style="Config.TButton"
        ).grid(row=0, column=1, sticky="ew", padx=5)
    
    def _create_config_buttons(self):
        """创建配置按钮区域"""
        config_buttons_frame = ttk.Frame(self.frame)
        config_buttons_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        config_buttons_frame.columnconfigure(0, weight=1)
        config_buttons_frame.columnconfigure(1, weight=1)
        
        ttk.Button(
            config_buttons_frame, 
            text="💾 保存配置", 
            command=self._save_config,
            style="Success.TButton"
        ).grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        ttk.Button(
            config_buttons_frame, 
            text="🔄 重置配置", 
            command=self._reset_config,
            style="Warning.TButton"
        ).grid(row=0, column=1, padx=(10, 0), sticky="ew")
    
    def _create_help_section(self):
        """创建帮助信息区域"""
        help_frame = tk.LabelFrame(self.frame, text="📖 帮助信息", 
                                   bg="#FFFFFF", fg="#333333", 
                                   font=("Arial", 10, "bold"), padx=10, pady=10)
        help_frame.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        
        help_text = """
📖 使用说明:
• 确保Android设备已连接并开启USB调试
• 配置DASHSCOPE API Key用于AI分析
• 单个任务: 输入任务描述后点击执行
• 批量任务: 选择Excel文件和目标Sheets
• 应用包名: 管理应用名称与包名的映射关系
        """
        ttk.Label(
            help_frame, 
            text=help_text, 
            justify="left", 
            font=("Arial", 9)
        ).grid(row=0, column=0, sticky="w")
        
        # 链接按钮
        links_frame = ttk.Frame(help_frame)
        links_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(
            links_frame, 
            text="📚 使用文档", 
            command=lambda: open_url("https://github.com"),
            style="Config.TButton"
        ).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(
            links_frame, 
            text="🐛 反馈问题", 
            command=lambda: open_url("https://github.com/issues"),
            style="Config.TButton"
        ).grid(row=0, column=1)
    
    def _browse_output_dir(self):
        """浏览输出目录"""
        dirname = filedialog.askdirectory(title="选择单个任务输出目录")
        if dirname:
            self.gui_app.output_dir_var.set(dirname)
    
    def _browse_batch_output_dir(self):
        """浏览批量输出目录"""
        dirname = filedialog.askdirectory(title="选择批量任务输出目录")
        if dirname:
            self.gui_app.batch_output_dir_var.set(dirname)
    
    def _add_app_package(self):
        """添加新的应用包名映射"""
        app_name = self.gui_app.new_app_name_var.get().strip()
        package_name = self.gui_app.new_package_name_var.get().strip()
        
        if not app_name or not package_name:
            messagebox.showwarning("警告", "请输入完整的应用名和包名！")
            return
        
        # 检查是否已存在
        if app_name in self.gui_app.app_packages:
            if not messagebox.askyesno("确认", f"应用 '{app_name}' 已存在，是否覆盖？"):
                return
        
        # 添加映射
        self.gui_app.app_packages[app_name] = package_name
        
        # 更新显示
        self.update_app_package_tree()
        
        # 清空输入框
        self.gui_app.new_app_name_var.set("")
        self.gui_app.new_package_name_var.set("")
        
        self.gui_app._log_output(f"✅ 已添加应用映射: {app_name} -> {package_name}")
    
    def _delete_selected_app_package(self):
        """删除选中的应用包名映射"""
        selected_items = self.gui_app.app_package_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的映射！")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认", f"确定要删除选中的 {len(selected_items)} 个映射吗？"):
            return
        
        # 删除选中的映射
        for item in selected_items:
            app_name = self.gui_app.app_package_tree.item(item)['values'][0]
            if app_name in self.gui_app.app_packages:
                del self.gui_app.app_packages[app_name]
                self.gui_app._log_output(f"🗑️ 已删除应用映射: {app_name}")
        
        # 更新显示
        self.update_app_package_tree()
    
    def _reset_app_packages(self):
        """重置应用包名映射为默认值"""
        if not messagebox.askyesno("确认", "确定要重置为默认的应用包名映射吗？这将覆盖所有自定义设置。"):
            return
        
        # 从config模块获取默认映射
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
        from src.config import config
        
        self.gui_app.app_packages = config.app_packages.copy()
        
        # 更新显示
        self.update_app_package_tree()
        
        self.gui_app._log_output("🔄 应用包名映射已重置为默认值")
    
    def update_app_package_tree(self):
        """更新应用包名映射的显示"""
        # 清空现有项目
        for item in self.gui_app.app_package_tree.get_children():
            self.gui_app.app_package_tree.delete(item)
        
        # 添加所有映射
        for app_name, package_name in sorted(self.gui_app.app_packages.items()):
            self.gui_app.app_package_tree.insert('', 'end', values=(app_name, package_name))
    
    def _on_app_package_double_click(self, event):
        """处理应用包名映射的双击编辑事件"""
        selected_items = self.gui_app.app_package_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = self.gui_app.app_package_tree.item(item)['values']
        if len(values) >= 2:
            app_name = values[0]
            package_name = values[1]
            
            # 填充到输入框中进行编辑
            self.gui_app.new_app_name_var.set(app_name)
            self.gui_app.new_package_name_var.set(package_name)
            
            self.gui_app._log_output(f"📝 双击编辑: {app_name} -> {package_name}")
            self.gui_app._log_output("💡 修改后点击'➕ 添加'按钮即可更新映射")
    
    def _show_common_apps(self):
        """显示常用应用列表供快速添加"""
        try:
            dialog = CommonAppsDialog(self.gui_app.root, self.gui_app)
            dialog.show()
        except Exception as e:
            self.gui_app._log_output(f"❌ 打开常用应用对话框失败: {e}")
            messagebox.showerror("错误", f"打开常用应用对话框失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        if hasattr(self.gui_app, 'config_manager'):
            self.gui_app.config_manager.save_config()
        else:
            self.gui_app._log_output("❌ 配置管理器未初始化")
    
    def _reset_config(self):
        """重置配置"""
        if hasattr(self.gui_app, 'config_manager'):
            self.gui_app.config_manager.load_config()
        else:
            self.gui_app._log_output("❌ 配置管理器未初始化")
    
    def _open_single_output(self):
        """打开单个任务输出目录"""
        output_dir = self.gui_app.output_dir_var.get()
        if output_dir:
            from ..utils.ui_helpers import open_directory
            open_directory(output_dir)
            self.gui_app._log_output(f"📂 已打开单个任务输出目录: {output_dir}")
        else:
            self.gui_app._log_output("⚠️ 单个任务输出目录未设置")
    
    def _open_batch_output(self):
        """打开批量任务输出目录"""
        batch_output_dir = self.gui_app.batch_output_dir_var.get()
        if batch_output_dir:
            from ..utils.ui_helpers import open_directory
            open_directory(batch_output_dir)
            self.gui_app._log_output(f"📊 已打开批量任务输出目录: {batch_output_dir}")
        else:
            self.gui_app._log_output("⚠️ 批量任务输出目录未设置")
    
    def _clean_output_dirs(self):
        """清理输出目录"""
        from tkinter import messagebox
        import shutil
        
        if not messagebox.askyesno("确认清理", "确定要清理所有输出目录吗？这将删除所有历史结果！"):
            return
        
        try:
            cleaned = 0
            # 清理单个任务输出目录
            single_dir = self.gui_app.output_dir_var.get()
            if single_dir and os.path.exists(single_dir):
                shutil.rmtree(single_dir, ignore_errors=True)
                os.makedirs(single_dir, exist_ok=True)
                cleaned += 1
                self.gui_app._log_output(f"🗑️ 已清理单个任务输出目录: {single_dir}")
            
            # 清理批量任务输出目录
            batch_dir = self.gui_app.batch_output_dir_var.get()
            if batch_dir and os.path.exists(batch_dir):
                shutil.rmtree(batch_dir, ignore_errors=True)
                os.makedirs(batch_dir, exist_ok=True)
                cleaned += 1
                self.gui_app._log_output(f"🗑️ 已清理批量任务输出目录: {batch_dir}")
            
            if cleaned > 0:
                self.gui_app._log_output(f"✅ 成功清理 {cleaned} 个输出目录")
                messagebox.showinfo("清理完成", f"成功清理 {cleaned} 个输出目录")
            else:
                self.gui_app._log_output("ℹ️ 没有找到需要清理的目录")
                
        except Exception as e:
            self.gui_app._log_output(f"❌ 清理输出目录失败: {e}")
            messagebox.showerror("清理失败", f"清理输出目录时出错: {e}")
    

    
    def _check_device(self):
        """检查设备连接状态"""
        if hasattr(self.gui_app, 'device_manager'):
            self.gui_app.device_manager.refresh_device_info()
            self.gui_app._log_output("🔍 正在检查设备连接状态...")
        else:
            self.gui_app._log_output("❌ 设备管理器未初始化")
    

    
    def _export_config(self):
        """导出配置"""
        if hasattr(self.gui_app, 'config_manager'):
            from tkinter import filedialog
            from datetime import datetime
            
            filename = filedialog.asksaveasfilename(
                title="导出配置",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile=f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            if filename:
                try:
                    self.gui_app.config_manager.export_config(filename)
                    self.gui_app._log_output(f"📤 配置已导出到: {filename}")
                    messagebox.showinfo("导出成功", f"配置已成功导出到:\n{filename}")
                except Exception as e:
                    self.gui_app._log_output(f"❌ 导出配置失败: {e}")
                    messagebox.showerror("导出失败", f"导出配置时出错: {e}")
        else:
            self.gui_app._log_output("❌ 配置管理器未初始化")
    
    def _import_config(self):
        """导入配置"""
        if hasattr(self.gui_app, 'config_manager'):
            from tkinter import filedialog
            
            filename = filedialog.askopenfilename(
                title="导入配置",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filename:
                try:
                    self.gui_app.config_manager.import_config(filename)
                    self.gui_app._log_output(f"📥 配置已从文件导入: {filename}")
                    messagebox.showinfo("导入成功", f"配置已成功从以下文件导入:\n{filename}")
                except Exception as e:
                    self.gui_app._log_output(f"❌ 导入配置失败: {e}")
                    messagebox.showerror("导入失败", f"导入配置时出错: {e}")
        else:
            self.gui_app._log_output("❌ 配置管理器未初始化")
    

    
    def grid(self, **kwargs):
        """网格布局"""
        if self.frame:
            self.frame.grid(**kwargs) 