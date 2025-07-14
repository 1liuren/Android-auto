#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电话号码处理器类
功能：字符分割、字符交换、图像处理
"""

import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
import re

class PhoneNumberProcessor:
    """
    电话号码处理器类
    
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
        
    def process_phone_number(self, 
                            img_path: str,
                            phone_region_box: List[List[int]],
                            target_phone_number: str,
                            output_path: str = "Final_Result.jpg") -> bool:
        """
        处理电话号码的主函数
        
        Args:
            original_image: 原始图像
            phone_region_box: 电话号码区域边界框 [[x1,y1], [x2,y2]]
            target_phone_number: 目标电话号码字符串
            output_path: 输出图像路径
            
        Returns:
            bool: 是否处理成功
        """
        # 1. 加载原始图像（解决中文路径问题）
        img = self._imread_unicode(img_path)
        if img is None:
            print("无法读取图片，请检查路径！")
            return False
        # 2. 提取电话号码区域
        x1, y1 = phone_region_box[0]
        x2, y2 = phone_region_box[1]
        phone_roi = img[y1:y2, x1:x2].copy()
        
        if self.debug_mode:
            cv2.imwrite("debug_phone_roi.jpg", phone_roi)
            
        # 3. 字符分割（使用居中优化）
        segmented_img, bboxes = self.center_symmetric_segmentation(phone_roi)
        
        if self.debug_mode:
            cv2.imwrite("debug_segmented.jpg", segmented_img)
            
        print(f"检测到 {len(bboxes)} 个字符")
        
        # 4. 智能字符交换
        if len(bboxes) >= 2:
            swapped_img = self.smart_character_swap(phone_roi, bboxes, target_phone_number)
        else:
            print("字符数量不足, 无法进行字符交换")
            return False
            
        if self.debug_mode:
            cv2.imwrite("debug_swapped.jpg", swapped_img)
            
        # 5. 替换回原图
        result_img = self._replace_back_to_original(img, swapped_img, phone_region_box)
        
        # 6. 保存结果（解决中文路径问题）
        success = self._imwrite_unicode(output_path, result_img)
        if success:
            print(f"处理完成，结果已保存至: {output_path}")
        else:
            print(f"保存失败: {output_path}")
        
        return success
    
    def center_symmetric_segmentation(self, img: np.ndarray, save_intermediate: bool = False) -> Tuple[np.ndarray, List[Tuple]]:
        """
        使用中心对称翻转改善字符居中的分割方法
        
        Args:
            img: 输入图像
            save_intermediate: 是否保存中间结果
            
        Returns:
            tuple: (处理后的图像, 边界框列表)
        """
        h, w = img.shape[:2]
        
        # 1. 正常分割
        _, normal_bboxes = self._character_segmentation_debug(img.copy(), save_intermediate=False)
        
        # 2. 中心对称翻转图像（180度旋转）
        flipped_img = cv2.rotate(img, cv2.ROTATE_180)
        
        # 3. 对翻转图像进行分割
        _, flipped_bboxes = self._character_segmentation_debug(flipped_img, save_intermediate=False)
        
        # 4. 将翻转坐标还原到原始坐标系
        restored_bboxes = []
        for x, y, bbox_w, bbox_h in flipped_bboxes:
            restored_x = w - x - bbox_w
            restored_y = h - y - bbox_h
            restored_bboxes.append((restored_x, restored_y, bbox_w, bbox_h))
        
        # 5. 对应bbox取并集（按x坐标排序后一一对应）
        normal_sorted = sorted(normal_bboxes, key=lambda b: b[0])
        restored_sorted = sorted(restored_bboxes, key=lambda b: b[0])
        
        final_bboxes = []
        max_len = min(len(normal_sorted), len(restored_sorted))
        for i in range(max_len):
            norm_bbox = normal_sorted[i]
            rest_bbox = restored_sorted[i]
            # 取并集
            min_x = min(norm_bbox[0], rest_bbox[0])
            min_y = min(norm_bbox[1], rest_bbox[1])
            max_x = max(norm_bbox[0] + norm_bbox[2], rest_bbox[0] + rest_bbox[2])
            max_y = max(norm_bbox[1] + norm_bbox[3], rest_bbox[1] + rest_bbox[3])
            
            union_bbox = (min_x, min_y, max_x - min_x, max_y - min_y)
            final_bboxes.append(union_bbox)
        
        # 如果有剩余的bbox，直接添加
        if len(normal_sorted) > max_len:
            final_bboxes.extend(normal_sorted[max_len:])
        elif len(restored_sorted) > max_len:
            final_bboxes.extend(restored_sorted[max_len:])
        
        # 6. 绘制最终边界框
        result_img = img.copy()
        for x, y, bbox_w, bbox_h in final_bboxes:
            cv2.rectangle(result_img, (x, y), (x + bbox_w, y + bbox_h), (255, 0, 0), 2)
        
        if save_intermediate:
            self._save_debug_images(img, normal_bboxes, restored_bboxes)
        
        return result_img, final_bboxes
    
    def smart_character_swap(self, img: np.ndarray, bboxes: List[Tuple], target_phone_number: str) -> np.ndarray:
        """
        智能字符交换
        
        Args:
            img: 输入图像
            bboxes: 字符边界框列表
            target_phone_number: 目标手机号字符串
            
        Returns:
            np.ndarray: 交换后的图像
        """
        if len(bboxes) < 2:
            return img
        
        # 清理手机号，去除空格等字符
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', target_phone_number)
        if len(clean_phone) < len(bboxes):
            # 如果清理后的手机号长度不够，使用原始字符串
            clean_phone = target_phone_number
            
        # 随机选择两个不同的字符进行交换
        max_tries = 10
        for _ in range(max_tries):
            idx1, idx2 = np.random.randint(3, min(len(bboxes), len(clean_phone)), 2)
            if idx1 != idx2 and idx1 < len(clean_phone) and idx2 < len(clean_phone):
                if clean_phone[idx1] != clean_phone[idx2]:
                    break
        else:
            # 如果找不到合适的字符对，默认交换前两个可用的字符
            idx1, idx2 = 0, 1
        
        print(f"交换第 {idx1} 和第 {idx2} 个字符")
        
        x1, y1, w1, h1 = bboxes[idx1]
        x2, y2, w2, h2 = bboxes[idx2]
        
        # 判断大小box
        area1, area2 = w1 * h1, w2 * h2
        if area1 >= area2:
            big_x, big_y, big_w, big_h = x1, y1, w1, h1
            small_x, small_y, small_w, small_h = x2, y2, w2, h2
        else:
            big_x, big_y, big_w, big_h = x2, y2, w2, h2
            small_x, small_y, small_w, small_h = x1, y1, w1, h1
        
        # 计算扩展后的小box区域
        y_offset_top = (big_h - small_h) // 2
        y_offset_bottom = (big_h - small_h) - y_offset_top
        x_offset_left = (big_w - small_w) // 2
        x_offset_right = (big_w - small_w) - x_offset_left
        
        small_y_top = max(0, small_y - y_offset_top)
        small_y_bottom = min(img.shape[0], small_y + y_offset_bottom + small_h)
        small_x_left = max(0, small_x - x_offset_left)
        small_x_right = min(img.shape[1], small_x + x_offset_right + small_w)
        
        # 提取两个区域
        roi1 = img[small_y_top:small_y_bottom, small_x_left:small_x_right].copy()
        roi2 = img[big_y:big_y+big_h, big_x:big_x+big_w].copy()
        
        # 交换
        result_img = img.copy()
        result_img[big_y:big_y+big_h, big_x:big_x+big_w] = roi1
        result_img[small_y_top:small_y_bottom, small_x_left:small_x_right] = roi2
        
        return result_img
    
    def _character_segmentation_debug(self, img: np.ndarray, save_intermediate: bool = False) -> Tuple[np.ndarray, List[Tuple]]:
        """
        字符分割调试版本
        """
        # 转灰度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if save_intermediate:
            cv2.imwrite("debug_1_gray.jpg", gray)
        
        # 二值化
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        if save_intermediate:
            cv2.imwrite("debug_2_thresh.jpg", thresh)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 3))
        eroded = cv2.erode(thresh, kernel, iterations=1)
        dilated = cv2.dilate(eroded, kernel, iterations=2)
        
        if save_intermediate:
            cv2.imwrite("debug_3_eroded.jpg", eroded)
            cv2.imwrite("debug_4_dilated.jpg", dilated)
        
        # 轮廓检测
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 过滤轮廓
        filtered_contours = self._filter_contours(contours)
        
        # 合并重叠轮廓
        merged_contours = self._merge_contours(filtered_contours)
        
        # 生成边界框
        bboxes = []
        for contour in merged_contours:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            bboxes.append((x, y, w, h))
        
        return img, bboxes
    
    def _filter_contours(self, contours: List) -> List:
        """过滤轮廓"""
        filtered = []
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = max(w, h) / (min(w, h) + 1e-5)
            
            if area > self.min_area and aspect_ratio <= self.max_aspect_ratio:
                filtered.append(contour)
        return filtered
    
    def _merge_contours(self, contours: List) -> List:
        """合并重叠或相邻的轮廓"""
        merged = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            merged_flag = False
            
            for i, merged_contour in enumerate(merged):
                mx, my, mw, mh = cv2.boundingRect(merged_contour)
                
                # 计算重叠区域
                overlap_x = max(0, min(x + w, mx + mw) - max(x, mx))
                overlap_y = max(0, min(y + h, my + mh) - max(y, my))
                overlap_area = overlap_x * overlap_y
                
                # 判断是否需要合并
                if overlap_area > 0 or (abs(x - (mx + mw)) < self.merge_distance and abs(y - my) < self.merge_distance):
                    # 创建合并后的轮廓
                    new_x = min(x, mx)
                    new_y = min(y, my)
                    new_w = max(x + w, mx + mw) - new_x
                    new_h = max(y + h, my + mh) - new_y
                    
                    merged_points = [[new_x, new_y], [new_x + new_w, new_y], 
                                   [new_x + new_w, new_y + new_h], [new_x, new_y + new_h]]
                    merged[i] = np.array(merged_points, dtype=np.int32)
                    merged_flag = True
                    break
            
            if not merged_flag:
                merged.append(contour)
        
        return merged
    
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
    
    def _save_debug_images(self, img: np.ndarray, normal_bboxes: List[Tuple], restored_bboxes: List[Tuple]):
        """保存调试图像"""
        # 正常分割结果
        normal_debug = img.copy()
        for x, y, w, h in normal_bboxes:
            cv2.rectangle(normal_debug, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.imwrite("debug_normal_bboxes.jpg", normal_debug)
        
        # 翻转还原结果
        restored_debug = img.copy()
        for x, y, w, h in restored_bboxes:
            cv2.rectangle(restored_debug, (x, y), (x + w, y + h), (0, 0, 255), 1)
        cv2.imwrite("debug_restored_bboxes.jpg", restored_debug)
    
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


def main():
    """
    使用示例
    """
    # 创建处理器实例
    processor = PhoneNumberProcessor()
    
    # 处理参数
    img_path = "OCR/1-17.jpg"
    phone_region_box = [[452, 1292], [936, 1413]]  # 电话号码区域
    target_phone_number = "18810032768"  # 目标电话号码
    output_path = "OCR/Final_Result.jpg"
    
    # 执行处理
    result = processor.process_phone_number(
        img_path=img_path,
        phone_region_box=phone_region_box,
        target_phone_number=target_phone_number,
        output_path=output_path
    )
    if result:
        print(f"✅ 处理成功！")
    else:
        print(f"❌ 处理失败")


if __name__ == "__main__":
    main() 