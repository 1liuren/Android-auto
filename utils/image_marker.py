#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图像标记工具
负责在截图上绘制简洁的操作标记（仅框和中心点）
"""

from PIL import Image, ImageDraw
import math
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from logger_config import get_logger

logger = get_logger(__name__)

class ImageMarker:
    """图像标记器"""
    
    @staticmethod
    def mark_action(screenshot_path: str, output_path: str, position: list = None, 
                   box: list = None, description: str = "", action_type: str = "tap",
                   swipe_start: list = None, swipe_end: list = None,
                   start_position: list = None, stop_position: list = None) -> bool:
        """在截图上标记操作位置"""
        try:
            img = Image.open(screenshot_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # 兼容旧的操作类型名称
            normalized_type = action_type.lower()
            if normalized_type == "tap":
                normalized_type = "touch"
            elif normalized_type == "typing":
                normalized_type = "input"
            elif normalized_type == "swipe":
                normalized_type = "scroll"
            
            if normalized_type in ["scroll", "drag"]:
                # 优先使用新格式参数
                s_start = start_position or swipe_start
                s_end = stop_position or swipe_end
                
                if s_start and s_end:
                    # 标记滑动/拖动操作
                    ImageMarker._draw_swipe_marker(draw, s_start, s_end, box, normalized_type)
                    operation_name = "滑动" if normalized_type == "scroll" else "拖动"
                    logger.info(f"✅ 标记{operation_name}路径: ({s_start[0]}, {s_start[1]}) -> ({s_end[0]}, {s_end[1]})")
                else:
                    logger.warning(f"⚠️  {normalized_type}操作缺少起始或结束位置，保存原图")
            elif normalized_type in ["touch", "long_touch", "input"]:
                # 标记点击类操作
                center_x, center_y = ImageMarker._get_center_position(position, box)
                
                if center_x is not None and center_y is not None:
                    # 绘制控件整体框和标记点
                    ImageMarker._draw_marker(draw, center_x, center_y, box, normalized_type)
                    operation_name = {"touch": "点击", "long_touch": "长按", "input": "输入"}[normalized_type]
                    logger.info(f"✅ 标记{operation_name}位置: ({center_x}, {center_y})")
                else:
                    logger.warning("⚠️  无法确定操作位置，保存原图")
            elif normalized_type in ["wait", "open", "request", "end"]:
                # 等待、打开和请求操作不需要标记，保存原图
                logger.info("✅ 等待、打开和请求操作无需标记，保存原图")
            else:
                logger.warning(f"⚠️  未知操作类型: {normalized_type}，保存原图")
            
            img.save(output_path)
            return True
            
        except Exception as e:
            logger.error(f"❌ 图像标记失败: {e}")
            return False
    
    @staticmethod
    def _get_center_position(position: list, box: list) -> tuple:
        """获取点击中心位置"""
        if position:
            return int(position[0]), int(position[1])
        elif box:
            if isinstance(box, list) and len(box) >= 2:
                # 检查是否是 [[x1,y1], [x2,y2]] 格式
                if isinstance(box[0], list) and len(box[0]) >= 2:
                    x1, y1 = int(box[0][0]), int(box[0][1])
                    x2, y2 = int(box[1][0]), int(box[1][1])
                    return (x1 + x2) // 2, (y1 + y2) // 2
                # 检查是否是 [x1, y1, x2, y2] 格式
                elif len(box) >= 4:
                    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                    return (x1 + x2) // 2, (y1 + y2) // 2
        return None, None
    
    @staticmethod
    def _draw_marker(draw: ImageDraw.Draw, center_x: int, center_y: int, box: list = None, operation_type: str = "touch"):
        """绘制操作标记（控件整体框+标记点）"""
        # 根据操作类型选择颜色
        colors = {
            "touch": "red",        # 普通点击 - 红色
            "long_touch": "orange", # 长按 - 橙色
            "input": "blue"        # 输入 - 蓝色
        }
        color = colors.get(operation_type, "red")
        
        # 先绘制控件整体框（如果提供了box参数）
        if box:
            widget_coords = ImageMarker._parse_box_coordinates(box)
            if widget_coords:
                x1, y1, x2, y2 = widget_coords
                # 绘制控件整体框
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                logger.debug(f"🔷 控件整体框: ({x1}, {y1}) -> ({x2}, {y2})")
        
        # 绘制操作中心点
        point_size = 12 if operation_type == "long_touch" else 10
        draw.ellipse([center_x - point_size, center_y - point_size, 
                     center_x + point_size, center_y + point_size], 
                    fill=color, outline=color)
        
        # 绘制小范围标记框
        box_size = 18 if operation_type == "long_touch" else 15
        small_box = [center_x - box_size, center_y - box_size, 
                    center_x + box_size, center_y + box_size]
        draw.rectangle(small_box, outline=color, width=2)
        
        # 绘制标识符号
        line_length = 15 if operation_type == "long_touch" else 12
        
        if operation_type == "touch":
            # 普通点击：十字中心线
            draw.line([center_x - line_length, center_y, center_x + line_length, center_y], 
                        fill=color, width=2)
            draw.line([center_x, center_y - line_length, center_x, center_y + line_length], 
                        fill=color, width=2)
        elif operation_type == "long_touch":
            # 长按：双重圆圈
            outer_size = point_size + 6
            draw.ellipse([center_x - outer_size, center_y - outer_size, 
                         center_x + outer_size, center_y + outer_size], 
                        outline=color, width=2)
        elif operation_type == "input":
            # 输入：键盘符号（简化的矩形）
            keyboard_width, keyboard_height = 8, 4
            draw.rectangle([center_x - keyboard_width, center_y - keyboard_height, 
                           center_x + keyboard_width, center_y + keyboard_height], 
                          outline=color, fill=color)
    
    @staticmethod
    def _draw_swipe_marker(draw: ImageDraw.Draw, start_pos: list, end_pos: list, box: list = None, operation_type: str = "scroll"):
        """绘制滑动/拖动操作标记"""
        fx, fy = int(start_pos[0]), int(start_pos[1])
        tx, ty = int(end_pos[0]), int(end_pos[1])
        
        # 根据操作类型选择颜色
        colors = {
            "scroll": {"area": "blue", "line": "blue", "start": "lightblue", "end": "darkblue"},
            "drag": {"area": "purple", "line": "purple", "start": "lightpink", "end": "darkred"}
        }
        color_scheme = colors.get(operation_type, colors["scroll"])
        
        # 先绘制操作区域框（如果提供了box参数）
        if box:
            widget_coords = ImageMarker._parse_box_coordinates(box)
            if widget_coords:
                x1, y1, x2, y2 = widget_coords
                # 绘制操作区域框
                draw.rectangle([x1, y1, x2, y2], outline=color_scheme["area"], width=4)
                operation_name = "滑动" if operation_type == "scroll" else "拖动"
                logger.debug(f"🔷 {operation_name}区域框: ({x1}, {y1}) -> ({x2}, {y2})")
        
        # 绘制操作路径（粗线）
        line_width = 8 if operation_type == "drag" else 6
        draw.line([fx, fy, tx, ty], fill=color_scheme["line"], width=line_width)
        
        # 绘制起点
        start_size = 14 if operation_type == "drag" else 12
        draw.ellipse([fx - start_size, fy - start_size, 
                     fx + start_size, fy + start_size], 
                    outline="green", fill=color_scheme["start"], width=3)
        
        # 绘制终点
        end_size = 14 if operation_type == "drag" else 12
        draw.ellipse([tx - end_size, ty - end_size, 
                     tx + end_size, ty + end_size], 
                    outline="red", fill=color_scheme["end"], width=3)
        
        # 绘制箭头指向（在路径末端）
        # 计算箭头方向
        dx = tx - fx
        dy = ty - fy
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # 单位向量
            ux = dx / length
            uy = dy / length
            
            # 箭头长度
            arrow_length = 20
            arrow_width = 8
            
            # 箭头端点
            arrow_end_x = tx - arrow_length * ux
            arrow_end_y = ty - arrow_length * uy
            
            # 箭头两翼
            perp_x = -uy * arrow_width
            perp_y = ux * arrow_width
            
            arrow_point1_x = arrow_end_x + perp_x
            arrow_point1_y = arrow_end_y + perp_y
            arrow_point2_x = arrow_end_x - perp_x
            arrow_point2_y = arrow_end_y - perp_y
            
            # 绘制箭头
            draw.polygon([
                (tx, ty),
                (arrow_point1_x, arrow_point1_y),
                (arrow_point2_x, arrow_point2_y)
            ], fill="blue", outline="blue")
    
    @staticmethod
    def _parse_box_coordinates(box: list) -> tuple:
        """解析box坐标，返回 (x1, y1, x2, y2) 格式"""
        if not box:
            return None
            
        try:
            if isinstance(box, list) and len(box) >= 2:
                # 检查是否是 [[x1,y1], [x2,y2]] 格式
                if isinstance(box[0], list) and len(box[0]) >= 2:
                    x1, y1 = int(box[0][0]), int(box[0][1])
                    x2, y2 = int(box[1][0]), int(box[1][1])
                    # 确保坐标顺序正确
                    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
                # 检查是否是 [x1, y1, x2, y2] 格式
                elif len(box) >= 4:
                    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                    # 确保坐标顺序正确
                    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        except (ValueError, IndexError, TypeError):
            logger.warning("⚠️  box坐标格式错误，跳过控件框绘制")
            
        return None
    
 