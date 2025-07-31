#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
坐标标注对话框
用于在截图上直接标注坐标点
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from ..utils.ui_helpers import create_custom_button, MODERN_COLORS
from src.logger_config import get_logger

# 获取日志记录器
logger = get_logger("coordinate_annotation_dialog")


class CoordinateAnnotationDialog:
    """坐标标注对话框"""
    
    def __init__(self, parent, screenshot_path, operation_type='touch', initial_coordinates=None):
        logger.debug(f"🚀 初始化坐标标注对话框: 操作类型={operation_type}, 截图路径={screenshot_path}")
        
        self.parent = parent
        self.screenshot_path = screenshot_path
        self.operation_type = operation_type
        self.initial_coordinates = initial_coordinates or {}
        self.selected_coordinates = None
        self.canvas_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        self.canvas_width = 0
        self.canvas_height = 0
        self.image_width = 0
        self.image_height = 0
        
        # 标注相关
        self.annotation_items = []  # 存储标注项目
        self.current_rect = None
        self.start_x = 0
        self.start_y = 0
        
        # 协调状态（用于点标注和框标注的协调）
        self.point_annotation = None  # 存储点标注信息 {'x': orig_x, 'y': orig_y}
        self.rect_annotation = None   # 存储矩形标注信息 {'bbox': [x1,y1,x2,y2], 'center': [cx,cy]}
        
        # 箭头绘制相关（用于scroll和drag）
        self.arrow_start = None
        self.arrow_end = None
        self.is_drawing_arrow = False
        
        logger.debug(f"📍 初始坐标: {self.initial_coordinates}")
        
        # 创建对话框
        self._create_dialog()
        self._load_screenshot()
        
    def _create_dialog(self):
        """创建对话框界面"""
        # 创建顶级窗口
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("📍 坐标标注工具")
        self.dialog.geometry("1000x800")
        self.dialog.configure(bg=MODERN_COLORS['bg_primary'])
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (800 // 2)
        self.dialog.geometry(f"1000x800+{x}+{y}")
        
        # 创建主框架
        main_frame = tk.Frame(self.dialog, bg=MODERN_COLORS['bg_primary'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 工具栏
        self._create_toolbar(main_frame)
        
        # 图像显示区域
        self._create_image_area(main_frame)
        
        # 状态栏
        self._create_status_bar(main_frame)
        
        # 绑定关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _get_instruction_text(self):
        """根据操作类型获取指导文本"""
        instructions = {
            'touch': "🖱️ 点击截图选择触摸点",
            'long_touch': "🖱️ 点击截图选择长按点",
            'input': "🖱️ 点击截图选择输入位置，或拖拽选择输入区域",
            'scroll': "🖱️ 拖拽绘制滑动箭头：起点→终点",
            'drag': "🖱️ 拖拽绘制拖动箭头：起点→终点",
            'wait': "⏱️ 等待操作无需坐标"
        }
        return instructions.get(self.operation_type, "🖱️ 点击截图选择坐标点")
        
    def _create_toolbar(self, parent):
        """创建工具栏"""
        toolbar_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'], relief="solid", bd=1)
        toolbar_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar_frame.columnconfigure(2, weight=1)
        
        # 根据操作类型显示不同的提示
        instruction_text = self._get_instruction_text()
        title_label = tk.Label(
            toolbar_frame,
            text=instruction_text,
            font=("Microsoft YaHei UI", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_secondary']
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # 绘制模式按钮组
        mode_frame = tk.Frame(toolbar_frame, bg=MODERN_COLORS['bg_secondary'])
        mode_frame.grid(row=0, column=2, padx=20, pady=10)
        
        self.draw_mode = tk.StringVar(value="point")
        
        # 根据操作类型显示不同的按钮组合
        if self.operation_type in ['touch', 'long_touch', 'input']:
            # touch类操作：点击和画框
            point_btn = tk.Button(
                mode_frame,
                text="📍 点击",
                command=lambda: self._set_draw_mode("point"),
                font=("Arial", 9),
                relief="raised",
                bg="lightblue"
            )
            point_btn.pack(side="left", padx=(0, 5))
            
            rect_btn = tk.Button(
                mode_frame,
                text="⬜ 画框",
                command=lambda: self._set_draw_mode("rect"),
                font=("Arial", 9),
                relief="flat",
                bg="lightgray"
            )
            rect_btn.pack(side="left")
            
            self.mode_buttons = {'point': point_btn, 'rect': rect_btn}
            
        elif self.operation_type in ['scroll', 'drag']:
            # scroll类操作：画框和画箭头
            rect_btn = tk.Button(
                mode_frame,
                text="⬜ 画框",
                command=lambda: self._set_draw_mode("rect"),
                font=("Arial", 9),
                relief="raised",
                bg="lightblue"
            )
            rect_btn.pack(side="left", padx=(0, 5))
            
            arrow_btn = tk.Button(
                mode_frame,
                text="➡️ 画箭头",
                command=lambda: self._set_draw_mode("arrow"),
                font=("Arial", 9),
                relief="flat",
                bg="lightgray"
            )
            arrow_btn.pack(side="left")
            
            self.mode_buttons = {'rect': rect_btn, 'arrow': arrow_btn}
            self.draw_mode.set("rect")  # scroll类操作默认为画框模式
            
        else:
            # 其他操作类型：只有点击
            point_btn = tk.Button(
                mode_frame,
                text="📍 点击",
                command=lambda: self._set_draw_mode("point"),
                font=("Arial", 9),
                relief="raised",
                bg="lightblue"
            )
            point_btn.pack(side="left")
            
            self.mode_buttons = {'point': point_btn}
        
        # 操作按钮
        button_frame = tk.Frame(toolbar_frame, bg=MODERN_COLORS['bg_secondary'])
        button_frame.grid(row=0, column=3, padx=20, pady=10)
        
        # 清除标注按钮
        clear_btn = create_custom_button(
            button_frame,
            text="🗑️ 清除标注",
            command=self._clear_annotations,
            style_type="warning"
        )
        clear_btn.pack(side="left", padx=(0, 10))
        
        # 确认按钮
        confirm_btn = create_custom_button(
            button_frame,
            text="✅ 确认选择",
            command=self._confirm_selection,
            style_type="success"
        )
        confirm_btn.pack(side="left", padx=(0, 10))
        
        # 取消按钮
        cancel_btn = create_custom_button(
            button_frame,
            text="❌ 取消",
            command=self._on_close,
            style_type="danger"
        )
        cancel_btn.pack(side="left")
        
    def _create_image_area(self, parent):
        """创建图像显示区域"""
        # 创建滚动框架
        canvas_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            highlightthickness=1,
            highlightbackground=MODERN_COLORS['gray']
        )
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.canvas.configure(
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 绑定画布事件
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        
        logger.debug("🖼️ 画布事件绑定完成")
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        
    def _create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'], relief="solid", bd=1)
        status_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)
        
        # 坐标显示
        tk.Label(
            status_frame,
            text="当前坐标:",
            font=("Arial", 10),
            bg=MODERN_COLORS['bg_secondary']
        ).grid(row=0, column=0, padx=10, pady=5)
        
        self.coord_label = tk.Label(
            status_frame,
            text="(0, 0)",
            font=("Arial", 10, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.coord_label.grid(row=0, column=1, sticky="w", pady=5)
        
        # 选中坐标显示
        tk.Label(
            status_frame,
            text="选中坐标:",
            font=("Arial", 10),
            bg=MODERN_COLORS['bg_secondary']
        ).grid(row=0, column=2, padx=(20, 10), pady=5)
        
        self.selected_label = tk.Label(
            status_frame,
            text="未选择",
            font=("Arial", 10, "bold"),
            fg=MODERN_COLORS['success'],
            bg=MODERN_COLORS['bg_secondary']
        )
        self.selected_label.grid(row=0, column=3, sticky="w", pady=5, padx=(0, 10))
        
    def _load_screenshot(self):
        """加载截图"""
        try:
            logger.debug(f"📷 开始加载截图: {self.screenshot_path}")
            
            if not os.path.exists(self.screenshot_path):
                logger.error(f"❌ 截图文件不存在: {self.screenshot_path}")
                messagebox.showerror("错误", f"截图文件不存在: {self.screenshot_path}")
                self._on_close()
                return
                
            # 加载图像
            image = Image.open(self.screenshot_path)
            self.image_width, self.image_height = image.size
            logger.debug(f"📷 原始图像尺寸: {self.image_width}x{self.image_height}")
            
            # 计算缩放比例以适应画布
            max_width = 800
            max_height = 600
            
            scale_x = max_width / self.image_width
            scale_y = max_height / self.image_height
            self.scale_factor = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
            logger.debug(f"📷 缩放比例: {self.scale_factor:.3f} (scale_x: {scale_x:.3f}, scale_y: {scale_y:.3f})")
            
            # 缩放图像
            if self.scale_factor < 1.0:
                new_width = int(self.image_width * self.scale_factor)
                new_height = int(self.image_height * self.scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"📷 图像已缩放至: {new_width}x{new_height}")
            
            self.canvas_width, self.canvas_height = image.size
            
            # 转换为PhotoImage
            self.photo_image = ImageTk.PhotoImage(image)
            
            # 设置画布大小
            self.canvas.configure(
                scrollregion=(0, 0, self.canvas_width, self.canvas_height),
                width=min(self.canvas_width, max_width),
                height=min(self.canvas_height, max_height)
            )
            logger.debug(f"📷 画布配置完成: {self.canvas_width}x{self.canvas_height}")
            
            # 显示图像
            self.canvas_image = self.canvas.create_image(
                0, 0,
                anchor="nw",
                image=self.photo_image
            )
            
            # 如果有初始坐标，显示它们
            self._load_initial_coordinates()
            
            logger.debug("📷 截图加载完成")
            
        except Exception as e:
            logger.error(f"❌ 加载截图失败: {e}")
            messagebox.showerror("错误", f"加载截图失败: {e}")
            self._on_close()
    
    def _load_initial_coordinates(self):
        """加载并显示初始坐标"""
        if not self.initial_coordinates:
            logger.debug("📍 无初始坐标需要加载")
            return
        
        try:
            logger.debug(f"📍 开始加载初始坐标: {self.initial_coordinates}")
            x = self.initial_coordinates.get('x', 0)
            y = self.initial_coordinates.get('y', 0)
            
            if x > 0 and y > 0:
                # 转换为画布坐标
                canvas_x = x * self.scale_factor
                canvas_y = y * self.scale_factor
                logger.debug(f"📍 初始坐标转换: 原始({x}, {y}) -> 画布({canvas_x:.1f}, {canvas_y:.1f})")
                
                if self.operation_type in ['scroll', 'drag']:
                    # 对于滑动和拖拽操作，显示起点和终点
                    end_x = self.initial_coordinates.get('end_x', x)
                    end_y = self.initial_coordinates.get('end_y', y)
                    
                    canvas_end_x = end_x * self.scale_factor
                    canvas_end_y = end_y * self.scale_factor
                    
                    logger.debug(f"🏹 加载初始箭头: 起点({x}, {y}) -> 终点({end_x}, {end_y})")
                    self._create_arrow_annotation((canvas_x, canvas_y), (canvas_end_x, canvas_end_y))
                else:
                    # 对于点击类操作，显示点标注
                    logger.debug(f"📍 加载初始点标注: ({x}, {y})")
                    self._create_point_annotation(canvas_x, canvas_y)
            else:
                logger.debug(f"📍 初始坐标无效: x={x}, y={y}")
                    
        except Exception as e:
            logger.error(f"❌ 加载初始坐标失败: {e}")
            
    def _on_canvas_click(self, event):
        """画布点击事件"""
        # 获取画布坐标
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        logger.debug(f"🖱️ 画布点击事件: 画布坐标({canvas_x:.1f}, {canvas_y:.1f})")
        
        # 检查是否在图像范围内
        if 0 <= canvas_x <= self.canvas_width and 0 <= canvas_y <= self.canvas_height:
            self.start_x = canvas_x
            self.start_y = canvas_y
            
            # 获取当前绘制模式
            draw_mode = self.draw_mode.get()
            logger.debug(f"🎯 当前绘制模式: {draw_mode}")
            
            # 根据绘制模式处理点击
            if draw_mode == "point":
                # 点击模式：直接创建点标注
                logger.debug("📍 点击模式：创建点标注")
                self._create_point_annotation(canvas_x, canvas_y)
            elif draw_mode == "arrow":
                # 箭头模式：开始绘制箭头
                if not self.is_drawing_arrow:
                    logger.debug("🏹 箭头模式：开始绘制箭头")
                    self.is_drawing_arrow = True
                    self.arrow_start = (canvas_x, canvas_y)
                else:
                    logger.debug("🏹 箭头模式：已在绘制中")
            elif draw_mode == "rect":
                # 矩形模式：准备绘制矩形（在拖拽时才真正绘制）
                logger.debug("📦 矩形模式：准备绘制矩形")
        else:
            logger.debug(f"⚠️ 点击位置超出图像范围: ({canvas_x:.1f}, {canvas_y:.1f})，图像尺寸: {self.canvas_width}x{self.canvas_height}")
            
    def _on_canvas_drag(self, event):
        """画布拖拽事件"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # 检查是否在图像范围内
        if 0 <= canvas_x <= self.canvas_width and 0 <= canvas_y <= self.canvas_height:
            if self.operation_type in ['scroll', 'drag'] and self.is_drawing_arrow:
                # 绘制箭头预览
                if self.current_rect:
                    self.canvas.delete(self.current_rect)
                
                # 绘制箭头线
                self.current_rect = self.canvas.create_line(
                    self.arrow_start[0], self.arrow_start[1], canvas_x, canvas_y,
                    fill="green", width=3, arrow=tk.LAST, arrowshape=(16, 20, 6)
                )
                logger.debug(f"🏹 绘制箭头预览: 起点({self.arrow_start[0]:.1f},{self.arrow_start[1]:.1f}) -> 当前({canvas_x:.1f},{canvas_y:.1f})")
            elif self.draw_mode.get() == "rect":
                # 矩形绘制模式：绘制矩形预览
                if self.current_rect:
                    self.canvas.delete(self.current_rect)
                    
                self.current_rect = self.canvas.create_rectangle(
                    self.start_x, self.start_y, canvas_x, canvas_y,
                    outline="blue",
                    width=2,
                    fill="",
                    stipple="gray50"
                )
                logger.debug(f"📦 绘制矩形预览: 起点({self.start_x:.1f},{self.start_y:.1f}) -> 当前({canvas_x:.1f},{canvas_y:.1f})")
            
    def _on_canvas_release(self, event):
        """画布释放事件"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        logger.debug(f"🖱️ 画布释放事件: 画布坐标({canvas_x:.1f}, {canvas_y:.1f})")
        
        # 检查是否在图像范围内
        if 0 <= canvas_x <= self.canvas_width and 0 <= canvas_y <= self.canvas_height:
            if self.operation_type in ['scroll', 'drag'] and self.is_drawing_arrow:
                # 完成箭头绘制
                distance = ((canvas_x - self.arrow_start[0])**2 + (canvas_y - self.arrow_start[1])**2)**0.5
                logger.debug(f"🏹 箭头绘制距离: {distance:.1f}px")
                if distance > 10:
                    self.arrow_end = (canvas_x, canvas_y)
                    logger.debug(f"🏹 完成箭头绘制: 起点({self.arrow_start[0]:.1f},{self.arrow_start[1]:.1f}) -> 终点({canvas_x:.1f},{canvas_y:.1f})")
                    self._create_arrow_annotation(self.arrow_start, self.arrow_end)
                else:
                    logger.debug("🏹 箭头绘制距离太短，忽略")
                self.is_drawing_arrow = False
            elif self.draw_mode.get() == "rect":
                # 矩形绘制模式：如果拖拽距离足够大，创建矩形标注
                distance = ((canvas_x - self.start_x)**2 + (canvas_y - self.start_y)**2)**0.5
                logger.debug(f"📦 矩形绘制距离: {distance:.1f}px")
                if distance > 5:
                    # 创建矩形标注（使用中心点）
                    center_x = (self.start_x + canvas_x) / 2
                    center_y = (self.start_y + canvas_y) / 2
                    logger.debug(f"📦 完成矩形绘制: 区域({self.start_x:.1f},{self.start_y:.1f},{canvas_x:.1f},{canvas_y:.1f}) 中心({center_x:.1f},{center_y:.1f})")
                    self._create_rect_annotation(self.start_x, self.start_y, canvas_x, canvas_y, center_x, center_y)
                else:
                    logger.debug("📦 矩形绘制距离太短，忽略")
            
        # 清除临时绘制项
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            logger.debug("🗑️ 清除临时绘制项")
            
    def _on_canvas_motion(self, event):
        """鼠标移动事件"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # 转换为原始图像坐标
        if 0 <= canvas_x <= self.canvas_width and 0 <= canvas_y <= self.canvas_height:
            orig_x = int(canvas_x / self.scale_factor)
            orig_y = int(canvas_y / self.scale_factor)
            self.coord_label.config(text=f"({orig_x}, {orig_y})")
            
            # 如果正在绘制箭头，更新临时箭头
            if self.is_drawing_arrow and self.arrow_start:
                if self.current_rect:
                    self.canvas.delete(self.current_rect)
                self.current_rect = self.canvas.create_line(
                    self.arrow_start[0], self.arrow_start[1], canvas_x, canvas_y,
                    fill="green", width=2, arrow=tk.LAST, dash=(4, 4)
                )
        else:
            self.coord_label.config(text="(超出范围)")
            
    def _canvas_to_original_coords(self, canvas_x, canvas_y):
        """将画布坐标转换为原始图像坐标"""
        orig_x = int(canvas_x / self.scale_factor)
        orig_y = int(canvas_y / self.scale_factor)
        return orig_x, orig_y
    
    def _update_selected_coordinates(self, x, y, bbox=None, end_x=None, end_y=None):
        """更新选中坐标信息"""
        self.selected_coordinates = {
            'x': x,
            'y': y,
            'bbox': bbox or [x - 50, y - 25, x + 50, y + 25],
            'x1': bbox[0] if bbox else x - 50,
            'y1': bbox[1] if bbox else y - 25,
            'x2': bbox[2] if bbox else x + 50,
            'y2': bbox[3] if bbox else y + 25
        }
        
        if end_x is not None and end_y is not None:
            self.selected_coordinates.update({
                'end_x': end_x,
                'end_y': end_y,
                'start_position': [x, y],
                'end_position': [end_x, end_y]
            })
            logger.debug(f"📍 添加终点坐标: ({end_x}, {end_y})")
            
        logger.debug(f"📍 坐标信息已更新: {self.selected_coordinates}")
        self._update_status_display()
    
    def _update_status_display(self):
        """更新状态栏显示"""
        if not self.selected_coordinates:
            self.selected_label.config(text="未选择")
            return
            
        x, y = self.selected_coordinates['x'], self.selected_coordinates['y']
        bbox = self.selected_coordinates['bbox']
        
        if 'end_x' in self.selected_coordinates:
            end_x, end_y = self.selected_coordinates['end_x'], self.selected_coordinates['end_y']
            text = f"起点: ({x}, {y}) → 终点: ({end_x}, {end_y}) 区域: [{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}]"
        else:
            if bbox[2] - bbox[0] > 100 or bbox[3] - bbox[1] > 50:  # 大于默认bbox说明是矩形
                text = f"中心: ({x}, {y}) 区域: [{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}]"
            else:
                text = f"({x}, {y}) 区域: [{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}]"
                
        self.selected_label.config(text=text)
    
    def _create_point_annotation(self, canvas_x, canvas_y):
        """创建点标注"""
        orig_x, orig_y = self._canvas_to_original_coords(canvas_x, canvas_y)
        logger.debug(f"📍 创建点标注: 画布坐标({canvas_x:.1f}, {canvas_y:.1f}) -> 原始坐标({orig_x}, {orig_y})")
        
        # 不自动清除标注，让用户手动控制
        # if self.draw_mode.get() != 'point':
        #     self._clear_annotations()
        
        # 绘制点标记
        point_size = 8
        point_id = self.canvas.create_oval(
            canvas_x - point_size, canvas_y - point_size,
            canvas_x + point_size, canvas_y + point_size,
            fill='red', outline='darkred', width=2
        )
        
        text_id = self.canvas.create_text(
            canvas_x, canvas_y - 20,
            text=f"({orig_x}, {orig_y})",
            fill='red', font=('Arial', 10, 'bold')
        )
        
        self.annotation_items.extend([point_id, text_id])
        logger.debug(f"📍 点标注元素已添加，当前标注项目数量: {len(self.annotation_items)}")
        
        # 记录点标注状态
        self.point_annotation = {'x': orig_x, 'y': orig_y}
        
        # 确定使用的bbox：如果已有矩形标注，使用矩形的bbox；否则生成默认bbox
        if self.rect_annotation:
            bbox = self.rect_annotation['bbox']
            logger.debug(f"📦 使用已有矩形标注的边界框: {bbox}")
        else:
            bbox_size = 50
            bbox = [orig_x - bbox_size, orig_y - 25, orig_x + bbox_size, orig_y + 25]
            logger.debug(f"📦 生成点标注默认边界框: {bbox}")
        
        self._update_selected_coordinates(orig_x, orig_y, bbox=bbox)
        
    def _create_rect_annotation(self, x1, y1, x2, y2, center_x, center_y):
        """创建矩形标注"""
        # 确定使用的中心点：如果已有点标注，使用点标注的坐标；否则使用计算的中心点
        if self.point_annotation:
            orig_center_x = self.point_annotation['x']
            orig_center_y = self.point_annotation['y']
            logger.debug(f"📦 创建矩形标注: 使用已有点标注坐标作为中心点({orig_center_x}, {orig_center_y})")
        else:
            orig_center_x, orig_center_y = self._canvas_to_original_coords(center_x, center_y)
            logger.debug(f"📦 创建矩形标注: 画布区域({x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}) 中心({center_x:.1f},{center_y:.1f}) -> 原始中心({orig_center_x},{orig_center_y})")
        
        # 不自动清除标注，让用户手动控制
        # if self.draw_mode.get() != 'rect':
        #     self._clear_annotations()
        
        # 创建矩形
        rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="blue", width=2, fill="", stipple="gray25"
        )
        
        # 创建中心点标记
        size = 8
        cross_h = self.canvas.create_line(
            center_x - size, center_y, center_x + size, center_y,
            fill="red", width=3
        )
        cross_v = self.canvas.create_line(
            center_x, center_y - size, center_x, center_y + size,
            fill="red", width=3
        )
        
        # 创建中心点圆圈
        circle = self.canvas.create_oval(
            center_x - size, center_y - size,
            center_x + size, center_y + size,
            outline="red", width=2, fill="yellow"
        )
        
        # 创建坐标文本
        text = self.canvas.create_text(
            center_x, center_y - 25,
            text=f"中心: ({orig_center_x}, {orig_center_y})",
            fill="red",
            font=("Arial", 10, "bold"),
            anchor="center"
        )
        
        # 保存标注项目
        self.annotation_items.extend([rect, cross_h, cross_v, circle, text])
        logger.debug(f"📦 矩形标注元素已添加，当前标注项目数量: {len(self.annotation_items)}")
        
        # 更新选中坐标（包含边界框信息）
        orig_x1 = int(min(x1, x2) / self.scale_factor)
        orig_y1 = int(min(y1, y2) / self.scale_factor)
        orig_x2 = int(max(x1, x2) / self.scale_factor)
        orig_y2 = int(max(y1, y2) / self.scale_factor)
        
        bbox = [orig_x1, orig_y1, orig_x2, orig_y2]
        logger.debug(f"📦 生成矩形标注边界框: {bbox}")
        
        # 记录矩形标注状态
        self.rect_annotation = {
            'bbox': bbox,
            'center': [orig_center_x, orig_center_y]
        }
        
        self._update_selected_coordinates(orig_center_x, orig_center_y, bbox=bbox)
    
    def _create_arrow_annotation(self, start_pos, end_pos):
        """创建箭头标注（用于scroll和drag操作）"""
        orig_start_x, orig_start_y = self._canvas_to_original_coords(start_pos[0], start_pos[1])
        orig_end_x, orig_end_y = self._canvas_to_original_coords(end_pos[0], end_pos[1])
        logger.debug(f"🏹 创建箭头标注: 画布起点({start_pos[0]:.1f},{start_pos[1]:.1f}) -> 原始起点({orig_start_x},{orig_start_y})")
        logger.debug(f"🏹 创建箭头标注: 画布终点({end_pos[0]:.1f},{end_pos[1]:.1f}) -> 原始终点({orig_end_x},{orig_end_y})")
        
        # 规整箭头为水平或垂直方向
        dx = abs(end_pos[0] - start_pos[0])
        dy = abs(end_pos[1] - start_pos[1])
        
        # 判断是水平还是垂直方向（哪个差值更大就保持那个方向）
        if dx > dy:  # 水平方向
            # 保持水平方向，垂直方向取起点的值
            end_pos = (end_pos[0], start_pos[1])
            orig_end_y = orig_start_y
        else:  # 垂直方向
            # 保持垂直方向，水平方向取起点的值
            end_pos = (start_pos[0], end_pos[1])
            orig_end_x = orig_start_x
            
        logger.debug(f"🏹 规整后的箭头: 起点({start_pos[0]:.1f},{start_pos[1]:.1f}) -> 终点({end_pos[0]:.1f},{end_pos[1]:.1f})")
        
        # 创建箭头线
        arrow = self.canvas.create_line(
            start_pos[0], start_pos[1], end_pos[0], end_pos[1],
            fill="green", width=4, arrow=tk.LAST, arrowshape=(16, 20, 6)
        )
        
        # 创建起点标记
        start_circle = self.canvas.create_oval(
            start_pos[0] - 8, start_pos[1] - 8,
            start_pos[0] + 8, start_pos[1] + 8,
            outline="green", width=3, fill="lightgreen"
        )
        
        # 创建终点标记
        end_circle = self.canvas.create_oval(
            end_pos[0] - 8, end_pos[1] - 8,
            end_pos[0] + 8, end_pos[1] + 8,
            outline="red", width=3, fill="lightcoral"
        )
        
        # 创建坐标文本
        start_text = self.canvas.create_text(
            start_pos[0], start_pos[1] - 25,
            text=f"起点: ({orig_start_x}, {orig_start_y})",
            fill="green",
            font=("Arial", 9, "bold"),
            anchor="center"
        )
        
        end_text = self.canvas.create_text(
            end_pos[0], end_pos[1] + 25,
            text=f"终点: ({orig_end_x}, {orig_end_y})",
            fill="red",
            font=("Arial", 9, "bold"),
            anchor="center"
        )
        
        # 保存标注项目
        self.annotation_items.extend([arrow, start_circle, end_circle, start_text, end_text])
        logger.debug(f"🏹 箭头标注元素已添加，当前标注项目数量: {len(self.annotation_items)}")
        
        # 检查是否已经有用户画的框（矩形标注），如果有则保持用户的bbox
        existing_bbox = None
        if hasattr(self, 'selected_coordinates') and self.selected_coordinates and 'bbox' in self.selected_coordinates:
            # 检查是否是用户画的框（大于默认bbox说明是用户画的）
            current_bbox = self.selected_coordinates['bbox']
            if (current_bbox[2] - current_bbox[0] > 100 or current_bbox[3] - current_bbox[1] > 50):
                existing_bbox = current_bbox
                logger.debug(f"🏹 保持用户画的框: {existing_bbox}")
        
        # 如果没有用户画的框，则生成基于箭头的边界框
        if existing_bbox is None:
            min_x = min(orig_start_x, orig_end_x) - 25
            min_y = min(orig_start_y, orig_end_y) - 25
            max_x = max(orig_start_x, orig_end_x) + 25
            max_y = max(orig_start_y, orig_end_y) + 25
            existing_bbox = [min_x, min_y, max_x, max_y]
            logger.debug(f"🏹 生成箭头默认边界框: {existing_bbox}")
        
        self._update_selected_coordinates(orig_start_x, orig_start_y, bbox=existing_bbox, end_x=orig_end_x, end_y=orig_end_y)
        
    def _clear_annotations(self):
        """清除所有标注（仅在用户点击清除按钮时调用）"""
        logger.debug(f"🗑️ 开始清除标注，当前标注项目数量: {len(self.annotation_items)}")
        
        cleared_count = 0
        for item in self.annotation_items:
            self.canvas.delete(item)
            cleared_count += 1
        self.annotation_items = []
        
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            cleared_count += 1
            
        # 清除协调状态
        self.point_annotation = None
        self.rect_annotation = None
        
        self.selected_coordinates = None
        self.selected_label.config(text="未选择")
        
        logger.debug(f"🗑️ 标注清除完成，共清除 {cleared_count} 个元素，协调状态已重置")
        
    def _confirm_selection(self):
        """确认选择"""
        if self.selected_coordinates:
            logger.debug(f"✅ 用户确认选择坐标: {self.selected_coordinates}")
            self.dialog.destroy()
        else:
            logger.warning("⚠️ 用户尝试确认选择但未选择任何坐标")
            messagebox.showwarning("警告", "请先选择一个坐标点")
            
    def _set_draw_mode(self, mode):
        """设置绘制模式"""
        old_mode = self.draw_mode.get()
        logger.debug(f"🔄 切换绘制模式: {old_mode} -> {mode}")
        
        # 不自动清除标注，让用户手动控制
        # if self.draw_mode.get() != mode:
        #     self._clear_annotations()
            
        self.draw_mode.set(mode)
        
        # 更新按钮样式
        for btn_mode, button in self.mode_buttons.items():
            if btn_mode == mode:
                button.config(relief="raised", bg="lightblue")
            else:
                button.config(relief="flat", bg="lightgray")
        
        logger.debug(f"🔄 绘制模式切换完成: {mode}，按钮样式已更新")
                
        # 重置绘制状态
        self.is_drawing_arrow = False
        self.arrow_start = None
        self.arrow_end = None
        
        # 清除临时绘制元素（如正在绘制的矩形）
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
        

        
    def _on_close(self):
        """关闭对话框"""
        logger.debug("❌ 用户关闭坐标标注对话框，未确认选择")
        self.selected_coordinates = None
        self.dialog.destroy()