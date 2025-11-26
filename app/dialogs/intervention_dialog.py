#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人工接管对话框
用于显示AI输出结果并允许人工修改
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import re
from ..utils.ui_helpers import create_custom_button, MODERN_COLORS
from src.logger_config import get_logger

# 获取日志记录器
logger = get_logger("intervention_dialog")


class InterventionDialog:
    """人工接管对话框"""
    
    def __init__(self, parent, ai_result, screenshot_path=None, main_app=None):
        self.parent = parent
        self.ai_result = ai_result.copy()  # 复制AI结果
        
        # 预处理AI结果中的坐标，将占位符替换为默认值
        self._preprocess_plan_coordinates()
        
        self.screenshot_path = screenshot_path
        self.main_app = main_app  # 主应用对象，包含device_manager等
        self.result = None  # 用户修改后的结果
        self.approved = False  # 是否通过审批
        self.xml_path = None  # 保存XML路径
        # 初始化completed_var，确保在_get_modified_result中可用
        self.completed_var = None
        
        # 创建对话框
        self._create_dialog()
        
    def _preprocess_plan_coordinates(self):
        """预处理plan中的坐标，将占位符文本替换为默认值"""
        if 'plan' not in self.ai_result or not isinstance(self.ai_result['plan'], dict):
            return
            
        plan = self.ai_result['plan']
        
        # 处理position字段
        if "position" in plan and isinstance(plan["position"], str):
            if "<point>" in plan["position"]:
                plan["position"] = [0, 0]  # 默认值
                
        # 处理box字段
        if "box" in plan and isinstance(plan["box"], str):
            if "<bbox>" in plan["box"]:
                plan["box"] = [[0, 0], [0, 0]]  # 默认值
                
        # 处理其他可能的坐标字段
        for key in ["start_position", "stop_position", "swipe_start", "swipe_end"]:
            if key in plan and isinstance(plan[key], str) and "<point>" in plan[key]:
                plan[key] = [0, 0]  # 默认值
        
    def _create_dialog(self):
        """创建对话框界面"""
        # 创建顶级窗口
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🛠️ 人工接管 - AI输出审批")
        self.dialog.geometry("1200x900")
        self.dialog.configure(bg=MODERN_COLORS['bg_primary'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (900 // 2)
        self.dialog.geometry(f"1200x900+{x}+{y}")
        
        # 创建主框架
        main_frame = tk.Frame(self.dialog, bg=MODERN_COLORS['bg_primary'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题区域
        self._create_title_section(main_frame)
        
        # 内容区域（左右分栏）
        content_frame = tk.Frame(main_frame, bg=MODERN_COLORS['bg_primary'])
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)
        
        # 左侧参数区域
        self._create_content_section(content_frame)
        
        # 右侧可视化区域
        self._create_visualization_section(content_frame)
        
        # 按钮区域
        self._create_button_section(main_frame)
        
        # 初始化可视化标注
        if self.screenshot_path:
            self._generate_visual_label()
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
    def _create_title_section(self, parent):
        """创建标题区域"""
        title_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'], relief="solid", bd=1)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        title_frame.columnconfigure(1, weight=1)
        
        # 图标
        icon_label = tk.Label(
            title_frame,
            text="🤖",
            font=("Arial", 24),
            bg=MODERN_COLORS['bg_secondary']
        )
        icon_label.grid(row=0, column=0, padx=20, pady=15)
        
        # 标题文本
        title_label = tk.Label(
            title_frame,
            text="AI 输出结果审批",
            font=("Microsoft YaHei UI", 16, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_secondary']
        )
        title_label.grid(row=0, column=1, sticky="w", pady=15)
        
        # 说明文本
        desc_label = tk.Label(
            title_frame,
            text="请审核AI的输出结果，您可以修改操作描述、坐标位置等信息",
            font=("Arial", 10),
            fg=MODERN_COLORS['dark_gray'],
            bg=MODERN_COLORS['bg_secondary']
        )
        desc_label.grid(row=1, column=1, sticky="w", padx=(0, 20), pady=(0, 15))
        
    def _create_content_section(self, parent):
        """创建左侧内容区域"""
        # 创建普通框架（不使用滚动条）
        content_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        content_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=0)  # 观察结果区域
        content_frame.rowconfigure(1, weight=1)  # 操作计划区域
        content_frame.rowconfigure(2, weight=0)  # 完成状态区域
        
        # AI观察结果
        self._create_observation_section(content_frame)
        
        # 操作计划
        self._create_plan_section(content_frame)
        
        # 任务完成状态区域（只在End操作时显示）
        self.completion_frame = None
        self._create_completion_section(content_frame)
        
        # 坐标标注工具区域
        if self.screenshot_path:
            self._create_coordinate_section(content_frame)
    
    def _create_visualization_section(self, parent):
        """创建右侧可视化区域"""
        viz_frame = tk.LabelFrame(
            parent,
            text="📱 可视化标注预览",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_primary']
        )
        viz_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)
        
        # 工具栏
        toolbar_frame = tk.Frame(viz_frame, bg=MODERN_COLORS['bg_primary'])
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # 坐标标注按钮
        coord_button = create_custom_button(
            toolbar_frame,
            text="🖱️ 坐标标注工具",
            command=self._open_coordinate_tool,
            style_type="info"
        )
        coord_button.pack(side="left", padx=(0, 10))
        
        # 刷新截屏按钮
        refresh_screenshot_button = create_custom_button(
            toolbar_frame,
            text="📷 重新截屏",
            command=self._refresh_screenshot,
            style_type="warning"
        )
        refresh_screenshot_button.pack(side="left", padx=(0, 5))
        
        # 刷新预览按钮
        refresh_button = create_custom_button(
            toolbar_frame,
            text="🔄 刷新预览",
            command=self._auto_generate_visual_label,
            style_type="success"
        )
        refresh_button.pack(side="left")
        
        # 生成可视化标注按钮
        generate_button = create_custom_button(
            toolbar_frame,
            text="🎯 生成标注",
            command=self._generate_visual_label,
            style_type="primary"
        )
        generate_button.pack(side="left", padx=(10, 0))
        

        
        # 图片显示区域
        self.image_frame = tk.Frame(viz_frame, bg=MODERN_COLORS['white'], relief="solid", bd=1)
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # 图片标签（用于显示截图和标注）
        self.image_label = tk.Label(
            self.image_frame,
            text="正在加载可视化标注...",
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark_gray'],
            font=("Arial", 12)
        )
        self.image_label.pack(expand=True, fill="both")
        
    def _create_observation_section(self, parent):
        """创建观察结果区域"""
        obs_frame = tk.LabelFrame(
            parent,
            text="🔍 AI观察结果",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_primary']
        )
        obs_frame.pack(fill="x", pady=(0, 15))
        obs_frame.columnconfigure(0, weight=1)
        
        # 观察结果文本框
        self.observation_text = tk.Text(
            obs_frame,
            height=3,
            font=("Arial", 9),
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark'],
            relief="solid",
            bd=1,
            wrap="word"
        )
        self.observation_text.pack(fill="x", padx=10, pady=10)
        self.observation_text.insert("1.0", self.ai_result.get('observation', ''))
        
    def _create_plan_section(self, parent):
        """创建操作计划区域"""
        plan_frame = tk.LabelFrame(
            parent,
            text="🎯 操作计划",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_primary']
        )
        plan_frame.pack(fill="x", pady=(0, 15))
        plan_frame.columnconfigure(1, weight=1)
        
        plan = self.ai_result.get('plan', {})
        
        # 操作描述
        tk.Label(
            plan_frame,
            text="操作描述:",
            font=("Arial", 9, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=0, column=0, sticky="w", padx=10, pady=3)
        
        self.description_entry = tk.Entry(
            plan_frame,
            font=("Arial", 9),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1
        )
        self.description_entry.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=3)
        self.description_entry.insert(0, plan.get('description', ''))
        
        # 操作类型
        tk.Label(
            plan_frame,
            text="操作类型:",
            font=("Arial", 9, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=1, column=0, sticky="w", padx=10, pady=3)
        
        self.type_var = tk.StringVar(value=plan.get('type', 'touch'))
        type_combo = ttk.Combobox(
            plan_frame,
            textvariable=self.type_var,
            values=['Open', 'touch', 'long_touch', 'input', 'scroll', 'drag', 'wait', 'request', 'End'],
            state="readonly",
            font=("Arial", 10)
        )
        type_combo.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=5)
        
        # Open操作相关参数（仅在Open类型时显示）
        self.open_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        self.open_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.open_frame.columnconfigure(1, weight=1)
        
        # 应用名称
        tk.Label(
            self.open_frame,
            text="应用名称:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=0, column=0, sticky="w")
        
        self.app_entry = tk.Entry(
            self.open_frame,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1
        )
        self.app_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.app_entry.insert(0, plan.get('app', ''))
        
        # 包名
        tk.Label(
            self.open_frame,
            text="包名:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        self.package_entry = tk.Entry(
            self.open_frame,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1
        )
        self.package_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(5, 0))
        self.package_entry.insert(0, plan.get('package', ''))
        
        # 坐标位置标签（根据操作类型动态显示）
        self.coord_label = tk.Label(
            plan_frame,
            text="坐标位置:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        )
        self.coord_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        
        coord_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        coord_frame.grid(row=3, column=1, sticky="ew", padx=(5, 10), pady=5)
        coord_frame.columnconfigure(0, weight=1)
        coord_frame.columnconfigure(1, weight=1)
        coord_frame.columnconfigure(2, weight=1)
        coord_frame.columnconfigure(3, weight=1)
        
        # 根据操作类型获取正确的起始坐标
        if plan.get('type', '').lower() in ['scroll', 'drag']:
            # scroll/drag操作优先使用start_position
            position = plan.get('start_position') or plan.get('position') or [0, 0]
        else:
            # 其他操作优先使用position
            position = plan.get('position') or plan.get('start_position') or [0, 0]
        
        tk.Label(coord_frame, text="X:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.x_entry = tk.Entry(coord_frame, width=10, font=("Arial", 10))
        self.x_entry.grid(row=0, column=1, sticky="w", padx=(2, 8))
        
        tk.Label(coord_frame, text="Y:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=2, sticky="w")
        self.y_entry = tk.Entry(coord_frame, width=10, font=("Arial", 10))
        self.y_entry.grid(row=0, column=3, sticky="w", padx=(2, 0))
        
        # 初始化坐标值
        logger.debug(f"🔍 初始化坐标值，plan数据: {plan}")
        logger.debug(f"📍 起始坐标position: {position}")
        
        self.x_entry.insert(0, str(position[0]))
        self.y_entry.insert(0, str(position[1]))
        
        logger.debug(f"✅ 起始坐标输入框已初始化: ({position[0]}, {position[1]})")
        
        # 边界框信息（根据操作类型显示）
        self.bbox_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        self.bbox_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.bbox_frame.columnconfigure(1, weight=1)
        
        self.bbox_label = tk.Label(
            self.bbox_frame,
            text="box:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        )
        self.bbox_label.grid(row=0, column=0, sticky="w")
        
        bbox_coord_frame = tk.Frame(self.bbox_frame, bg=MODERN_COLORS['bg_primary'])
        bbox_coord_frame.grid(row=0, column=1, sticky="ew")
        bbox_coord_frame.columnconfigure(0, weight=1)
        bbox_coord_frame.columnconfigure(1, weight=1)
        bbox_coord_frame.columnconfigure(2, weight=1)
        bbox_coord_frame.columnconfigure(3, weight=1)
        bbox_coord_frame.columnconfigure(4, weight=1)
        bbox_coord_frame.columnconfigure(5, weight=1)
        bbox_coord_frame.columnconfigure(6, weight=1)
        bbox_coord_frame.columnconfigure(7, weight=1)
        
        # 获取bbox信息，支持多种格式
        bbox = plan.get('bbox') or plan.get('box', [[0, 0], [0, 0]])
        if isinstance(bbox, list):
            if len(bbox) == 4:  # [x1, y1, x2, y2] 格式
                bbox_flat = bbox
            elif len(bbox) >= 2 and isinstance(bbox[0], list) and len(bbox[0]) >= 2 and len(bbox[1]) >= 2:  # [[x1,y1],[x2,y2]] 格式
                bbox_flat = [bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]]
            else:
                bbox_flat = [0, 0, 0, 0]
        else:
            bbox_flat = [0, 0, 0, 0]
        
        tk.Label(bbox_coord_frame, text="x1:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.bbox_left_entry = tk.Entry(bbox_coord_frame, width=8, font=("Arial", 10))
        self.bbox_left_entry.grid(row=0, column=1, sticky="w", padx=(2, 8))
        
        tk.Label(bbox_coord_frame, text="y1:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=2, sticky="w")
        self.bbox_top_entry = tk.Entry(bbox_coord_frame, width=8, font=("Arial", 10))
        self.bbox_top_entry.grid(row=0, column=3, sticky="w", padx=(2, 8))
        
        tk.Label(bbox_coord_frame, text="x2:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=4, sticky="w")
        self.bbox_right_entry = tk.Entry(bbox_coord_frame, width=8, font=("Arial", 10))
        self.bbox_right_entry.grid(row=0, column=5, sticky="w", padx=(2, 8))
        
        tk.Label(bbox_coord_frame, text="y2:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=6, sticky="w")
        self.bbox_bottom_entry = tk.Entry(bbox_coord_frame, width=8, font=("Arial", 10))
        self.bbox_bottom_entry.grid(row=0, column=7, sticky="w", padx=(2, 0))
        
        # 初始化边界框坐标值
        logger.debug(f"📍 边界框bbox: {bbox}")
        logger.debug(f"📍 边界框bbox_flat: {bbox_flat}")
        
        self.bbox_left_entry.insert(0, str(bbox_flat[0]))
        self.bbox_top_entry.insert(0, str(bbox_flat[1]))
        self.bbox_right_entry.insert(0, str(bbox_flat[2]))
        self.bbox_bottom_entry.insert(0, str(bbox_flat[3]))
        
        logger.debug(f"✅ 边界框输入框已初始化: [{bbox_flat[0]}, {bbox_flat[1]}, {bbox_flat[2]}, {bbox_flat[3]}]")
        
        # 滑动相关参数（仅在scroll/drag类型时显示）
        self.swipe_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        self.swipe_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.swipe_frame.columnconfigure(1, weight=1)
        
        self.swipe_label = tk.Label(
            self.swipe_frame,
            text="滑动终点:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        )
        self.swipe_label.grid(row=0, column=0, sticky="w")
        
        swipe_coord_frame = tk.Frame(self.swipe_frame, bg=MODERN_COLORS['bg_primary'])
        swipe_coord_frame.grid(row=0, column=1, sticky="ew")
        swipe_coord_frame.columnconfigure(0, weight=1)
        swipe_coord_frame.columnconfigure(1, weight=1)
        swipe_coord_frame.columnconfigure(2, weight=1)
        swipe_coord_frame.columnconfigure(3, weight=1)
        
        # 获取终点坐标：优先使用stop_position，其次是end_position
        end_position = plan.get('stop_position') or plan.get('end_position') or [0, 0]
        # 如果都没有，则使用起始坐标
        if end_position == [0, 0]:
            end_position = position
        
        tk.Label(swipe_coord_frame, text="X:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.end_x_entry = tk.Entry(swipe_coord_frame, width=10, font=("Arial", 10))
        self.end_x_entry.grid(row=0, column=1, sticky="w", padx=(2, 8))
        
        tk.Label(swipe_coord_frame, text="Y:", bg=MODERN_COLORS['bg_primary'], font=("Arial", 10)).grid(row=0, column=2, sticky="w")
        self.end_y_entry = tk.Entry(swipe_coord_frame, width=10, font=("Arial", 10))
        self.end_y_entry.grid(row=0, column=3, sticky="w", padx=(2, 0))
        
        # 初始化终点坐标值
        logger.debug(f"📍 终点坐标end_position: {end_position}")
        
        self.end_x_entry.insert(0, str(end_position[0]))
        self.end_y_entry.insert(0, str(end_position[1]))
        
        logger.debug(f"✅ 终点坐标输入框已初始化: ({end_position[0]}, {end_position[1]})")
        
        # 输入文本（仅在Input类型时显示）
        self.input_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        self.input_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.input_frame.columnconfigure(1, weight=1)
        
        tk.Label(
            self.input_frame,
            text="输入文本:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=0, column=0, sticky="w")
        
        self.input_text_entry = tk.Entry(
            self.input_frame,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1
        )
        self.input_text_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.input_text_entry.insert(0, plan.get('text', ''))
        
        # 时长参数（仅在long_touch和wait类型时显示）
        self.duration_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        self.duration_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.duration_frame.columnconfigure(1, weight=1)
        
        tk.Label(
            self.duration_frame,
            text="时长(秒):",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=0, column=0, sticky="w")
        
        self.duration_entry = tk.Entry(
            self.duration_frame,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1,
            width=10
        )
        self.duration_entry.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        # 根据操作类型获取默认时长值
        default_duration = 1.0
        if plan.get('type') == 'wait' and 'wait_time' in plan:
            default_duration = plan.get('wait_time')
        elif 'duration' in plan:
            default_duration = plan.get('duration')
            
        self.duration_entry.insert(0, str(default_duration))
        
        # Request操作相关参数（仅在request类型时显示）
        self.request_frame = tk.Frame(plan_frame, bg=MODERN_COLORS['bg_primary'])
        self.request_frame.grid(row=8, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.request_frame.columnconfigure(1, weight=1)
        
        # Request文本
        tk.Label(
            self.request_frame,
            text="提问文本:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=0, column=0, sticky="nw", pady=(2, 0))
        
        self.request_text_entry = tk.Text(
            self.request_frame,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1,
            height=3,
            wrap=tk.WORD
        )
        self.request_text_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.request_text_entry.insert(tk.END, plan.get('text', ''))
        
        # Request选项
        tk.Label(
            self.request_frame,
            text="可选项:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).grid(row=1, column=0, sticky="nw", pady=(5, 0))
        
        self.request_options_entry = tk.Text(
            self.request_frame,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            relief="solid",
            bd=1,
            height=2,
            wrap=tk.WORD
        )
        self.request_options_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(5, 0))
        # 将options列表转换为每行一个选项的文本格式
        options = plan.get('options', [])
        if options:
            options_text = '\n'.join(str(opt) for opt in options)
            self.request_options_entry.insert(tk.END, options_text)
        
        # Request响应输入
        tk.Label(
            self.request_frame,
            text="用户响应:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary'],
            fg='red'  # 高亮显示这是需要用户输入的部分
        ).grid(row=2, column=0, sticky="nw", pady=(5, 0))
        
        self.request_response_entry = tk.Entry(
            self.request_frame,
            font=("Arial", 10),
            bg='#fff8dc',  # 淡黄色背景突出显示
            relief="solid",
            bd=2
        )
        self.request_response_entry.grid(row=2, column=1, sticky="ew", padx=(5, 0), pady=(5, 0))
        
        # 绑定类型变化事件
        type_combo.bind('<<ComboboxSelected>>', self._on_type_changed_with_visual)
        self._on_type_changed()  # 初始化显示
        
        # 绑定坐标变化事件
        for entry in [self.x_entry, self.y_entry, self.end_x_entry, self.end_y_entry, 
                      self.bbox_left_entry, self.bbox_top_entry, self.bbox_right_entry, self.bbox_bottom_entry]:
            entry.bind('<KeyRelease>', lambda e: self._auto_generate_visual_label())
            entry.bind('<FocusOut>', lambda e: self._auto_generate_visual_label())
        
        # 初始化时自动生成可视化标注
        self.dialog.after(100, self._auto_generate_visual_label)  # 延迟100ms确保UI完全加载
        
    def _create_completion_section(self, parent):
        """创建任务完成状态区域"""
        self.completion_frame = tk.LabelFrame(
            parent,
            text="✅ 任务状态",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_primary']
        )
        self.completion_frame.pack(fill="x", pady=(0, 15))
        
        # 默认隐藏，只在End操作时显示
        self.completion_frame.pack_forget()
        
        # 任务完成状态
        self.completed_var = tk.BooleanVar(value=self.ai_result.get('is_task_completed', False))
        completed_check = tk.Checkbutton(
            self.completion_frame,
            text="任务已完成",
            variable=self.completed_var,
            font=("Arial", 10),
            bg=MODERN_COLORS['bg_primary']
        )
        completed_check.pack(anchor="w", padx=10, pady=5)
        
        # 完成原因
        tk.Label(
            self.completion_frame,
            text="完成原因:",
            font=("Arial", 10, "bold"),
            bg=MODERN_COLORS['bg_primary']
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        self.completion_reason_text = tk.Text(
            self.completion_frame,
            height=3,
            font=("Arial", 10),
            bg=MODERN_COLORS['white'],
            fg=MODERN_COLORS['dark'],
            relief="solid",
            bd=1,
            wrap="word"
        )
        self.completion_reason_text.pack(fill="x", padx=10, pady=(5, 10))
        self.completion_reason_text.insert("1.0", self.ai_result.get('completion_reason', ''))
        
    def _create_coordinate_section(self, parent):
        """创建坐标标注区域"""
        coord_frame = tk.LabelFrame(
            parent,
            text="📍 可视化标注工具",
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_primary']
        )
        coord_frame.pack(fill="x", pady=(0, 15))
        
        # 说明文本
        info_label = tk.Label(
            coord_frame,
            text="生成可视化标注图片，支持画框、点击、画箭头等方式修改操作参数",
            font=("Arial", 10),
            fg=MODERN_COLORS['dark_gray'],
            bg=MODERN_COLORS['bg_primary']
        )
        info_label.pack(padx=10, pady=(10, 5))
        
        # 按钮容器
        button_container = tk.Frame(coord_frame, bg=MODERN_COLORS['bg_primary'])
        button_container.pack(fill="x", padx=10, pady=(5, 10))
        
        # 坐标标注按钮
        coord_button = create_custom_button(
            button_container,
            text="🖱️ 打开坐标标注工具",
            command=self._open_coordinate_tool,
            style_type="info"
        )
        coord_button.pack(side="left", padx=(0, 10))
        
        # 重新截屏按钮
        screenshot_button = create_custom_button(
            button_container,
            text="📷 重新截屏",
            command=self._refresh_screenshot,
            style_type="warning"
        )
        screenshot_button.pack(side="left", padx=(0, 10))
        
        # 刷新预览按钮
        visual_button = create_custom_button(
            button_container,
            text="🔄 刷新预览",
            command=self._generate_visual_label,
            style_type="success"
        )
        visual_button.pack(side="left")
        
    def _refresh_screenshot(self):
        """重新截屏并刷新预览"""
        try:
            # 检查main_app对象是否存在
            if not self.main_app:
                messagebox.showerror("错误", "主应用对象未初始化，无法重新截屏")
                return
                
            # 检查设备管理器
            if not hasattr(self.main_app, 'device_manager') or not self.main_app.device_manager:
                messagebox.showerror("错误", "设备管理器未初始化")
                return
                
            # 尝试连接设备
            if not self.main_app.device_manager.is_device_connected():
                messagebox.showerror("错误", "设备未连接，无法重新截屏")
                return
            
            # 检查任务管理器
            if not hasattr(self.main_app, 'task_manager') or not self.main_app.task_manager:
                messagebox.showerror("错误", "任务管理器未初始化")
                return
                
            # 检查任务执行器
            if not hasattr(self.main_app.task_manager, 'task_executor') or not self.main_app.task_manager.task_executor:
                messagebox.showerror("错误", "任务执行器未初始化")
                return
                
            executor = self.main_app.task_manager.task_executor
            if not hasattr(executor, 'device') or not executor.device:
                messagebox.showerror("错误", "设备控制器未初始化")
                return
            
            try:
                import os
                import time
                
                # 如果没有原始截屏路径，创建临时目录
                if not self.screenshot_path:
                    temp_dir = os.path.join(os.getcwd(), "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    self.screenshot_path = os.path.join(temp_dir, "screenshot.jpg")
                    self.xml_path = os.path.join(temp_dir, "hierarchy.xml")
                
                # 使用原始文件名进行重新截屏和获取XML
                screenshot_path = self.screenshot_path
                xml_path = self.xml_path or os.path.join(os.path.dirname(self.screenshot_path), "hierarchy.xml")
                
                # 重新截屏和获取XML
                executor.device.screenshot(screenshot_path)
                executor.device.get_xml_hierarchy(xml_path)
                
                # 保存XML路径到实例变量，以便在_get_modified_result中使用
                self.xml_path = xml_path
                
                # 刷新可视化预览
                self._auto_generate_visual_label()
                
                messagebox.showinfo("成功", "已重新截屏并刷新预览")
                
            except Exception as e:
                messagebox.showerror("错误", f"重新截屏失败: {e}")
                
        except Exception as e:
            messagebox.showerror("错误", f"重新截屏过程中发生错误: {e}")
    
    def _generate_visual_label(self):
        """生成可视化标注预览"""
        self._auto_generate_visual_label()
    
    def _show_visual_label(self, image_path):
        """显示可视化标注图片"""
        try:
            import subprocess
            import platform
            import os
            
            # 根据操作系统打开图片
            if platform.system() == 'Windows':
                os.startfile(image_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', image_path])
            else:  # Linux
                subprocess.run(['xdg-open', image_path])
                
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片: {e}")
    
    def _auto_generate_visual_label(self):
        """自动生成可视化标注并在右侧显示"""
        try:
            import os
            from utils.image_marker import ImageMarker
            
            # 检查截图路径
            if not self.screenshot_path or not os.path.exists(self.screenshot_path):
                if hasattr(self, 'image_label'):
                    self.image_label.config(text="未找到截图文件", image="")
                return
            
            # 获取当前的操作信息
            current_result = self._get_modified_result()
            plan_data = current_result.get('plan', {})
            
            # 准备标记参数
            action_type = plan_data.get('type', '')
            position = None
            bbox = plan_data.get('box')
            start_position = None
            end_position = None
            description = plan_data.get('description', '')
            
            # 根据操作类型准备参数
            pos = plan_data.get('position', [0, 0])
            if len(pos) >= 2:
                position = [int(pos[0]), int(pos[1])]
                

            
            # 处理滑动类操作的终点坐标和box信息
            if action_type in ['scroll', 'drag']:
                start_position = plan_data.get('start_position', pos)   
                end_position = plan_data.get('stop_position', pos)
                    
            
            # 生成临时标注图片
            temp_dir = os.path.dirname(self.screenshot_path)
            temp_label_path = os.path.join(temp_dir, 'temp_intervention_preview.jpg')
            
            # 调用ImageMarker生成标注图片
            marker = ImageMarker()
            success = marker.mark_action(
                screenshot_path=self.screenshot_path,
                output_path=temp_label_path,
                action_type=action_type,
                position=position,
                box=bbox,
                description=description,
                start_position=start_position,
                stop_position=end_position
            )
            
            # 在右侧显示生成的标注图片
            if success and os.path.exists(temp_label_path) and hasattr(self, 'image_label'):
                self._display_image_in_label(temp_label_path)
                logger.debug(f"✅ 可视化标注生成成功: {temp_label_path}")
            elif hasattr(self, 'image_label'):
                # 如果生成失败，显示原始截图
                self._display_image_in_label(self.screenshot_path)
                logger.debug(f"❌ 可视化标注生成失败，显示原图: {self.screenshot_path}")
                
        except Exception as e:
            if hasattr(self, 'image_label'):
                self.image_label.config(text=f"生成可视化标注失败: {str(e)}", image="")
            logger.debug(f"❌ 生成可视化标注异常: {e}")
    
    def _display_image_in_label(self, image_path):
        """在标签中显示图片"""
        try:
            from PIL import Image, ImageTk
            
            # 打开图片
            image = Image.open(image_path)
            
            # 计算缩放比例（适应显示区域）
            display_width = 500  # 右侧区域宽度
            display_height = 600  # 右侧区域高度
            
            # 保持宽高比缩放
            img_width, img_height = image.size
            scale_w = display_width / img_width
            scale_h = display_height / img_height
            scale = min(scale_w, scale_h)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 缩放图片
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可用的格式
            photo = ImageTk.PhotoImage(image)
            
            # 显示图片
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # 保持引用
            
        except Exception as e:
            self.image_label.config(text=f"显示图片失败: {str(e)}", image="")
        
    def _create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        button_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        
        # 通过按钮
        approve_btn = create_custom_button(
            button_frame,
            text="✅ 通过并执行",
            command=self._on_approve,
            style_type="success"
        )
        approve_btn.pack(side="left", padx=(0, 10))
        
        # 取消按钮
        cancel_btn = create_custom_button(
            button_frame,
            text="❌ 取消",
            command=self._on_cancel,
            style_type="danger"
        )
        cancel_btn.pack(side="left")
        
        # 预览JSON按钮
        preview_btn = create_custom_button(
            button_frame,
            text="👁️ 预览JSON",
            command=self._preview_json,
            style_type="info"
        )
        preview_btn.pack(side="right")
        
    def _on_type_changed_with_visual(self, *args):
        """操作类型改变时的处理（包含可视化更新）"""
        self._on_type_changed(*args)
        self._generate_visual_label()
    
    def _on_type_changed(self, *args):
        """操作类型改变时的处理"""
        operation_type = self.type_var.get()
        logger.debug(f"🔄 操作类型切换: {operation_type}")
        
        # 根据操作类型更新坐标标签文本和显示相关控件
        if operation_type in ['scroll', 'drag']:
            logger.debug(f"📍 设置滑动/拖拽模式: 显示起始位置和边界框")
            self.coord_label.config(text="起始位置:")
            self.bbox_frame.grid()  # 显示边界框
            # 更新滑动终点标签
            if hasattr(self, 'swipe_label'):
                if operation_type == 'scroll':
                    self.swipe_label.config(text="滑动终点:")
                else:  # drag
                    self.swipe_label.config(text="拖动终点:")
            logger.debug(f"✅ 坐标标签已更新为: {self.coord_label.cget('text')}")
            logger.debug(f"✅ 边界框已显示")
        elif operation_type == 'touch':
            logger.debug(f"📍 设置点击模式: 显示点击位置和边界框")
            self.coord_label.config(text="点击位置:")
            self.bbox_frame.grid()  # 显示边界框（用户要求touch也显示box信息）
            logger.debug(f"✅ 坐标标签已更新为: {self.coord_label.cget('text')}")
            logger.debug(f"✅ 边界框已显示")
        elif operation_type == 'long_touch':
            logger.debug(f"📍 设置长按模式: 显示长按位置和边界框")
            self.coord_label.config(text="长按位置:")
            self.bbox_frame.grid()  # 显示边界框
            logger.debug(f"✅ 坐标标签已更新为: {self.coord_label.cget('text')}")
            logger.debug(f"✅ 边界框已显示")
        elif operation_type == 'input':
            logger.debug(f"📍 设置输入模式: 显示输入位置和边界框")
            self.coord_label.config(text="输入位置:")
            self.bbox_frame.grid()  # 显示边界框
            logger.debug(f"✅ 坐标标签已更新为: {self.coord_label.cget('text')}")
            logger.debug(f"✅ 边界框已显示")
        else:
            logger.debug(f"📍 设置默认模式: 显示坐标位置，隐藏边界框")
            self.coord_label.config(text="坐标位置:")
            self.bbox_frame.grid_remove()  # 隐藏边界框
            logger.debug(f"✅ 坐标标签已更新为: {self.coord_label.cget('text')}")
            logger.debug(f"✅ 边界框已隐藏")
        
        # 显示/隐藏Open操作相关控件
        if operation_type == 'Open':
            self.open_frame.grid()
            # Open操作不需要坐标，保持为0
            if not self.x_entry.get():
                self.x_entry.insert(0, "0")
            if not self.y_entry.get():
                self.y_entry.insert(0, "0")
        else:
            self.open_frame.grid_remove()
            # 清空应用信息
            if hasattr(self, 'app_entry'):
                self.app_entry.delete(0, tk.END)
            if hasattr(self, 'package_entry'):
                self.package_entry.delete(0, tk.END)
        
        # 显示/隐藏滑动相关控件（scroll和drag操作需要终点坐标）
        if operation_type in ['scroll', 'drag']:
            self.swipe_frame.grid()
            # 不设置默认坐标，保持原有值或0
        else:
            self.swipe_frame.grid_remove()
            # 清空终点坐标
            if hasattr(self, 'end_x_entry'):
                self.end_x_entry.delete(0, tk.END)
            if hasattr(self, 'end_y_entry'):
                self.end_y_entry.delete(0, tk.END)
            
        # 显示/隐藏输入相关控件
        if operation_type == 'input':
            self.input_frame.grid()
            # 不设置默认坐标，保持原有值或0
        else:
            self.input_frame.grid_remove()
            # 清空输入文本
            if hasattr(self, 'input_text_entry'):
                self.input_text_entry.delete(0, tk.END)
            
        # 显示/隐藏时长相关控件（long_touch和wait操作需要时长参数）
        if operation_type in ['long_touch', 'wait']:
            self.duration_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
            # 只在没有值时设置默认时长
            if hasattr(self, 'duration_entry') and not self.duration_entry.get():
                default_duration = "2.0" if operation_type == 'long_touch' else "3.0"
                self.duration_entry.insert(0, default_duration)
            # 不设置默认坐标，保持原有值或0
        else:
            self.duration_frame.grid_remove()
            
        # 显示/隐藏Request相关控件
        if operation_type == 'request':
            self.request_frame.grid()
            # Request操作不需要坐标，设置为0
            if not self.x_entry.get():
                self.x_entry.insert(0, "0")
            if not self.y_entry.get():
                self.y_entry.insert(0, "0")
        else:
            self.request_frame.grid_remove()
            
        # touch操作不设置默认坐标，保持原有值或0
            
        # 显示/隐藏任务完成状态区域（只在End操作时显示）
        if hasattr(self, 'completion_frame') and self.completion_frame:
            if operation_type == 'End':
                self.completion_frame.pack(fill="x", pady=(0, 15))
            else:
                self.completion_frame.pack_forget()
                
        # 自动生成可视化标注
        self._auto_generate_visual_label()
            
    def _open_coordinate_tool(self):
        """打开坐标标注工具"""
        try:
            from .coordinate_annotation_dialog import CoordinateAnnotationDialog
            
            # 获取当前操作类型
            current_type = self.type_var.get()
            
            # 准备初始坐标数据
            initial_coordinates = {
                'x': int(self.x_entry.get()) if self.x_entry.get() else 0,
                'y': int(self.y_entry.get()) if self.y_entry.get() else 0
            }
            
            # 添加边界框信息（如果存在）
            if hasattr(self, 'bbox_left_entry') and all([
                self.bbox_left_entry.get(), self.bbox_top_entry.get(),
                self.bbox_right_entry.get(), self.bbox_bottom_entry.get()
            ]):
                try:
                    bbox = [
                        int(self.bbox_left_entry.get()),
                        int(self.bbox_top_entry.get()),
                        int(self.bbox_right_entry.get()),
                        int(self.bbox_bottom_entry.get())
                    ]
                    initial_coordinates['bbox'] = bbox
                    logger.debug(f"📦 传递边界框信息给CoordinateAnnotationDialog: {bbox}")
                except ValueError:
                    pass
            
            # 如果是scroll或drag操作，添加终点坐标
            if current_type in ['scroll', 'drag']:
                initial_coordinates['end_x'] = int(self.end_x_entry.get()) if self.end_x_entry.get() else 0
                initial_coordinates['end_y'] = int(self.end_y_entry.get()) if self.end_y_entry.get() else 0
            
            # 如果是长按或等待操作，添加时长参数
            if current_type in ['long_touch', 'wait']:
                plan = self.ai_result.get('plan', {})
                initial_coordinates['duration'] = plan.get('duration', 1.0)
            
            coord_dialog = CoordinateAnnotationDialog(
                self.dialog, 
                self.screenshot_path,
                operation_type=current_type,
                initial_coordinates=initial_coordinates
            )
            
            # 等待用户操作
            self.dialog.wait_window(coord_dialog.dialog)
            
            # 获取标注结果
            if coord_dialog.selected_coordinates:
                coordinates = coord_dialog.selected_coordinates
                
                # 更新起始坐标
                if 'x' in coordinates and 'y' in coordinates:
                    self.x_entry.delete(0, tk.END)
                    self.x_entry.insert(0, str(coordinates['x']))
                    self.y_entry.delete(0, tk.END)
                    self.y_entry.insert(0, str(coordinates['y']))
                
                # 更新终点坐标（如果是scroll或drag操作）
                if current_type in ['scroll', 'drag'] and 'end_x' in coordinates and 'end_y' in coordinates:
                    self.end_x_entry.delete(0, tk.END)
                    self.end_x_entry.insert(0, str(coordinates['end_x']))
                    self.end_y_entry.delete(0, tk.END)
                    self.end_y_entry.insert(0, str(coordinates['end_y']))
                
                # 更新边界框信息（如果有bbox信息）
                if 'bbox' in coordinates:
                    bbox = coordinates['bbox']
                    if hasattr(self, 'bbox_left_entry'):
                        self.bbox_left_entry.delete(0, tk.END)
                        self.bbox_left_entry.insert(0, str(bbox[0]))
                    if hasattr(self, 'bbox_top_entry'):
                        self.bbox_top_entry.delete(0, tk.END)
                        self.bbox_top_entry.insert(0, str(bbox[1]))
                    if hasattr(self, 'bbox_right_entry'):
                        self.bbox_right_entry.delete(0, tk.END)
                        self.bbox_right_entry.insert(0, str(bbox[2]))
                    if hasattr(self, 'bbox_bottom_entry'):
                        self.bbox_bottom_entry.delete(0, tk.END)
                        self.bbox_bottom_entry.insert(0, str(bbox[3]))
                    logger.debug(f"📦 边界框信息已更新: {bbox}")
                
                # 更新时长参数（如果是long_touch或wait操作）
                if current_type in ['long_touch', 'wait'] and 'duration' in coordinates:
                    if hasattr(self, 'duration_entry'):
                        self.duration_entry.delete(0, tk.END)
                        self.duration_entry.insert(0, str(coordinates['duration']))
                
                # 自动刷新可视化标注
                self._auto_generate_visual_label()
                
                # 显示完整的坐标信息（包括bbox信息）
                coord_info = f"坐标: ({coordinates['x']}, {coordinates['y']})"
                if 'bbox' in coordinates:
                    bbox = coordinates['bbox']
                    coord_info += f"\n边界框: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"
                if 'end_x' in coordinates and 'end_y' in coordinates:
                    coord_info += f"\n终点: ({coordinates['end_x']}, {coordinates['end_y']})"
                
                messagebox.showinfo("成功", f"已应用坐标:\n{coord_info}")
                
        except ImportError:
            messagebox.showerror("错误", "坐标标注工具模块未找到")
        except Exception as e:
            messagebox.showerror("错误", f"打开坐标标注工具失败: {e}")
            
    def _preview_json(self):
        """预览修改后的JSON结果"""
        try:
            result = self._get_modified_result()
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            
            # 创建预览窗口
            preview_window = tk.Toplevel(self.dialog)
            preview_window.title("JSON预览")
            preview_window.geometry("600x400")
            preview_window.configure(bg=MODERN_COLORS['bg_primary'])
            
            # JSON文本框
            text_widget = tk.Text(
                preview_window,
                font=("Consolas", 10),
                bg=MODERN_COLORS['white'],
                fg=MODERN_COLORS['dark'],
                wrap="word"
            )
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            text_widget.insert("1.0", json_str)
            text_widget.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成JSON预览失败: {e}")
            
    def _get_modified_result(self):
        """获取修改后的结果"""
        try:
            # 从原始AI结果开始，只更新用户实际修改的部分
            result = self.ai_result.copy()
            logger.debug(f"🔄 开始生成修改后的结果，原始AI结果: {self.ai_result}")
            
            # 更新观察结果（如果用户修改了）
            observation = self.observation_text.get("1.0", tk.END).strip()
            if observation:
                result['observation'] = observation
                logger.debug(f"📝 观察结果已更新: {observation}")
            
            # 更新任务完成状态（如果completed_var存在）
            if self.completed_var:
                # 当操作类型不是End时，强制设置任务完成状态为False
                if self.type_var.get() != "end":
                    result['is_task_completed'] = False
                    logger.debug("✅ 非End操作，任务完成状态已设置为False")
                else:
                    result['is_task_completed'] = self.completed_var.get()
                    logger.debug(f"✅ 任务完成状态已更新: {self.completed_var.get()}")
            
            # 更新完成原因（如果completion_reason_text存在且有内容）
            if hasattr(self, 'completion_reason_text'):
                completion_reason = self.completion_reason_text.get("1.0", tk.END).strip()
                if completion_reason:
                    result['completion_reason'] = completion_reason
                    logger.debug(f"📋 完成原因已更新: {completion_reason}")
            
            # 获取原始计划，只更新用户修改的部分
            plan = result.get('plan', {}).copy()
            logger.debug(f"📋 开始更新计划信息，原始plan: {plan}")
            
            # 更新操作描述（如果用户修改了）
            description = self.description_entry.get().strip()
            if description:
                plan['description'] = description
                logger.debug(f"📝 操作描述已更新: {description}")
            
            # 更新操作类型
            operation_type = self.type_var.get()
            plan['type'] = operation_type
            logger.debug(f"🔧 操作类型已更新: {operation_type}")
            
            # 根据操作类型更新坐标信息
            x_val = self.x_entry.get().strip()
            y_val = self.y_entry.get().strip()
            logger.debug(f"📍 获取坐标输入: x={x_val}, y={y_val}")
            
            if x_val and y_val:
                try:
                    coordinates = [int(x_val), int(y_val)]
                    logger.debug(f"📍 解析坐标成功: {coordinates}")
                    
                    # 根据操作类型设置不同的字段名
                    if self.type_var.get() in ['scroll', 'drag']:
                        # 滑动和拖拽操作使用start_position
                        plan['start_position'] = coordinates
                        logger.debug(f"📍 设置起始位置: {coordinates}")
                        # 移除position字段（如果存在）
                        if 'position' in plan:
                            del plan['position']
                            logger.debug("📍 已移除position字段")
                    else:
                        # 其他操作使用position
                        plan['position'] = coordinates
                        logger.debug(f"📍 设置位置: {coordinates}")
                        # 移除start_position字段（如果存在）
                        if 'start_position' in plan:
                            del plan['start_position']
                            logger.debug("📍 已移除start_position字段")
                except ValueError as e:
                    logger.warning(f"❌ 坐标解析失败: {e}，保持原始值")
                    pass  # 保持原始值
            
            # 更新边界框信息（如果操作类型需要且用户输入了有效数据）
            if self.type_var.get() in ['scroll', 'drag', 'input', 'touch', 'long_touch']:
                try:
                    left_val = self.bbox_left_entry.get().strip()
                    top_val = self.bbox_top_entry.get().strip()
                    right_val = self.bbox_right_entry.get().strip()
                    bottom_val = self.bbox_bottom_entry.get().strip()
                    
                    if all([left_val, top_val, right_val, bottom_val]):
                        bbox_coords = [int(left_val), int(top_val), int(right_val), int(bottom_val)]
                        # 同时保存两种格式，确保兼容性
                        plan['bbox'] = bbox_coords  # [x1, y1, x2, y2] 格式
                        plan['box'] = [[int(left_val), int(top_val)], [int(right_val), int(bottom_val)]]  # [[x1,y1],[x2,y2]] 格式
                        logger.debug(f"📦 边界框信息已保存: bbox={bbox_coords}, box={plan['box']}")
                except ValueError:
                    pass  # 保持原始值
            
            # 更新终点坐标（如果是scroll或drag操作且用户输入了有效坐标）
            if self.type_var.get() in ['scroll', 'drag']:
                end_x_val = self.end_x_entry.get().strip()
                end_y_val = self.end_y_entry.get().strip()
                
                if end_x_val and end_y_val:
                    try:
                        plan['stop_position'] = [int(end_x_val), int(end_y_val)]
                    except ValueError:
                        pass  # 保持原始值
            
            # 更新输入文本（如果是input操作且用户输入了内容）
            if self.type_var.get() == 'input':
                input_text = self.input_text_entry.get().strip()
                if input_text:
                    plan['input_text'] = input_text
            
            # 更新时长参数（如果是long_touch或wait操作且用户输入了有效时长）
            if self.type_var.get() in ['long_touch', 'wait'] and hasattr(self, 'duration_entry'):
                duration_val = self.duration_entry.get().strip()
                if duration_val:
                    try:
                        # 根据操作类型设置不同的时长参数字段
                        if self.type_var.get() == 'wait':
                            plan['wait_time'] = float(duration_val)
                        else:  # long_touch
                            plan['duration'] = float(duration_val)
                    except ValueError:
                        pass  # 保持原始值
            
            # 更新Open操作相关参数（如果用户输入了内容）
            if self.type_var.get() == 'Open':
                app_val = self.app_entry.get().strip()
                package_val = self.package_entry.get().strip()
                if app_val:
                    plan['app'] = app_val
                if package_val:
                    plan['package'] = package_val
            
            # 更新Request操作相关参数（如果用户输入了内容）
            if self.type_var.get() == 'request':
                # 更新提问文本
                request_text = self.request_text_entry.get(1.0, tk.END).strip()
                if request_text:
                    plan['text'] = request_text
                
                # 更新选项列表
                options_text = self.request_options_entry.get(1.0, tk.END).strip()
                if options_text:
                    # 将文本按行分割为选项列表
                    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                    plan['options'] = options
                else:
                    # 如果选项为空，移除options字段
                    if 'options' in plan:
                        del plan['options']
                
                # 获取用户响应（这是关键部分）
                user_response = self.request_response_entry.get().strip()
                if user_response:
                    # 将用户响应添加到结果中，用于传递给后续模型
                    plan['user_response'] = user_response
                    logger.info(f"📝 用户Request响应: {user_response}")
            
            result['plan'] = plan
            logger.debug(f"📋 计划信息更新完成: {plan}")
            # 清除临时文件
            try:
                # 清除临时XML文件
                if hasattr(self, 'xml_path') and self.xml_path and os.path.exists(self.xml_path):
                    temp_xml_path = os.path.join(os.path.dirname(self.screenshot_path), "hierarchy.xml")
                    if os.path.exists(temp_xml_path):
                        os.remove(temp_xml_path)
                        logger.debug(f"🗑️ 已删除临时XML文件: {temp_xml_path}")
                
                # 清除临时标注预览图片
                if hasattr(self, 'screenshot_path') and self.screenshot_path:
                    temp_dir = os.path.dirname(self.screenshot_path)
                    temp_label_path = os.path.join(temp_dir, 'temp_intervention_preview.jpg')
                    if os.path.exists(temp_label_path):
                        os.remove(temp_label_path)
                        logger.debug(f"🗑️ 已删除临时标注预览图片: {temp_label_path}")
            except Exception as e:
                logger.warning(f"⚠️ 清除临时文件失败: {e}")
            # 保持截图路径信息
            if hasattr(self, 'screenshot_path') and self.screenshot_path:
                result['screenshot_path'] = self.screenshot_path
                logger.debug(f"📸 截图路径已保持: {self.screenshot_path}")
            
            # 保持XML路径信息（如果有重新截屏后的XML）
            if hasattr(self, 'xml_path') and self.xml_path:
                result['xml_path'] = self.xml_path
                logger.debug(f"📄 XML路径已保持: {self.xml_path}")
            
            logger.debug(f"✅ 修改后的结果生成完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取修改结果失败: {e}")
            raise Exception(f"获取修改结果失败: {e}")
            
    def _on_approve(self):
        """通过审批"""
        try:
            self.result = self._get_modified_result()
            self.approved = True
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存修改失败: {e}")
            
    def _on_cancel(self):
        """取消操作"""
        self.approved = False
        self.dialog.destroy()
        
    def show(self):
        """显示对话框并等待结果"""
        try:
            self.dialog.wait_window()
            return self.approved, self.result
        except Exception as e:
            logger.debug(f"❌ 对话框显示异常: {e}")
            # 确保返回有效的默认值
            return False, None