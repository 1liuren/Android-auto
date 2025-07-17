#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务管理器
"""

import os
import sys
import threading
import pandas as pd
import json
from datetime import datetime

# 添加src模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.task_executor import TaskExecutor
from src.config import config
from src.logger_config import get_logger
from ..utils.validators import (
    validate_task_description, validate_batch_execution_params
)
from ..utils.ui_helpers import safe_filename


class TaskManager:
    """任务管理器"""
    
    def __init__(self, gui_app):
        self.gui_app = gui_app
        self.current_task = None
        self.task_executor = None
        self.cancel_requested = False
        self.logger = get_logger("task_manager")
        
    def execute_single_task(self, task_query):
        """执行单个任务"""
        # 验证任务描述
        is_valid, msg = validate_task_description(task_query)
        if not is_valid:
            self.logger.error(f"❌ 任务验证失败: {msg}")
            return False
        
        if self.current_task and self.current_task.is_alive():
            self.logger.warning("⚠️ 当前有任务正在执行")
            return False
        
        # 重置中断标志
        self.cancel_requested = False
        
        # 更新UI状态 - 确保在主线程中执行
        self.gui_app.root.after(0, lambda: self.gui_app._set_buttons_state(False))
        self.gui_app.root.after(0, lambda: self.gui_app._update_status("🚀 执行中...", "orange"))
        self.gui_app.root.after(0, lambda: self._update_control_buttons(True))  # 显示中断按钮
        
        # 在新线程中执行任务
        self.current_task = threading.Thread(
            target=self._run_single_task,
            args=(task_query,),
            daemon=True
        )
        self.current_task.start()
        return True
    
    def _run_single_task(self, query):
        """在新线程中运行单个任务"""
        try:
            self.logger.info(f"🚀 开始执行任务: {query}")
            
            # 检查是否被取消
            if self.cancel_requested:
                self.logger.warning("⚠️ 任务已被用户取消")
                self.gui_app._update_status("⚠️ 已取消", "orange")
                return
            
            # 同步前端配置到后端config
            api_key = self.gui_app.api_key_var.get()
            if api_key:
                config.dashscope_api_key = api_key
                self.logger.info("🔑 API Key已从前端同步到后端")
            else:
                self.logger.warning("⚠️ 前端未配置API Key")
            
            # 同步其他配置
            model_name = self.gui_app.model_name_var.get()
            if model_name:
                config.model_name = model_name
                self.logger.info(f"🤖 AI模型已设置为: {model_name}")
            
            max_steps = self.gui_app.max_steps_var.get()
            if max_steps:
                config.max_execution_times = int(max_steps)
            
            device_id = self.gui_app.device_id_var.get()
            if device_id:
                config.device_id = device_id
            
            # 同步多模态增强设置
            multimodal_enabled = self.gui_app.multimodal_enabled_var.get()
            config.multimodal_enhancement["enabled"] = multimodal_enabled
            self.logger.info(f"🔍 多模态增强已设置为: {'启用' if multimodal_enabled else '禁用'}")
            
            # 创建任务执行器
            output_dir = self.gui_app.output_dir_var.get() or "output"
            self.task_executor = TaskExecutor(output_base_dir=output_dir)
            
            # 更新任务执行器的应用包名映射
            config.app_packages.update(self.gui_app.app_packages)
            
            # 执行任务（需要在执行过程中检查中断）
            success = self._execute_with_cancel_check(query)
            
            if self.cancel_requested:
                self.logger.warning("⚠️ 任务执行过程中被取消")
                self.gui_app._update_status("⚠️ 已取消", "orange")
            elif success:
                self.logger.success("✅ 任务执行完成！")
                self.gui_app._update_status("✅ 完成", "green")
                
                # 询问是否打开输出目录
                self.gui_app.root.after(0, lambda: self.gui_app._ask_open_output(self.task_executor.output_dir))
            else:
                self.logger.error("❌ 任务执行失败")
                self.gui_app._update_status("❌ 失败", "red")
                
        except Exception as e:
            self.logger.error(f"❌ 任务执行异常: {e}")
            self.gui_app._update_status("❌ 异常", "red")
        finally:
            # 重新启用按钮，隐藏中断按钮
            self.gui_app.root.after(0, lambda: self._reset_ui_after_task())
    
    def _execute_with_cancel_check(self, query):
        """执行任务并检查取消请求"""
        # 这里应该是一个可以被中断的执行过程
        # 由于TaskExecutor.run_task()是同步的，我们需要在合适的地方检查中断
        # 这是一个简化的实现，实际上可能需要修改TaskExecutor来支持中断
        
        if self.cancel_requested:
            return False
        
        try:
            # 模拟可中断的执行过程
            success = self.task_executor.run_task(query)
            return success and not self.cancel_requested
        except Exception as e:
            if self.cancel_requested:
                self.logger.warning("⚠️ 任务在执行过程中被中断")
                return False
            raise e
    
    def _reset_ui_after_task(self):
        """任务完成后重置UI状态"""
        self.gui_app._set_buttons_state(True)
        self._update_control_buttons(False)  # 隐藏中断按钮
        self.task_executor = None
    
    def _update_control_buttons(self, task_running):
        """更新控制按钮状态"""
        if hasattr(self.gui_app, 'control_panel'):
            self.gui_app.control_panel._update_task_buttons(task_running)
    
    def execute_batch_tasks(self, excel_path, selected_sheets, target_column):
        """执行批量任务"""
        # 验证批量执行参数
        is_valid, msg = validate_batch_execution_params(excel_path, selected_sheets, target_column)
        if not is_valid:
            self.logger.error(f"❌ 批量任务验证失败: {msg}")
            return False
        
        if self.current_task and self.current_task.is_alive():
            self.logger.warning("⚠️ 当前有任务正在执行")
            return False
        
        # 重置中断标志
        self.cancel_requested = False
        
        # 更新UI状态 - 确保在主线程中执行
        self.gui_app.root.after(0, lambda: self.gui_app._set_buttons_state(False))
        self.gui_app.root.after(0, lambda: self.gui_app._update_status("📊 批量执行中...", "orange"))
        self.gui_app.root.after(0, lambda: self._update_control_buttons(True))  # 显示中断按钮
        
        # 在新线程中执行批量任务
        self.current_task = threading.Thread(
            target=self._run_batch_tasks,
            args=(excel_path, selected_sheets, target_column),
            daemon=True
        )
        self.current_task.start()
        return True
    
    def _run_batch_tasks(self, excel_path, selected_sheets, target_column):
        """在新线程中运行批量任务"""
        try:
            self.logger.info(f"📊 开始批量执行: {len(selected_sheets)} 个Sheet，处理列: {target_column}")
            
            # 检查是否被取消
            if self.cancel_requested:
                self.logger.warning("⚠️ 批量任务已被用户取消")
                self.gui_app._update_status("⚠️ 已取消", "orange")
                return
            
            # 创建自定义批量执行器
            success = self._execute_custom_batch(excel_path, selected_sheets, target_column)
            
            if self.cancel_requested:
                self.logger.warning("⚠️ 批量任务执行过程中被取消")
                self.gui_app._update_status("⚠️ 已取消", "orange")
            elif success:
                self.logger.success("✅ 批量任务执行完成！")
                self.gui_app._update_status("✅ 批量完成", "green")
            else:
                self.logger.error("❌ 批量任务执行失败")
                self.gui_app._update_status("❌ 批量失败", "red")
                
        except Exception as e:
            self.logger.error(f"❌ 批量任务执行异常: {e}")
            self.gui_app._update_status("❌ 批量异常", "red")
        finally:
            # 重新启用按钮，隐藏中断按钮
            self.gui_app.root.after(0, lambda: self._reset_ui_after_task())
    
    def _execute_custom_batch(self, excel_path, selected_sheets, target_column):
        """执行自定义批量任务"""
        try:
            # 同步前端配置到后端config
            api_key = self.gui_app.api_key_var.get()
            if api_key:
                config.dashscope_api_key = api_key
                self.logger.info("🔑 API Key已从前端同步到后端")
            else:
                self.logger.warning("⚠️ 前端未配置API Key")
                
            # 同步其他配置
            model_name = self.gui_app.model_name_var.get()
            if model_name:
                config.model_name = model_name
                self.logger.info(f"🤖 AI模型已设置为: {model_name}")
            
            max_steps = self.gui_app.max_steps_var.get()
            if max_steps:
                config.max_execution_times = int(max_steps)
            
            device_id = self.gui_app.device_id_var.get()
            if device_id:
                config.device_id = device_id
            
            # 同步多模态增强设置
            multimodal_enabled = self.gui_app.multimodal_enabled_var.get()
            config.multimodal_enhancement["enabled"] = multimodal_enabled
            self.logger.info(f"🔍 多模态增强已设置为: {'启用' if multimodal_enabled else '禁用'}")
                
            # 设置输出目录 - 直接使用batch_output作为根目录
            batch_output_base = self.gui_app.batch_output_dir_var.get() or "batch_output"
            os.makedirs(batch_output_base, exist_ok=True)
            
            # 更新任务执行器的应用包名映射
            config.app_packages.update(self.gui_app.app_packages)
            
            total_tasks = 0
            success_tasks = 0
            failed_tasks = []
            
            # 读取Excel文件
            excel_file = pd.ExcelFile(excel_path)
            
            for sheet_name in selected_sheets:
                # 检查是否被取消
                if self.cancel_requested:
                    self.logger.warning(f"🛑 批量任务在处理Sheet '{sheet_name}' 前被中断")
                    return False
                
                self.logger.info(f"\n📋 处理Sheet: {sheet_name}")
                
                # 读取sheet数据
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # 检查目标列是否存在
                if target_column not in df.columns:
                    self.logger.warning(f"⚠️ Sheet '{sheet_name}' 中未找到列 '{target_column}'，跳过")
                    continue
                
                # 创建sheet输出目录 - 直接在batch_output_base下
                sheet_output_dir = os.path.join(batch_output_base, sheet_name)
                os.makedirs(sheet_output_dir, exist_ok=True)
                
                # 提取任务列表
                queries = []
                for index, row in df.iterrows():
                    query_value = row.get(target_column)
                    if pd.notna(query_value) and str(query_value).strip():
                        queries.append({
                            'query': str(query_value).strip(),
                            'row': index + 2,  # Excel行号（从1开始，加上表头）
                            'sheet': sheet_name
                        })
                
                self.logger.info(f"📝 从Sheet '{sheet_name}' 的列 '{target_column}' 中提取到 {len(queries)} 个任务")
                
                # 执行任务
                sheet_results = []
                for i, query_info in enumerate(queries, 1):
                    # 检查是否被取消
                    if self.cancel_requested:
                        self.logger.warning(f"🛑 批量任务在第 {i}/{len(queries)} 个任务时被中断")
                        return False
                    
                    query = query_info['query']
                    row_num = query_info['row']
                    
                    self.logger.info(f"🔄 执行任务 {i}/{len(queries)}: {query}")
                    
                    try:
                        # 为每个任务创建独立的执行器，直接输出到目标路径
                        safe_query = safe_filename(query)
                        task_output_path = os.path.join(sheet_output_dir, safe_query)
                        
                        # 如果同名目录已存在，添加序号区分
                        if os.path.exists(task_output_path):
                            counter = 1
                            while os.path.exists(f"{task_output_path}_{counter}"):
                                counter += 1
                            task_output_path = f"{task_output_path}_{counter}"
                        
                        # 创建任务执行器，直接输出到目标路径
                        executor = TaskExecutor(output_base_dir=sheet_output_dir)
                        
                        # 保存executor引用用于中断
                        self.task_executor = executor
                        
                        # 执行单个任务
                        start_time = datetime.now()
                        success = executor.run_task(query)
                        end_time = datetime.now()
                        execution_time = (end_time - start_time).total_seconds()
                        
                        # 再次检查是否被取消（任务执行后）
                        if self.cancel_requested:
                            self.logger.warning(f"🛑 批量任务在任务 {i}/{len(queries)} 执行完成后被中断")
                            return False
                        
                        # 重命名输出目录为正确的名称（如果需要）
                        if success and os.path.exists(executor.output_dir):
                            actual_output = executor.output_dir
                            if actual_output != task_output_path:
                                if os.path.exists(task_output_path):
                                    import shutil
                                    shutil.rmtree(task_output_path)
                                
                                import shutil
                                shutil.move(actual_output, task_output_path)
                            
                            self.logger.info(f"📁 任务结果已保存到: {task_output_path}")
                        
                        # 记录结果
                        result = {
                            'query': query,
                            'row': row_num,
                            'sheet': sheet_name,
                            'success': success,
                            'execution_time': execution_time,
                            'output_path': task_output_path if success else None,
                            'timestamp': start_time.isoformat()
                        }
                        sheet_results.append(result)
                        
                        total_tasks += 1
                        if success:
                            success_tasks += 1
                            self.logger.success(f"✅ 任务完成，用时 {execution_time:.1f} 秒")
                        else:
                            failed_tasks.append(query_info)
                            self.logger.error(f"❌ 任务失败，用时 {execution_time:.1f} 秒")
                            
                    except Exception as e:
                        self.logger.error(f"❌ 执行任务时出错: {e}")
                        failed_tasks.append(query_info)
                        total_tasks += 1
                
                # 保存sheet执行结果
                results_file = os.path.join(sheet_output_dir, f"{sheet_name}_results.json")
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(sheet_results, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"📄 Sheet '{sheet_name}' 执行结果已保存: {results_file}")
            
            # 生成总体报告
            self._generate_batch_report(batch_output_base, total_tasks, success_tasks, failed_tasks, target_column)
            
            # 询问是否打开输出目录
            self.gui_app.root.after(0, lambda: self.gui_app._ask_open_output(batch_output_base))
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 自定义批量执行失败: {e}")
            return False
    
    def _generate_batch_report(self, output_dir, total_tasks, success_tasks, failed_tasks, target_column):
        """生成批量执行报告"""
        try:
            report = {
                'summary': {
                    'total_tasks': total_tasks,
                    'success_tasks': success_tasks,
                    'failed_tasks': len(failed_tasks),
                    'success_rate': (success_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                    'target_column': target_column,
                    'execution_time': datetime.now().isoformat()
                },
                'failed_tasks': failed_tasks
            }
            
            report_file = os.path.join(output_dir, 'batch_execution_report.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # 输出报告摘要
            self.logger.info("\n📊 批量执行报告:")
            self.logger.info(f"   总任务数: {total_tasks}")
            self.logger.info(f"   成功: {success_tasks}")
            self.logger.info(f"   失败: {len(failed_tasks)}")
            self.logger.info(f"   成功率: {report['summary']['success_rate']:.1f}%")
            self.logger.info(f"   处理列: {target_column}")
            self.logger.info(f"📄 详细报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 生成报告失败: {e}")
    
    def is_task_running(self):
        """检查是否有任务正在运行"""
        return self.current_task and self.current_task.is_alive()
    
    def cancel_current_task(self):
        """取消当前任务"""
        if self.current_task and self.current_task.is_alive():
            self.logger.warning("🛑 正在取消当前任务...")
            self.cancel_requested = True
            
            # 如果有任务执行器，调用其中断方法
            if self.task_executor:
                try:
                    self.task_executor.interrupt_task()
                    self.logger.warning("🛑 已向任务执行器发送中断信号")
                except Exception as e:
                    self.logger.warning(f"⚠️ 中断任务执行器时出错: {e}")
            
            self.gui_app._update_status("🛑 正在取消...", "orange")
            return True
        else:
            self.logger.info("ℹ️ 没有正在运行的任务")
            return False
    
    def get_task_status(self):
        """获取任务状态"""
        if not self.current_task:
            return "idle"
        elif self.current_task.is_alive():
            return "running"
        else:
            return "completed" 