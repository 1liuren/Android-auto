#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据验证函数
"""

import re
import os
import pandas as pd


def validate_api_key(api_key):
    """验证API Key"""
    if not api_key:
        return False, "API Key不能为空"
    
    if len(api_key) < 10:
        return False, "API Key长度过短"
    
    # 简单的格式检查
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', api_key):
        return False, "API Key格式不正确"
    
    return True, "API Key格式正确"


def validate_device_id(device_id):
    """验证设备ID"""
    if not device_id:
        return True, "设备ID为空，将使用默认设备"
    
    # 设备ID通常是字母数字组合
    if not re.match(r'^[a-zA-Z0-9_\-:\.]+$', device_id):
        return False, "设备ID格式不正确"
    
    return True, "设备ID格式正确"


def validate_max_steps(max_steps_str):
    """验证最大执行次数"""
    if not max_steps_str:
        return False, "最大执行次数不能为空"
    
    try:
        max_steps = int(max_steps_str)
        if max_steps < 1:
            return False, "最大执行次数必须大于0"
        if max_steps > 1000:
            return False, "最大执行次数不能超过1000"
        return True, f"最大执行次数: {max_steps}"
    except ValueError:
        return False, "最大执行次数必须是数字"


def validate_task_description(task):
    """验证任务描述"""
    if not task:
        return False, "任务描述不能为空"
    
    if len(task.strip()) < 2:
        return False, "任务描述太短"
    
    if len(task) > 200:
        return False, "任务描述太长（最多200字符）"
    
    return True, "任务描述有效"


def validate_excel_file(file_path):
    """验证Excel文件"""
    if not file_path:
        return False, "请选择Excel文件"
    
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        return False, "文件格式不正确，请选择Excel文件（.xlsx或.xls）"
    
    try:
        # 尝试读取文件
        excel_file = pd.ExcelFile(file_path)
        if not excel_file.sheet_names:
            return False, "Excel文件没有工作表"
        return True, f"Excel文件有效，包含 {len(excel_file.sheet_names)} 个工作表"
    except Exception as e:
        return False, f"无法读取Excel文件: {e}"


def validate_sheet_selection(sheet_vars):
    """验证Sheet选择"""
    if not sheet_vars:
        return False, "没有可用的工作表"
    
    selected_sheets = [sheet for sheet, var in sheet_vars.items() if var.get()]
    if not selected_sheets:
        return False, "请至少选择一个工作表"
    
    return True, f"已选择 {len(selected_sheets)} 个工作表"


def validate_column_selection(excel_path, sheet_name, column_name):
    """验证列选择"""
    if not column_name:
        return False, "请选择要处理的列"
    
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=0)
        if column_name not in df.columns:
            return False, f"工作表 '{sheet_name}' 中不存在列 '{column_name}'"
        return True, f"列 '{column_name}' 存在"
    except Exception as e:
        return False, f"验证列时出错: {e}"


def validate_app_package_mapping(app_name, package_name):
    """验证应用包名映射"""
    if not app_name or not app_name.strip():
        return False, "应用名称不能为空"
    
    if not package_name or not package_name.strip():
        return False, "包名不能为空"
    
    # 验证包名格式（简单检查）
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$', package_name):
        return False, "包名格式不正确（应为com.example.app格式）"
    
    return True, "应用包名映射有效"


def validate_batch_execution_params(excel_path, selected_sheets, target_column):
    """验证批量执行参数"""
    # 验证Excel文件
    is_valid, msg = validate_excel_file(excel_path)
    if not is_valid:
        return False, f"Excel文件验证失败: {msg}"
    
    # 验证选中的sheets
    if not selected_sheets:
        return False, "请至少选择一个工作表"
    
    # 验证目标列
    if not target_column:
        return False, "请选择要处理的列"
    
    # 验证每个sheet中是否存在目标列
    try:
        excel_file = pd.ExcelFile(excel_path)
        missing_columns = []
        
        for sheet in selected_sheets:
            if sheet not in excel_file.sheet_names:
                return False, f"工作表 '{sheet}' 不存在"
            
            df = pd.read_excel(excel_file, sheet_name=sheet, nrows=0)
            if target_column not in df.columns:
                missing_columns.append(sheet)
        
        if missing_columns:
            return False, f"以下工作表中缺少列 '{target_column}': {', '.join(missing_columns)}"
        
        return True, f"批量执行参数验证通过：{len(selected_sheets)} 个工作表，列 '{target_column}'"
        
    except Exception as e:
        return False, f"验证批量执行参数时出错: {e}" 