#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# 添加src模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.logger_config import get_logger

from src.config import config
from src.gui_config import gui_config
from ..utils.validators import (
    validate_api_key, validate_device_id, validate_max_steps
)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, gui_app):
        self.gui_app = gui_app
        self.logger = get_logger("config_manager")
        
    def load_config(self):
        """加载配置"""
        try:
            # 从GUI配置管理器加载配置
            self.gui_app.output_dir_var.set(gui_config.get("output_dir", "output"))
            self.gui_app.batch_output_dir_var.set(gui_config.get("batch_output_dir", "batch_output"))
            self.gui_app.api_key_var.set(gui_config.get("api_key", config.dashscope_api_key or ""))
            self.gui_app.max_steps_var.set(str(gui_config.get("max_execution_times", config.max_execution_times)))
            self.gui_app.privacy_enabled_var.set(gui_config.get("privacy_enabled", config.privacy_protection.get("enabled", True)))
            self.gui_app.device_id_var.set(gui_config.get("device_id", ""))
            self.gui_app.excel_path_var.set(gui_config.get("excel_file", "验收通过数据/标贝采集需求.xlsx"))
            
            # 设置任务输入框
            self.gui_app.task_entry.delete(0, tk.END)
            self.gui_app.task_entry.insert(0, gui_config.get("last_task", "在京东上查快递"))
            
            self.gui_app.column_var.set(gui_config.get("target_column", "示例query"))
            
            # 设置窗口大小
            geometry = gui_config.get("window_geometry", "1200x800")
            self.gui_app.root.geometry(geometry)
            
            # 加载应用包名映射
            self._load_app_packages()
            
            self.logger.success("✅ 配置加载完成")
            return True
            
        except Exception as e:
            self.logger.error("❌ 配置加载失败: {e}")
            return False
    
    def save_config(self):
        """保存配置"""
        try:
            # 验证配置
            if not self._validate_config():
                return False
            
            # 收集当前设置
            current_config = {
                "output_dir": self.gui_app.output_dir_var.get(),
                "batch_output_dir": self.gui_app.batch_output_dir_var.get(),
                "api_key": self.gui_app.api_key_var.get(),
                "max_execution_times": int(self.gui_app.max_steps_var.get() or 50),
                "privacy_enabled": self.gui_app.privacy_enabled_var.get(),
                "device_id": self.gui_app.device_id_var.get(),
                "excel_file": self.gui_app.excel_path_var.get(),
                "selected_sheets": [sheet for sheet, var in self.gui_app.sheet_vars.items() if var.get()],
                "target_column": self.gui_app.column_var.get(),
                "window_geometry": self.gui_app.root.geometry(),
                "last_task": self.gui_app.task_entry.get(),
                "app_packages": self.gui_app.app_packages.copy()
            }
            
            # 更新GUI配置
            gui_config.update(current_config)
            
            # 同时更新系统config对象
            config.dashscope_api_key = self.gui_app.api_key_var.get()
            config.max_execution_times = int(self.gui_app.max_steps_var.get() or 50)
            config.device_id = self.gui_app.device_id_var.get()
            
            # 更新系统config的应用包名映射
            config.app_packages.update(self.gui_app.app_packages)
            
            # 保存到文件
            if gui_config.save_config():
                self.logger.success("✅ 配置保存成功")
                messagebox.showinfo("成功", "配置已保存！")
                return True
            else:
                raise Exception("配置文件保存失败")
                
        except Exception as e:
            self.logger.error("❌ 配置保存失败: {e}")
            messagebox.showerror("错误", f"配置保存失败: {e}")
            return False
    
    def _validate_config(self):
        """验证配置"""
        # 验证API Key
        api_key = self.gui_app.api_key_var.get()
        is_valid, msg = validate_api_key(api_key)
        if not is_valid:
            messagebox.showerror("配置错误", f"API Key验证失败: {msg}")
            return False
        
        # 验证最大执行次数
        max_steps = self.gui_app.max_steps_var.get()
        is_valid, msg = validate_max_steps(max_steps)
        if not is_valid:
            messagebox.showerror("配置错误", f"最大执行次数验证失败: {msg}")
            return False
        
        # 隐私保护配置无需验证，布尔值总是有效的
        
        return True
    
    def _load_app_packages(self):
        """加载应用包名映射"""
        try:
            # 首先从config模块加载默认值
            self.gui_app.app_packages = config.app_packages.copy()
            
            # 然后从GUI配置中加载自定义值
            saved_packages = gui_config.get("app_packages", {})
            if saved_packages:
                self.gui_app.app_packages.update(saved_packages)
            
            # 更新显示（如果组件已存在）
            if hasattr(self.gui_app, 'config_panel'):
                self.gui_app.config_panel.update_app_package_tree()
            
        except Exception as e:
            self.logger.error("❌ 加载应用包名映射失败: {e}")
    
    def reset_config(self):
        """重置配置为默认值"""
        try:
            # 重置GUI配置为默认值
            gui_config.reset_to_defaults()
            
            # 重新加载配置
            self.load_config()
            
            self.logger.info("🔄 配置已重置为默认值")
            messagebox.showinfo("成功", "配置已重置为默认值！")
            
        except Exception as e:
            self.logger.error("❌ 重置配置失败: {e}")
            messagebox.showerror("错误", f"重置配置失败: {e}")
    
    def export_config(self, file_path):
        """导出配置到文件"""
        try:
            current_config = {
                "output_dir": self.gui_app.output_dir_var.get(),
                "api_key": self.gui_app.api_key_var.get(),
                "max_execution_times": int(self.gui_app.max_steps_var.get() or 50),
                "device_id": self.gui_app.device_id_var.get(),
                "excel_file": self.gui_app.excel_path_var.get(),
                "target_column": self.gui_app.column_var.get(),
                "last_task": self.gui_app.task_entry.get(),
                "app_packages": self.gui_app.app_packages.copy()
            }
            
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=2, ensure_ascii=False)
            
            self.logger.success("✅ 配置已导出到: {file_path}")
            messagebox.showinfo("成功", f"配置已导出到:\n{file_path}")
            
        except Exception as e:
            self.logger.error("❌ 导出配置失败: {e}")
            messagebox.showerror("错误", f"导出配置失败: {e}")
    
    def import_config(self, file_path):
        """从文件导入配置"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 更新GUI组件
            self.gui_app.output_dir_var.set(imported_config.get("output_dir", "output"))
            self.gui_app.api_key_var.set(imported_config.get("api_key", ""))
            self.gui_app.max_steps_var.set(str(imported_config.get("max_execution_times", 50)))
            self.gui_app.device_id_var.set(imported_config.get("device_id", ""))
            self.gui_app.excel_path_var.set(imported_config.get("excel_file", ""))
            self.gui_app.column_var.set(imported_config.get("target_column", "示例query"))
            
            # 更新任务输入框
            self.gui_app.task_entry.delete(0, tk.END)
            self.gui_app.task_entry.insert(0, imported_config.get("last_task", ""))
            
            # 更新应用包名映射
            imported_packages = imported_config.get("app_packages", {})
            if imported_packages:
                self.gui_app.app_packages.update(imported_packages)
                if hasattr(self.gui_app, 'config_panel'):
                    self.gui_app.config_panel.update_app_package_tree()
            
            self.logger.success("✅ 配置已从文件导入: {file_path}")
            messagebox.showinfo("成功", f"配置已从文件导入:\n{file_path}")
            
        except Exception as e:
            self.logger.error("❌ 导入配置失败: {e}")
            messagebox.showerror("错误", f"导入配置失败: {e}")
    
    def auto_save_config(self):
        """自动保存配置（退出时调用）"""
        try:
            current_config = {
                "output_dir": self.gui_app.output_dir_var.get(),
                "api_key": self.gui_app.api_key_var.get(),
                "max_execution_times": int(self.gui_app.max_steps_var.get() or 50),
                "device_id": self.gui_app.device_id_var.get(),
                "excel_file": self.gui_app.excel_path_var.get(),
                "selected_sheets": [sheet for sheet, var in self.gui_app.sheet_vars.items() if var.get()],
                "target_column": self.gui_app.column_var.get(),
                "window_geometry": self.gui_app.root.geometry(),
                "last_task": self.gui_app.task_entry.get(),
                "app_packages": self.gui_app.app_packages.copy()
            }
            
            gui_config.update(current_config)
            gui_config.save_config()
            
            return True
            
        except Exception as e:
            self.logger.warning("⚠️ 自动保存配置失败: {e}")
            return False 