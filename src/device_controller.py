#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备控制模块
负责与Android设备的连接和操作
"""

import uiautomator2 as u2
import time
from .config import config

class DeviceController:
    """设备控制器"""
    
    def __init__(self):
        self.device = None
        self._connect()
    
    def _connect(self):
        """连接设备"""
        try:
            self.device = u2.connect(config.device_id)
            print(f"✅ 设备连接成功: {config.device_id}")
        except Exception as e:
            print(f"❌ 设备连接失败: {e}")
            print("请检查设备连接和adb调试是否开启")
            raise
    
    def test_connection(self) -> bool:
        """测试设备连接和功能"""
        try:
            print("🔍 正在测试设备连接...")
            
            # 测试设备信息
            device_info = self.device.device_info
            width = device_info.get('display', {}).get('width', 'unknown')
            height = device_info.get('display', {}).get('height', 'unknown')
            print(f"📱 设备信息: {width}x{height}")
            
            # 测试截图功能
            print("📸 测试截图功能...")
            self.device.screenshot("test_connection.jpg")
            print("✅ 截图功能正常")
            
            return True
            
        except Exception as e:
            print(f"❌ 设备连接测试失败: {e}")
            return False
    
    def screenshot(self, save_path: str) -> str:
        """截取屏幕截图"""
        self.device.screenshot(save_path)
        return save_path
    
    def get_xml_hierarchy(self, save_path: str) -> str:
        """获取界面XML层次结构"""
        xml_content = self.device.dump_hierarchy()
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        return save_path
    
    def click(self, x: int, y: int) -> bool:
        """点击指定坐标"""
        try:
            # 验证坐标是否在屏幕范围内
            device_info = self.device.device_info
            width = device_info.get('display', {}).get('width', 1080)
            height = device_info.get('display', {}).get('height', 2400)
            
            if 0 <= x <= width and 0 <= y <= height:
                print(f"🎯 点击位置: ({x}, {y})")
                self.device.click(x, y)
                time.sleep(2)  # 等待界面响应
                return True
            else:
                print(f"❌ 坐标超出屏幕范围: ({x}, {y}) vs ({width}x{height})")
                return False
                
        except Exception as e:
            print(f"❌ 点击操作失败: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """输入文本"""
        try:
            print(f"⌨️  输入文本: {text}")
            self.device.send_keys(text)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ 文本输入失败: {e}")
            return False
    
    def start_app(self, package_name: str) -> bool:
        """启动应用"""
        try:
            print(f"📱 启动应用: {package_name}")
            self.device.app_start(package_name)
            time.sleep(3)  # 等待应用启动
            return True
        except Exception as e:
            print(f"❌ 应用启动失败: {e}")
            return False
    
    def get_current_app(self) -> dict:
        """获取当前应用信息"""
        try:
            return self.device.app_current()
        except:
            return {"package": "unknown", "activity": "unknown"} 