#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
隐私保护模块
负责检测和处理敏感信息，如手机号码假名化
"""

import os
import re
import cv2
import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional, Dict
from .config import config
from .logger_config import get_logger
from utils.phone_number_processor import PhoneNumberProcessor

logger = get_logger(__name__)

class PrivacyProtector:
    """隐私保护器"""
    
    def __init__(self):
        self.phone_processor = PhoneNumberProcessor(debug_mode=config.privacy_protection.get("debug_mode", False))
        self.protection_enabled = config.privacy_protection.get("enabled", True)
    
    def check_privacy_sensitivity(self, xml_content: str, screenshot_path: str) -> Dict:
        """
        备用方法已移除，现在完全依赖LLM检测结果
        
        Args:
            xml_content: XML界面内容
            screenshot_path: 截图路径
            
        Returns:
            Dict: 空的隐私检测结果
        """
        logger.info("🔒 隐私检测完全依赖LLM结果，备用方法已禁用")
        return {"phone_numbers": []}
    
    def protect_screenshot(self, screenshot_path: str, privacy_info: Dict) -> str:
        """
        对截图进行隐私保护处理
        
        Args:
            screenshot_path: 原始截图路径
            privacy_info: 隐私信息
            
        Returns:
            str: 处理后的截图路径
        """
        phone_numbers = privacy_info.get("phone_numbers", [])
        if not phone_numbers:
            return screenshot_path
        
        try:
            # 生成保护后的文件名
            base_name = os.path.splitext(screenshot_path)[0]
            protected_path = f"{base_name}_protected.jpg"
            
            # 对每个手机号进行假名化处理
            current_path = screenshot_path
            
            for i, phone_info in enumerate(privacy_info.get("phone_numbers", [])):
                temp_path = f"{base_name}_temp_{i}.jpg"
                
                success = self._anonymize_phone_number(
                    current_path,
                    phone_info,
                    temp_path
                )
                
                if success:
                    current_path = temp_path
                    logger.info(f"✅ 手机号 {phone_info['display_number']} 已假名化")
                else:
                    logger.warning(f"⚠️ 手机号 {phone_info['display_number']} 假名化失败")
            
            # 重命名最终文件
            if current_path != screenshot_path:
                os.rename(current_path, protected_path)
                
                # 清理临时文件
                self._cleanup_temp_files(base_name)
                
                logger.info(f"🔒 隐私保护完成: {protected_path}")
                return protected_path
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"❌ 隐私保护处理失败: {e}")
            return screenshot_path
    

    
    def _parse_bounds(self, bounds_str: str) -> Optional[List[List[int]]]:
        """解析bounds字符串"""
        try:
            # 格式: [left,top][right,bottom]
            pattern = r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]'
            match = re.match(pattern, bounds_str)
            
            if match:
                left, top, right, bottom = map(int, match.groups())
                return [[left, top], [right, bottom]]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 边界解析失败: {e}")
            return None
    
    def _anonymize_phone_number(self, img_path: str, phone_info: Dict, output_path: str) -> bool:
        """对单个手机号进行假名化"""
        try:
            phone_region_box = phone_info["bbox"]
            display_number = phone_info["display_number"]
            
            # 使用正则表达式清理手机号码
            target_phone = self._clean_phone_with_regex(display_number)
            
            # 确保手机号格式正确
            if len(target_phone) != 11 or not target_phone.startswith('1'):
                logger.warning(f"⚠️ 手机号格式异常: {target_phone} (原文: {display_number})")
                return False
            
            # 调用手机号处理器
            success = self.phone_processor.process_phone_number(
                img_path=img_path,
                phone_region_box=phone_region_box,
                target_phone_number=target_phone,
                output_path=output_path
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 手机号假名化失败: {e}")
            return False
    
    def _clean_phone_with_regex(self, phone_text: str) -> str:
        """使用正则表达式清理手机号码"""
        if not phone_text:
            return ""
        
        # 去除所有空格和常见分隔符
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone_text)
        
        # 如果是+86开头，去掉国家代码
        if cleaned.startswith('+86'):
            cleaned = cleaned[3:]
        elif cleaned.startswith('86') and len(cleaned) == 13:
            cleaned = cleaned[2:]
        
        # 确保是11位数字
        if re.match(r'^1[3-9]\d{9}$', cleaned):
            return cleaned
        
        # 如果不符合标准格式，尝试提取11位数字
        phone_match = re.search(r'1[3-9]\d{9}', phone_text)
        if phone_match:
            return phone_match.group()
        
        logger.warning(f"⚠️ 无法清理手机号码: {phone_text}")
        return cleaned
    
    def _cleanup_temp_files(self, base_name: str):
        """清理临时文件"""
        try:
            import glob
            temp_pattern = f"{base_name}_temp_*.jpg"
            temp_files = glob.glob(temp_pattern)
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"🗑️ 清理临时文件: {temp_file}")
                    
        except Exception as e:
            logger.warning(f"⚠️ 临时文件清理失败: {e}")
 