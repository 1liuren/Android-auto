#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图像标记工具
负责在截图上绘制简洁的操作标记（仅框和中心点）
"""

from PIL import Image, ImageDraw

class ImageMarker:
    """图像标记器"""
    
    @staticmethod
    def mark_action(screenshot_path: str, output_path: str, position: list = None, 
                   box: list = None, description: str = "") -> bool:
        """在截图上标记操作位置"""
        try:
            img = Image.open(screenshot_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # 获取点击中心位置
            center_x, center_y = ImageMarker._get_center_position(position, box)
            
            if center_x is not None and center_y is not None:
                # 绘制控件整体框和标记点
                ImageMarker._draw_marker(draw, center_x, center_y, box)
                
                print(f"✅ 标记点击位置: ({center_x}, {center_y})")
            else:
                print("⚠️  无法确定点击位置，保存原图")
            
            img.save(output_path)
            return True
            
        except Exception as e:
            print(f"❌ 图像标记失败: {e}")
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
    def _draw_marker(draw: ImageDraw.Draw, center_x: int, center_y: int, box: list = None):
        """绘制简洁的点击标记（控件整体框+标记点）"""
        # 先绘制控件整体框（如果提供了box参数）
        if box:
            widget_coords = ImageMarker._parse_box_coordinates(box)
            if widget_coords:
                x1, y1, x2, y2 = widget_coords
                # 绘制控件整体框（蓝色）
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
                print(f"🔷 控件整体框: ({x1}, {y1}) -> ({x2}, {y2})")
        
        # 绘制点击中心点（红色圆点）
        point_size = 10
        draw.ellipse([center_x - point_size, center_y - point_size, 
                     center_x + point_size, center_y + point_size], 
                    fill="red", outline="red")
        
        # 绘制小范围标记框（30x30像素的方框）
        box_size = 15
        small_box = [center_x - box_size, center_y - box_size, 
                    center_x + box_size, center_y + box_size]
        draw.rectangle(small_box, outline="red", width=2)
        
        # 绘制十字中心线
        line_length = 12
        # 横线
        draw.line([center_x - line_length, center_y, center_x + line_length, center_y], 
                 fill="red", width=2)
        # 竖线
        draw.line([center_x, center_y - line_length, center_x, center_y + line_length], 
                 fill="red", width=2)
    
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
            print("⚠️  box坐标格式错误，跳过控件框绘制")
            
        return None
    
 