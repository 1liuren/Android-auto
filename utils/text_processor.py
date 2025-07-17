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
    1. 字符分割和居中优化
    2. 智能字符交换
    3. 图像处理和背景分析
    4. 生成最终结果
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        初始化处理器
        
        Args:
            debug_mode: 是否启用调试模式（保存中间处理步骤）
        """
        self.debug_mode = debug_mode
        self.min_area = 100  # 最小轮廓面积阈值
        self.max_aspect_ratio = 5  # 最大长宽比
        self.merge_distance = 10  # 轮廓合并距离阈值
        
    def process_text(self, 
                            img_path: str,
                            text_region_box: List[List[int]],
                            target_text: str,
                            replace_text: str,
                            output_path: str = "Final_Result.jpg") -> bool:
        """
        处理电话地址姓名等文本的主函数
        
        Args:
            img_path: 图像路径
            phone_region_box: 电话号码区域边界框 [[x1,y1], [x2,y2]]
            target_phone_number: 目标电话号码字符串
            output_path: 输出图像路径
            
        Returns:
            bool: 是否处理成功
        """
        print("=" * 60)
        print("🚀 开始文本处理...")
        print(f"📁 图像路径: {img_path}")
        print(f"📱 目标文本: {target_text}")
        print(f"📍 区域范围: {text_region_box}")
        
        # 1. 加载原始图像（解决中文路径问题）
        img = self._imread_unicode(img_path)
        if img is None:
            print("❌ 无法读取图片，请检查路径！")
            return False
        
        print(f"✅ 成功加载图像，尺寸: {img.shape}")
        
        # 2. 提取电话号码区域
        x1, y1 = text_region_box[0]
        x2, y2 = text_region_box[1]
        
        # 验证区域边界
        if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0 or x2 > img.shape[1] or y2 > img.shape[0]:
            print(f"❌ 无效的区域边界: ({x1},{y1}) -> ({x2},{y2})")
            return False
            
        phone_roi = img[y1:y2, x1:x2].copy()
        roi_width, roi_height = x2 - x1, y2 - y1
        
        print(f"📋 提取ROI区域: {roi_width}x{roi_height}")
        
        if self.debug_mode:
            cv2.imwrite("debug_phone_roi.jpg", phone_roi)
            print("💾 已保存ROI调试图像")
            
        # 3. 改进的字符分割
        print("\n📊 开始字符分割分析...")
        segmented_img, bboxes = self.center_symmetric_segmentation(phone_roi, save_intermediate=self.debug_mode)
        
        print(f"\n📈 分割结果统计:")
        print(f"  检测到字符数: {len(bboxes)}")
        if bboxes:
            widths = [bbox[2] for bbox in bboxes]
            heights = [bbox[3] for bbox in bboxes]
            print(f"  平均宽度: {np.mean(widths):.1f}px (范围: {min(widths)}-{max(widths)})")
            print(f"  平均高度: {np.mean(heights):.1f}px (范围: {min(heights)}-{max(heights)})")
            
            # 显示每个字符框的详细信息
            for i, (x, y, w, h) in enumerate(bboxes):
                print(f"    字符{i+1}: ({x},{y},{w},{h}) 面积={w*h}")
        
        if self.debug_mode:
            cv2.imwrite("debug_segmented.jpg", segmented_img)
            print("💾 已保存分割调试图像")
        
        # 4. 智能字符交换
        print(f"\n🔄 准备字符替换...")
        if len(bboxes) >= 2:
            print(f"✅ 字符数量充足 ({len(bboxes)} >= 2)，开始替换")
            swapped_img = self.smart_character_replace(segmented_img, bboxes, replace_text)
        else:
            print(f"❌ 字符数量不足 ({len(bboxes)} < 2)，无法进行字符替换")
            # 如果字符数量不足，仍然继续处理，使用原图
            swapped_img = phone_roi.copy()
            
        if self.debug_mode:
            cv2.imwrite("debug_swapped.jpg", swapped_img)
            print("💾 已保存交换调试图像")
            
        # 5. 替换回原图
        print(f"\n🔧 合成最终结果...")
        result_img = self._replace_back_to_original(img, swapped_img, text_region_box)
        
        # 6. 保存结果（解决中文路径问题）
        print(f"\n💾 保存结果到: {output_path}")
        success = self._imwrite_unicode(output_path, result_img)
        if success:
            print(f"✅ 处理完成！结果已保存至: {output_path}")
        else:
            print(f"❌ 保存失败: {output_path}")
        
        print("=" * 60)
        return success
    
    def center_symmetric_segmentation(self, img: np.ndarray, save_intermediate: bool = False) -> Tuple[np.ndarray, List[Tuple]]:
        """
        改进的字符分割方法，解决字符粘连、高度不统一、嵌套框等问题
        
        Args:
            img: 输入图像
            save_intermediate: 是否保存中间结果
            
        Returns:
            tuple: (处理后的图像, 边界框列表)
        """
        print("🔍 开始改进的字符分割...")
        
        # 使用改进的字符分割算法
        segmented_img, bboxes = self._improved_character_segmentation(img.copy(), save_intermediate)
        
        cleaned_bboxes = bboxes
        
        # 绘制最终边界框
        result_img = img.copy()
        color_list = [
            (255, 0, 0),    # 红
            (0, 255, 0),    # 绿
            (0, 0, 255),    # 蓝
            (255, 255, 0),  # 青
            (255, 0, 255),  # 紫
            (0, 255, 255),  # 黄
            (128, 0, 128),  # 深紫
            (0, 128, 255),  # 橙
            (128, 128, 0),  # 橄榄
            (0, 128, 128),  # 青绿
        ]
        
        for i, (x, y, bbox_w, bbox_h) in enumerate(cleaned_bboxes):
            color = color_list[i % len(color_list)]
            cv2.rectangle(result_img, (x, y), (x + bbox_w, y + bbox_h), color, 2)
            # 添加序号标注
            cv2.putText(result_img, str(i+1), (x+2, y+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        print(f"✅ 分割完成，检测到 {len(cleaned_bboxes)} 个字符")
        
        if save_intermediate:
            cv2.imwrite("debug_final_segmentation.jpg", result_img)
        
        return result_img, cleaned_bboxes
    
    def _improved_character_segmentation(self, img: np.ndarray, save_intermediate: bool = False) -> Tuple[np.ndarray, List[Tuple]]:
        """
        改进的字符分割算法，解决字符粘连和分离问题
        """
        print("📊 执行改进的字符分割算法...")
        
        # 1. 预处理
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if save_intermediate:
            cv2.imwrite("debug_1_gray.jpg", gray)
        
        # 2. 自适应二值化，保持字符形状
        # 使用多种二值化方法并结合
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        thresh = cv2.bitwise_or(thresh_otsu, thresh_otsu)
        
        if save_intermediate:
            cv2.imwrite("debug_2_thresh.jpg", thresh)
        
        # 3. 形态学腐蚀与膨胀操作，增强字符分离
        kernel_erode = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))  # 增加腐蚀程度
        eroded = cv2.erode(thresh, kernel_erode, iterations=1)
        
        if save_intermediate:
            cv2.imwrite("debug_3_eroded.jpg", eroded)
        
        # 4. 直方图二值化与投影分析分割文字区域
        # 横向投影（行方向，适合分割横排文字）
        horizontal_hist = np.sum(eroded, axis=1)
        horizontal_thresh = np.max(horizontal_hist) * 0.01  # 阈值可调
        horizontal_regions = []
        in_region = False
        start_row = 0
        # 假设只有一行文字，筛选面积最大的区域作为唯一行区域
        temp_regions = []
        for i, val in enumerate(horizontal_hist):
            if val > horizontal_thresh and not in_region:
                in_region = True
                start_row = i
            elif val <= horizontal_thresh and in_region:
                in_region = False
                end_row = i
                if end_row - start_row > 2:  # 过滤极小区域
                    temp_regions.append((start_row, end_row))
        if in_region:
            end_row = len(horizontal_hist) - 1
            if end_row - start_row > 2:
                temp_regions.append((start_row, end_row))
        # 只保留面积最大的区域
        if temp_regions:
            horizontal_regions = [max(temp_regions, key=lambda r: r[1] - r[0])]
        else:
            horizontal_regions = []

        # 基于每个行区域，分别做竖向投影分割
        vertical_regions = []
        for (start_row, end_row) in horizontal_regions:
            # 只对当前行区域做竖向投影
            line_eroded = eroded[start_row:end_row, :]
            vertical_hist = np.sum(line_eroded, axis=0)
            vertical_thresh = np.max(vertical_hist) * 0.01  # 阈值可调
            in_region = False
            start_col = 0
            for i, val in enumerate(vertical_hist):
                if val > vertical_thresh and not in_region:
                    in_region = True
                    start_col = i
                elif val <= vertical_thresh and in_region:
                    in_region = False
                    end_col = i
                    if end_col - start_col > 2:
                        # 记录为 (start_col, end_col, start_row, end_row)
                        vertical_regions.append((start_col, end_col, start_row, end_row))
        if in_region:
            end_col = len(vertical_hist) - 1
            if end_col - start_col > 2:
                vertical_regions.append((start_col, end_col, start_row, end_row))

        print(f"🔍 横向检测到 {len(horizontal_regions)} 个文字行区域")
        print(f"🔍 竖向检测到 {len(vertical_regions)} 个文字列区域")

        # 可视化横向和竖向分割框
        if save_intermediate:
            vis_img = img.copy()
            for (start_row, end_row) in horizontal_regions:
                cv2.rectangle(vis_img, (0, start_row), (img.shape[1]-1, end_row), (255, 0, 0), 1)
            for (start_col, end_col, start_row, end_row) in vertical_regions:
                cv2.rectangle(vis_img, (start_col, 0), (end_col, img.shape[0]-1), (0, 255, 0), 1)
            # 同时输出两张图像到一张大图中
            # 竖向直方图可视化（只对最大行区域）
            if horizontal_regions:
                start_row, end_row = horizontal_regions[0]
                line_eroded = eroded[start_row:end_row, :]
                vertical_hist = np.sum(line_eroded, axis=0)
                hist_img_v = np.ones((200, len(vertical_hist), 3), dtype=np.uint8) * 255
                max_val_v = np.max(vertical_hist)
                if max_val_v > 0:
                    norm_hist_v = (vertical_hist / max_val_v * 180).astype(np.int32)
                    for x, h in enumerate(norm_hist_v):
                        cv2.line(hist_img_v, (x, 199), (x, 199 - h), (0, 128, 0), 1)
                # 拼接两张图像（竖直方向）
                h1, w1 = vis_img.shape[:2]
                h2, w2 = hist_img_v.shape[:2]
                # 调整宽度一致
                if w1 != w2:
                    # 以较大宽度为准，填充较小的
                    max_w = max(w1, w2)
                    if w1 < max_w:
                        pad = np.ones((h1, max_w - w1, 3), dtype=np.uint8) * 255
                        vis_img_pad = np.concatenate([vis_img, pad], axis=1)
                    else:
                        vis_img_pad = vis_img
                    if w2 < max_w:
                        pad = np.ones((h2, max_w - w2, 3), dtype=np.uint8) * 255
                        hist_img_v_pad = np.concatenate([hist_img_v, pad], axis=1)
                    else:
                        hist_img_v_pad = hist_img_v
                else:
                    vis_img_pad = vis_img
                    hist_img_v_pad = hist_img_v
                combined_img = np.concatenate([vis_img_pad, hist_img_v_pad], axis=0)
                cv2.imwrite("debug_4_histogram_regions_and_vertical_hist.jpg", combined_img)
            else:
                cv2.imwrite("debug_4_histogram_regions.jpg", vis_img)

        # 生成横向和竖向的所有交叉小块作为候选文字框
        candidate_bboxes = []
        for (start_row, end_row) in horizontal_regions:
            for (start_col, end_col, start_row, end_row) in vertical_regions:
                w = end_col - start_col
                h = end_row - start_row
                if w > 10 and h > 10:  # 过滤极小块
                    candidate_bboxes.append((start_col, start_row, w, h))

        print(f"✅ 横竖交叉得到 {len(candidate_bboxes)} 个候选文字框")
        
        
        # 7. 生成边界框
        bboxes = []
        debug_img = img.copy()
        
        for i, contour in enumerate(candidate_bboxes):
            x, y, w, h = contour
            bboxes.append((x, y, w, h))
            cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 1)
            cv2.putText(debug_img, str(i), (x, y-2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        if save_intermediate:
            cv2.imwrite("debug_4_separated_contours.jpg", debug_img)
        
        return debug_img, bboxes
    
    def _imread_unicode(self, img_path: str):
        """
        解决OpenCV在Windows下无法读取中文路径的问题
        
        Args:
            img_path: 图片路径
            
        Returns:
            np.ndarray: 图像数据，失败返回None
        """
        try:
            # 使用numpy.fromfile读取文件
            img_array = np.fromfile(img_path, dtype=np.uint8)
            # 使用cv2.imdecode解码图像
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
            # 使用cv2.imencode编码图像
            ext = os.path.splitext(img_path)[1]
            success, img_encoded = cv2.imencode(ext, img)
            if success:
                # 使用numpy.tofile写入文件
                img_encoded.tofile(img_path)
                return True
            return False
        except Exception as e:
            print(f"写入图片失败: {e}")
            return False
    
    def analyze_background(self, img: np.ndarray, bbox: Tuple[int, int, int, int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        分析边界框周围的背景特征
        
        Args:
            img: 输入图像
            bbox: 边界框 (x, y, w, h)
            
        Returns:
            tuple: (平均背景色, 背景区域)
        """
        x, y, w, h = bbox
        margin = 20
        
        bg_x1 = max(0, x - margin)
        bg_y1 = max(0, y - margin)
        bg_x2 = min(img.shape[1], x + w + margin)
        bg_y2 = min(img.shape[0], y + h + margin)
        
        background_region = img[bg_y1:bg_y2, bg_x1:bg_x2]
        
        # 创建掩码，排除中心区域
        mask = np.ones((bg_y2-bg_y1, bg_x2-bg_x1), dtype=bool)
        center_x = x - bg_x1
        center_y = y - bg_y1
        mask[center_y:center_y+h, center_x:center_x+w] = False
        
        # 计算背景平均颜色
        bg_pixels = background_region[mask]
        avg_color = np.mean(bg_pixels, axis=0)
        
        return avg_color, background_region

    def test_character_segmentation(self, img_path: str, text_region_box: List[List[int]]):
        """
        测试字符分割功能，不进行字符交换
        
        Args:
            img_path: 图像路径
            region_box: 测试区域
        """
        print("\n🧪 测试字符分割功能...")
        
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
        
        # 执行分割测试
        segmented_img, bboxes = self.center_symmetric_segmentation(roi, save_intermediate=True)
        
        # 保存测试结果
        test_output = "test_segmentation_result.jpg"
        self._imwrite_unicode(test_output, segmented_img)
        
        print(f"🎯 测试完成！")
        print(f"  检测到 {len(bboxes)} 个字符区域")
        print(f"  结果已保存: {test_output}")
        
        return bboxes
    
    def smart_character_replace(self, img, bboxes, chars, font_path="utils/SIMHEI.TTF"):
        """
        智能字符交换方法：
        1. 提取截获图像的背景颜色
        2. 创建画布
        3. 根据提供的字符和替换的位置（检测框索引对应的字符），使用指定的字体puttext到画布中

        Args:
            img: 原始图像（numpy数组）
            bboxes: 字符检测框列表，每个为[x1, y1, x2, y2]
            chars: 替换字符列表，长度与bboxes一致
            font_path: 字体文件路径
            font_size: 字体大小

        Returns:
            替换后的图像
        """
    

        # 1. 提取背景颜色（取所有bbox外的区域平均色）
        # mask = np.ones(img.shape[:2], dtype=bool)
        avg_color = [255, 255, 255]

        # 2. 创建画布（与原图同尺寸，填充背景色）
        canvas = np.full_like(img, avg_color, dtype=np.uint8)

        # 3. 逐个字符框进行替换
        # 将OpenCV图像（BGR）转为PIL图像（RGB）
        canvas_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        # draw = ImageDraw.Draw(canvas_pil)

        # 只取与bboxes数量相同的字符
        chars = list(chars)
        if len(chars) > len(bboxes):
            chars = chars[:len(bboxes)]
        elif len(chars) < len(bboxes):
            # 不足时补空字符
            chars += [' '] * (len(bboxes) - len(chars))

        for (bbox, char) in zip(bboxes, chars):
            x1, y1, w, h = bbox
            x2, y2 = x1 + w, y1 + h
            # 检查宽高是否为正，防止负数导致 ValueError
            if w <= 0 or h <= 0:
                print(f"⚠️ 跳过无效字符框: {bbox}（宽度或高度为负/零）")
                continue
            # 字体大小为字符框高度的80%
            font_size = max(12, int(h))
            try:
                # 尝试加载加粗字体（如果字体文件支持加粗）
                font = ImageFont.truetype(font_path, font_size)
                # 通过多次描边实现加粗效果（PIL本身不直接支持加粗）
                bold = True
            except Exception as e:
                print(f"❌ 加载字体失败: {e}，使用默认字体")
                font = ImageFont.load_default()
                bold = False
            # 计算字符尺寸（PIL方式，支持中文）
            # 字体大小由 font_size 参数控制，font_size = max(12, int(h * 0.8))
            # 如果需要调整字体大小，可以修改 font_size 的计算方式
            char_canvas = np.full((h, w, 3), avg_color, dtype=np.uint8)
            char_pil = Image.fromarray(cv2.cvtColor(char_canvas, cv2.COLOR_BGR2RGB))
            char_draw = ImageDraw.Draw(char_pil)
            try:
                char_bbox = char_draw.textbbox((0, 0), char, font=font)
                char_w = char_bbox[2] - char_bbox[0]
                char_h = char_bbox[3] - char_bbox[1]
            except AttributeError:
                char_w, char_h = char_draw.textsize(char, font=font)
            # 居中放置字符
            text_x = (w - char_w) // 2
            text_y = (h - char_h) // 2
            char_draw.text((text_x, text_y), char, font=font, fill=(0, 0, 0))
            # 将字符画布粘贴到主画布
            canvas_pil.paste(char_pil, (x1, y1))
        # 将PIL图像（RGB）转回OpenCV图像（BGR）
        result_img = cv2.cvtColor(np.array(canvas_pil), cv2.COLOR_RGB2BGR)
        return result_img

    def _replace_back_to_original(self, original_img: np.ndarray, processed_roi: np.ndarray, region_box: List[List[int]]) -> np.ndarray:
            """将处理后的ROI替换回原图"""
            result_img = original_img.copy()
            x1, y1 = region_box[0]
            x2, y2 = region_box[1]
            w, h = x2 - x1, y2 - y1
            
            # 调整尺寸并替换
            resized_roi = cv2.resize(processed_roi, (w, h))
            result_img[y1:y2, x1:x2] = resized_roi
            
            return result_img

def main():
    """
    使用示例和测试
    """
    print("🚀 PhoneNumberProcessor 改进版测试")
    print("=" * 60)
    
   
    
    # 测试参数
    img_path = "../../OCR-test/1-17.jpg"
    text_region_box = [[66,325],[479,398]]  # 文本区域
    target_text = "上海虹桥-南京南"  # 目标文本
    replace_text = "北京南站-天津站"  # 替换文本
    # text_region_box = [[452, 1292], [936, 1413]]  # 电话号码区域
    # target_text = "18810032768"  # 目标电话号码
    output_path = "Final_Result.jpg"
    
    # 创建处理器实例（启用调试模式，并传入文本区域和目标文本）
    processor = TextProcessor(
        debug_mode=True,
    )
    print("📋 测试配置:")
    print(f"  图像路径: {img_path}")
    print(f"  文本区域: {text_region_box}")
    print(f"  目标文本: {target_text}")
    
    # # 方式1: 只测试字符分割效果
    # print("\n" + "="*40)
    # print("🧪 方式1: 测试字符分割")
    # print("="*40)
    
    # try:
    #     bboxes = processor.test_character_segmentation(img_path, text_region_box)
    #     if bboxes:
    #         print(f"✅ 分割测试成功，检测到 {len(bboxes)} 个字符")
    #     else:
    #         print("⚠️ 未检测到字符区域")
    # except Exception as e:
    #     print(f"❌ 分割测试失败: {e}")
    
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
    if result:
        print(f"✅ 完整处理成功！")
    else:
        print(f"❌ 完整处理失败")
    
    # # 方式3: 分析多个区域（如果有多个测试区域）
    # print("\n" + "="*40)
    # print("📊 方式3: 多区域分析示例")
    # print("="*40)
    
    # # 可以添加更多测试区域
    # test_regions = [
    #     [[66,325],[479,398]],  # 第一个区域
    #     # [[100,100],[300,150]],  # 可以添加更多区域进行测试
    # ]
    
    # try:
    #     processor.analyze_image_text_regions(img_path, test_regions)
    # except Exception as e:
    #     print(f"❌ 多区域分析失败: {e}")
    
    # print("\n" + "="*60)
    # print("📝 改进总结:")
    # print("  ✅ 解决了字符粘连问题")
    # print("  ✅ 统一了字符框高度")
    # print("  ✅ 移除了嵌套框")
    # print("  ✅ 增加了详细的调试信息")
    # print("  ✅ 改进了轮廓过滤和分离算法")
    # print("="*60)


if __name__ == "__main__":
    main() 