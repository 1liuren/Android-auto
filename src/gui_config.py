#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI配置管理模块
用于保存和加载GUI界面的配置信息
"""

import os
import json
from typing import Dict, Any
from .logger_config import get_logger

logger = get_logger(__name__)

class GUIConfig:
    """GUI配置管理类"""
    
    def __init__(self, config_file: str = "gui_config.json"):
        self.config_file = config_file
        self.default_config = {
            "output_dir": "output",
            "batch_output_dir": "batch_output",
            "api_key": "",
            "model_name": "deepseek-r1",
            "max_execution_times": 50,
            "privacy_enabled": True,
            "multimodal_enabled": False,
            "device_id": "auto",
            "excel_file": "验收通过数据/标贝采集需求.xlsx",
            "selected_sheets": ["爱奇艺", "懂车帝", "美团外卖", "饿了么"],
            "target_column": "示例query",
            "window_geometry": "1200x800",
            "last_task": "在京东上查快递",
            "app_packages": {
                "美团外卖": "com.sankuai.meituan.takeoutnew", 
                "饿了么": "me.ele",
                "爱奇艺": "com.qiyi.video",
                "懂车帝": "com.ss.android.auto",
                "滴滴出行": "com.sdu.didi.psnger",
                "携程": "ctrip.android.view"
            }
        }
        self.config = self.default_config.copy()
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    
                # 合并配置（保持默认值）
                for key, value in saved_config.items():
                    if key in self.default_config:
                        self.config[key] = value
                
                logger.info(f"✅ 配置已从 {self.config_file} 加载")
            else:
                logger.info("📝 使用默认配置")
                
        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}，使用默认配置")
            self.config = self.default_config.copy()
        
        return self.config
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 配置已保存到 {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置保存失败: {e}")
            return False
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def update(self, new_config: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(new_config)
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
        logger.info("🔄 配置已重置为默认值")
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到指定文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 配置已导出到 {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置导出失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从指定文件导入配置"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ 配置文件不存在: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证并更新配置
            for key, value in imported_config.items():
                if key in self.default_config:
                    self.config[key] = value
            
            logger.info(f"✅ 配置已从 {file_path} 导入")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置导入失败: {e}")
            return False

# 创建全局配置实例
gui_config = GUIConfig() 