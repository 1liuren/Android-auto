#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理器类
功能：字符分割、字符交换、图像处理
"""

import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
import re
from PIL import Image, ImageDraw, ImageFont

class TextProcessor:
    """
    文本处理器类
    
    主要功能：
    1. 检测文本区域的背景颜色
    2. 水平方向文本定位
    3. 整体文本替换
    4. 生成最终结果
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        初始化文本处理器
        
        Args:
            debug_mode: 是否启用调试模式
        """
        self.debug_mode = debug_mode
        # 添加历史记录功能
        self.replacement_history = {}  # 格式: {target_text: replacement_text}
        
    def process_text(self, 
                    img_path: str,
                    text_region_box: List[List[int]],
                    target_text: str,
                    replace_text: str = None,
                    output_path: str = "Final_Result.jpg") -> bool:
        """
        处理文本的主函数
        
        Args:
            img_path: 图像路径
            text_region_box: 文本区域边界框 [[x1,y1], [x2,y2]]
            target_text: 目标文本字符串
            replace_text: 替换文本（如果有历史记录则忽略此参数）
            output_path: 输出图像路径
            
        Returns:
            bool: 是否处理成功
        """
        # 检查历史记录
        if target_text in self.replacement_history:
            actual_replace_text = self.replacement_history[target_text]
            print(f"使用历史记录: {target_text} -> {actual_replace_text}")
        else:
            actual_replace_text = replace_text if replace_text else target_text
            # 记录到历史
            self.replacement_history[target_text] = actual_replace_text
            print(f"新建记录: {target_text} -> {actual_replace_text}")
        
        # 1. 加载原始图像
        img = self._imread_unicode(img_path)
        if img is None:
            print("无法读取图片，请检查路径！")
            return False
            
        # 2. 提取文本区域
        x1, y1 = text_region_box[0]
        x2, y2 = text_region_box[1]
        text_roi = img[y1:y2, x1:x2].copy()
        
        if self.debug_mode:
            cv2.imwrite("debug_text_roi.jpg", text_roi)
            
        # 3. 检测背景颜色（精确采样）
        bg_color = self._detect_background_color(text_roi)
        
        # 4. 检测文本水平区域（更新调用）
        text_y, text_height, text_center_y = self._detect_text_horizontal_region(text_roi)
        
        # 5. 检测文字颜色（随机采样与背景不同的颜色）
        text_color = self._detect_text_color(text_roi, bg_color)
        
        # 6. 生成替换文本图像（修正垂直位置）
        replaced_roi = self._generate_text_image(text_roi, actual_replace_text, bg_color, text_color, text_y, text_height)
        
        if self.debug_mode:
            cv2.imwrite("debug_replaced.jpg", replaced_roi)
            
        # 7. 替换回原图
        result_img = self._replace_back_to_original(img, replaced_roi, text_region_box)
        
        # 8. 保存结果
        success = self._imwrite_unicode(output_path, result_img)
        if success:
            print(f"处理完成，结果已保存至: {output_path}")
        else:
            print(f"保存失败: {output_path}")
        
        return success
    
    def _detect_background_color(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """
        精确检测背景颜色（使用边缘区域采样）
        
        Args:
            roi: 文本区域图像
            
        Returns:
            tuple: BGR背景颜色
        """
        h, w = roi.shape[:2]
        
        # 采样边缘区域的像素
        edge_pixels = []
        
        # 上边缘
        edge_pixels.extend(roi[0:3, :].reshape(-1, 3))
        # 下边缘
        edge_pixels.extend(roi[h-3:h, :].reshape(-1, 3))
        # 左边缘
        edge_pixels.extend(roi[:, 0:3].reshape(-1, 3))
        # 右边缘
        edge_pixels.extend(roi[:, w-3:w].reshape(-1, 3))
        
        edge_pixels = np.array(edge_pixels)
        
        # 使用众数作为背景颜色
        from scipy import stats
        bg_b = int(stats.mode(edge_pixels[:, 0], keepdims=True)[0][0])
        bg_g = int(stats.mode(edge_pixels[:, 1], keepdims=True)[0][0])
        bg_r = int(stats.mode(edge_pixels[:, 2], keepdims=True)[0][0])
        
        print(f"检测到背景颜色: BGR({bg_b}, {bg_g}, {bg_r})")
        return (bg_b, bg_g, bg_r)
    
    def _detect_text_color(self, roi: np.ndarray, bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        通过随机采样检测与背景不同的文字颜色
        
        Args:
            roi: 文本区域图像
            bg_color: 背景颜色
            
        Returns:
            tuple: BGR文字颜色
        """
        h, w = roi.shape[:2]
        bg_b, bg_g, bg_r = bg_color
        
        # 随机采样中心区域的像素
        center_h_start = h // 4
        center_h_end = 3 * h // 4
        center_w_start = w // 4
        center_w_end = 3 * w // 4
        
        center_roi = roi[center_h_start:center_h_end, center_w_start:center_w_end]
        center_pixels = center_roi.reshape(-1, 3)
        
        # 找到与背景颜色差异最大的像素
        color_distances = []
        for pixel in center_pixels:
            distance = np.sqrt(sum((pixel - np.array([bg_b, bg_g, bg_r])) ** 2))
            color_distances.append((distance, pixel))
        
        # 选择距离背景色最远的颜色作为文字颜色
        # 选取距离最远的10%个点
        top_10 = sorted(color_distances, key=lambda x: x[0], reverse=True)[: int(len(center_pixels) * 0.1)]
        # 计算这1000个点的平均颜色值
        avg_color = np.mean([x[1] for x in top_10], axis=0)
        text_color = tuple(map(int, avg_color))
        
        print(f"检测到文字颜色: BGR{text_color}")
        return text_color
    
    def _detect_text_horizontal_region(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """
        改进的文本区域检测（返回更精确的文本信息）
        
        Args:
            roi: 文本区域图像
            
        Returns:
            tuple: (文本起始y坐标, 文本高度, 文本中心y坐标)
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # 方法1: 使用投影法检测文本行
        # 计算垂直投影（每行的非背景像素数量）
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 计算每行的像素密度
        row_densities = []
        for i in range(h):
            row = binary[i, :]
            density = np.sum(row > 0) / w  # 非零像素比例
            row_densities.append(density)
        
        # 使用密度阈值找到文本区域
        max_density = max(row_densities)
        density_threshold = max_density * 0.1  # 10%的最大密度作为阈值
        
        text_rows = [i for i, density in enumerate(row_densities) if density > density_threshold]
        
        if text_rows:
            text_y = min(text_rows)
            text_bottom = max(text_rows)
            text_height = text_bottom - text_y + 1
            text_center_y = (text_y + text_bottom) // 2
        else:
            # 备用方法：使用轮廓检测
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # 找到最大的轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w_cont, h_cont = cv2.boundingRect(largest_contour)
                text_y = y
                text_height = h_cont
                text_center_y = y + h_cont // 2
            else:
                # 最后的备用方案
                text_y = h // 4
                text_height = h // 2
                text_center_y = h // 2
        
        print(f"检测到文本区域: y={text_y}, height={text_height}, center_y={text_center_y}")
        print(f"行密度分布: max={max_density:.3f}, threshold={density_threshold:.3f}")
        
        return text_y, text_height, text_center_y
    
    def _estimate_original_font_size(self, roi: np.ndarray, text_y: int, text_height: int) -> int:
        """
        估算原始文字的字体大小
        
        Args:
            roi: 文本区域图像
            text_y: 文本起始y坐标
            text_height: 文本高度
            
        Returns:
            int: 估算的字体大小
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 提取文本区域
        text_region = gray[text_y:text_y+text_height, :]
        
        # 二值化
        _, binary = cv2.threshold(text_region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 查找轮廓来估算字符大小
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # 计算所有字符轮廓的平均高度
            char_heights = []
            for contour in contours:
                _, _, _, h = cv2.boundingRect(contour)
                if h > text_height * 0.3:  # 过滤噪声，只考虑较大的轮廓
                    char_heights.append(h)
            
            if char_heights:
                avg_char_height = max(char_heights)
                # 根据字符高度估算字体大小（经验公式）
                estimated_font_size = int(avg_char_height * 1) + 3
                print(f"字符高度分析: 平均={avg_char_height:.1f}, 估算字体={estimated_font_size}")
                return max(16, estimated_font_size)
        
        # 备用方案：基于文本高度
        return max(20, int(text_height * 0.9))
    
    def _generate_text_image(self, roi: np.ndarray, text: str, bg_color: Tuple[int, int, int], 
                           text_color: Tuple[int, int, int], text_y: int, text_height: int, 
                           font_path: str = None) -> np.ndarray:
        """
        生成替换文本图像（优化字体大小和位置）
        
        Args:
            roi: 原始文本区域
            text: 要生成的文本
            bg_color: 背景颜色
            text_color: 文字颜色
            text_y: 文本起始y坐标
            text_height: 文本高度
            font_path: 字体文件路径
            
        Returns:
            np.ndarray: 生成的文本图像
        """
        h, w = roi.shape[:2]
        
        # 创建背景画布
        canvas = np.full((h, w, 3), bg_color, dtype=np.uint8)
        
        # 改进的字体大小估算
        estimated_font_size = self._estimate_original_font_size(roi, text_y, text_height)
        
        # 动态确定字体路径
        if font_path is None:
            font_path = self._get_font_path()
        
        try:
            # 使用PIL绘制中文文字
            pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            
            if os.path.exists(font_path):
                # 迭代调整字体大小以获得最佳匹配
                best_font_size = estimated_font_size
                
                
                # 最终字体
                font = ImageFont.truetype(font_path, best_font_size)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height_actual = bbox[3] - bbox[1]
                
                # 改进的位置计算
                text_x = (w - text_width) // 2
                
                # 重新检测文本中心位置
                _, _, text_center_y = self._detect_text_horizontal_region(roi)
                
                # 计算垂直位置：让新文字的中心对齐原文字的中心
                text_baseline_y = text_center_y - text_height_actual // 2
                
                # 边界检查
                # text_baseline_y = max(0, min(h - text_height_actual, text_baseline_y))
                text_baseline_y = text_y - 4 
                
                print(f"最终文本参数:")
                print(f"  字体大小: {best_font_size}")
                print(f"  文本尺寸: {text_width}x{text_height_actual}")
                print(f"  位置: ({text_x}, {text_baseline_y})")
                print(f"  原文中心: {text_center_y}, 新文中心: {text_baseline_y + text_height_actual//2}")
                
                # 转换颜色格式 (BGR -> RGB)
                text_color_rgb = (text_color[2], text_color[1], text_color[0])
                
                # 绘制文本
                draw.text((text_x, text_baseline_y), text, font=font, fill=text_color_rgb)
                
                # 转换回OpenCV格式
                canvas = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                
            else:
                print("警告：未找到中文字体文件，使用默认字体")
                # 回退到OpenCV字体
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = estimated_font_size / 30.0
                (text_width, text_height_actual), baseline = cv2.getTextSize(text, font, font_scale, 2)
                
                available_width = int(w * 0.95)
                if text_width > available_width:
                    font_scale = font_scale * available_width / text_width
                    (text_width, text_height_actual), baseline = cv2.getTextSize(text, font, font_scale, 2)
                
                text_x = (w - text_width) // 2
                text_baseline_y = text_y + (text_height + text_height_actual) // 2
                text_baseline_y = max(text_height_actual, min(h - baseline, text_baseline_y))
                
                cv2.putText(canvas, text, (text_x, text_baseline_y), font, font_scale, text_color, 2, cv2.LINE_AA)
                
        except Exception as e:
            print(f"绘制文字时出错: {e}")
            # 出错时返回原始画布
            pass
        
        return canvas
    
    def _get_font_path(self) -> str:
        """
        动态获取字体文件路径，兼容开发环境和exe打包环境
        
        Returns:
            str: 字体文件的完整路径
        """
        import sys
        
        # 字体文件名
        font_filename = "方正兰亭中黑_GBK.TTF"
        
        # 检测是否在PyInstaller打包的exe中运行
        if getattr(sys, 'frozen', False):
            # 在exe环境中，使用_MEIPASS临时目录
            base_path = sys._MEIPASS
            font_path = os.path.join(base_path, "utils", font_filename)
        else:
            # 在开发环境中，使用相对路径
            font_path = os.path.join("utils", font_filename)
        
        print(f"字体路径: {font_path}")
        print(f"字体文件存在: {os.path.exists(font_path)}")
        
        # 如果主字体不存在，尝试备用字体
        if not os.path.exists(font_path):
            backup_font = "SIMHEI.TTF"
            if getattr(sys, 'frozen', False):
                backup_path = os.path.join(sys._MEIPASS, "utils", backup_font)
            else:
                backup_path = os.path.join("utils", backup_font)
            
            if os.path.exists(backup_path):
                print(f"使用备用字体: {backup_path}")
                return backup_path
        
        return font_path
    
    def _replace_back_to_original(self, original_img: np.ndarray, processed_roi: np.ndarray, 
                                region_box: List[List[int]]) -> np.ndarray:
        """
        将处理后的ROI替换回原图
        
        Args:
            original_img: 原始图像
            processed_roi: 处理后的ROI
            region_box: 区域边界框
            
        Returns:
            替换后的图像
        """
        result_img = original_img.copy()
        x1, y1 = region_box[0]
        x2, y2 = region_box[1]
        w, h = x2 - x1, y2 - y1
        
        # 调整尺寸并替换
        resized_roi = cv2.resize(processed_roi, (w, h))
        result_img[y1:y2, x1:x2] = resized_roi
        
        return result_img
    
    def _imread_unicode(self, img_path: str):
        """
        解决OpenCV在Windows下无法读取中文路径的问题
        
        Args:
            img_path: 图片路径
            
        Returns:
            np.ndarray: 图像数据，失败返回None
        """
        try:
            img_array = np.fromfile(img_path, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"读取图片失败: {e}")
            return None
    
    def _imwrite_unicode(self, img_path: str, img):
        """
        解决OpenCV在Windows下无法写入中文路径的问题
        
        Args:
            img_path: 图片路径
            img: 图像数据
            
        Returns:
            bool: 是否写入成功
        """
        try:
            # 获取文件扩展名
            ext = os.path.splitext(img_path)[1]
            # 编码图像数据
            success, img_encoded = cv2.imencode(ext, img)
            if success:
                # 直接写入文件(如果存在则覆盖)
                with open(img_path, 'wb') as f:
                    f.write(img_encoded.tobytes())
                return True
            return False
        except Exception as e:
            print(f"写入图片失败: {e}")
            return False

    # 保留原有的测试方法，但简化逻辑
    def test_character_segmentation(self, img_path: str, text_region_box: List[List[int]], target_text: Optional[str] = None):
        """
        测试文本区域检测功能
        
        Args:
            img_path: 图像路径
            text_region_box: 测试区域
            target_text: (可选) 目标文本
        """
        print("\n🧪 测试文本区域检测功能...")
        
        # 加载图像
        img = self._imread_unicode(img_path)
        if img is None:
            print("❌ 无法加载测试图像")
            return
        
        # 提取区域
        x1, y1 = text_region_box[0]
        x2, y2 = text_region_box[1]
        roi = img[y1:y2, x1:x2].copy()
        
        print(f"📏 测试区域尺寸: {x2-x1}x{y2-y1}")
        if target_text:
            print(f"🎯 目标文本: '{target_text}'")
        
        # 检测背景颜色
        bg_color = self._detect_background_color(roi)
        print(f"🎨 背景颜色: {bg_color}")
        
        # 检测文本水平区域
        text_region = self._detect_text_horizontal_region(roi)
        print(f"📏 文本水平区域: {text_region}")
        
        # 保存测试结果
        test_output = "test_text_detection_result.jpg"
        # 在ROI上标记检测到的文本区域
        test_img = roi.copy()
        top_y, bottom_y = text_region
        cv2.rectangle(test_img, (0, top_y), (roi.shape[1]-1, bottom_y), (0, 255, 0), 2)
        cv2.putText(test_img, f"BG: {bg_color}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        self._imwrite_unicode(test_output, test_img)
        
        print(f"🎯 测试完成！")
        print(f"  结果已保存: {test_output}")
        
        return bg_color, text_region

def main():
    """
    使用示例和测试
    """
    print("🚀 TextProcessor 新版本测试")
    print("=" * 60)
    
    # 测试参数
    img_path = r"text_test\1-1.jpg"
    text_region_box = [[66,468],[960,542]]  
    target_text = "中关村东升科技园西北门美团外卖柜"  # 目标文本
    replace_text = "中关村西升科技园东南门美团外卖柜"  # 替换文本
    text_region_box_name = [[66,548],[180,600]]  # 文本区域
    target_text_name = "刘哈哈"
    replace_text_name = "刘帅帅"
    output_path = "Final_Result.jpg"
    output_path_final = "Final_Result_name.jpg"
    
    # 创建处理器实例
    processor = TextProcessor(debug_mode=True)
    
    print("📋 测试配置:")
    print(f"  图像路径: {img_path}")
    print(f"  文本区域: {text_region_box}")
    print(f"  目标文本: {target_text}")
    print(f"  替换文本: {replace_text}")
    
    # 方式1: 测试文本检测
    print("\n" + "="*40)
    print("🧪 方式1: 测试文本检测")
    print("="*40)
    
    try:
        bg_color, text_region = processor.test_character_segmentation(img_path, text_region_box, target_text)
        print(f"✅ 检测测试成功")
    except Exception as e:
        print(f"❌ 检测测试失败: {e}")
    
    # 方式2: 完整处理流程
    print("\n" + "="*40)
    print("🔧 方式2: 完整处理流程")
    print("="*40)
    
    result = processor.process_text(
        img_path=img_path,
        text_region_box=text_region_box,
        target_text=target_text,
        replace_text=replace_text,
        output_path=output_path
    )
    result2 = processor.process_text(
        img_path=output_path,
        text_region_box=text_region_box_name,
        target_text=target_text_name,
        replace_text=replace_text_name,
        output_path=output_path_final
    )
    
    if result and result2:
        print(f"✅ 完整处理成功！")
        print(f"✅ 完整处理成功！")
    else:
        print(f"❌ 完整处理失败")
    
    print("\n" + "="*60)
    print("📝 新版本特性:")
    print("  ✅ 自动检测背景颜色")
    print("  ✅ 水平方向文本定位")
    print("  ✅ 整体文本替换（不分割单个字符）")
    print("  ✅ 保持背景颜色一致")
    print("  ✅ 文本水平对齐")
    print("="*60)

if __name__ == "__main__":
    main()