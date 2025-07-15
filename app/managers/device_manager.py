#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备管理器
"""

import os
import sys
import threading

# 添加src模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.device_controller import DeviceController
from src.logger_config import get_logger


class DeviceManager:
    """设备管理器"""
    
    def __init__(self, gui_app):
        self.gui_app = gui_app
        self.device_controller = None
        self.device_info = None
        self.logger = get_logger("device_manager")
        
    def refresh_device_info(self, callback=None):
        """刷新设备信息"""
        try:
            self.logger.info("🔄 正在刷新设备信息...")
            
            # 在新线程中获取设备信息
            threading.Thread(
                target=self._get_device_info,
                args=(callback,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.logger.error(f"❌ 刷新设备信息失败: {e}")
    
    def _get_device_info(self, callback=None):
        """获取设备信息"""
        try:
            self.logger.info("🔄 正在检测设备连接状态...")
            
            # 创建设备控制器
            self.device_controller = DeviceController()
            
            # 检测连接状态
            connection_result = self.device_controller.test_connection()
            self.logger.info(f"🔗 连接测试结果: {connection_result}")
            
            if connection_result:
                # 获取设备信息
                self.device_info = self.device_controller.get_device_info()
                self.logger.info(f"📱 设备信息获取结果: {bool(self.device_info)}")
                
                if self.device_info:
                    info_text = self._format_device_info(self.device_info)
                    color = "green"
                    self.logger.success("✅ 设备连接正常，信息获取成功")
                else:
                    info_text = "📱 设备: 已连接但信息获取失败"
                    color = "orange"
                    self.logger.warning("⚠️ 设备已连接但无法获取详细信息")
            else:
                info_text = "📱 设备: 未连接"
                color = "red"
                self.device_info = None
                self.logger.error("❌ 设备未连接或ADB不可用")
            
            # 更新UI（在主线程中执行）
            self.gui_app.root.after(0, lambda: self._update_device_info_ui(info_text, color))
            
            # 调用回调函数
            if callback:
                callback(self.device_info is not None, self.device_info)
            
        except Exception as e:
            self.gui_app.root.after(0, lambda: self._update_device_info_ui("📱 设备: 检测失败", "red"))
            self.logger.error(f"❌ 设备信息获取失败: {e}")
            
            if callback:
                callback(False, None)
    
    def _format_device_info(self, device_info):
        """格式化设备信息"""
        if not device_info:
            return "📱 设备: 信息获取失败"
        
        brand = device_info.get('brand', 'Unknown')
        model = device_info.get('model', 'Unknown')
        version = device_info.get('version', 'Unknown')
        
        return f"📱 {brand} {model} (Android {version})"
    
    def _update_device_info_ui(self, text, color):
        """更新设备信息显示"""
        # 更新状态栏中的设备信息，传递颜色
        if hasattr(self.gui_app, 'status_bar') and self.gui_app.status_bar:
            self.gui_app.status_bar.update_device_info(text, color)
        
        # 如果控制面板中也有设备信息标签，也更新它
        if hasattr(self.gui_app, 'device_info_label') and self.gui_app.device_info_label:
            self.gui_app.device_info_label.config(text=text, foreground=color)
            
        # 强制更新UI显示
        if hasattr(self.gui_app, 'root') and self.gui_app.root:
            self.gui_app.root.update_idletasks()
    
    def check_device(self):
        """检查设备连接状态"""
        try:
            # 创建设备控制器（如果还没有的话）
            if not self.device_controller:
                self.device_controller = DeviceController()
            
            # 测试连接
            connection_result = self.device_controller.test_connection()
            
            if connection_result:
                return "已连接设备"
            else:
                return "未连接设备"
                
        except Exception as e:
            return f"检测失败: {str(e)}"
    
    def get_device_status(self):
        """获取设备状态"""
        if not self.device_controller:
            return "unknown"
        
        try:
            if self.device_controller.test_connection():
                return "connected"
            else:
                return "disconnected"
        except:
            return "error"
    
    def get_device_info_dict(self):
        """获取设备信息字典"""
        return self.device_info if self.device_info else {}
    
    def is_device_connected(self):
        """检查设备是否连接"""
        try:
            if not self.device_controller:
                self.device_controller = DeviceController()
            return self.device_controller.test_connection()
        except:
            return False
    
    def get_device_id(self):
        """获取设备ID"""
        if self.device_info:
            return self.device_info.get('device_id', 'Unknown')
        return 'Unknown'
    
    def check_device_requirements(self):
        """检查设备是否满足运行要求"""
        if not self.is_device_connected():
            return False, "设备未连接"
        
        if not self.device_info:
            return False, "无法获取设备信息"
        
        # 检查Android版本
        try:
            version = self.device_info.get('version', '0')
            version_num = float(version.split('.')[0])
            if version_num < 7:  # 要求Android 7.0以上
                return False, f"Android版本过低: {version}，需要7.0以上"
        except:
            self.gui_app._log_output("⚠️ 无法解析Android版本")
        
        # 检查屏幕状态（这需要额外的ADB命令）
        try:
            if self.device_controller:
                # 这里可以添加更多的设备检查逻辑
                pass
        except:
            pass
        
        return True, "设备满足运行要求"
    
    def wake_device(self):
        """唤醒设备屏幕"""
        try:
            if not self.device_controller:
                self.device_controller = DeviceController()
            
            # 发送唤醒命令
            import subprocess
            result = subprocess.run(
                ['adb', 'shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.gui_app._log_output("📱 设备屏幕已唤醒")
                return True
            else:
                self.gui_app._log_output("❌ 无法唤醒设备屏幕")
                return False
                
        except Exception as e:
            self.gui_app._log_output(f"❌ 唤醒设备失败: {e}")
            return False
    
    def get_screen_info(self):
        """获取屏幕信息"""
        try:
            if not self.device_controller:
                self.device_controller = DeviceController()
            
            # 获取屏幕分辨率
            import subprocess
            result = subprocess.run(
                ['adb', 'shell', 'wm', 'size'],
                capture_output=True, text=True
            )
            
            screen_info = {}
            if result.returncode == 0:
                # 解析输出，例如: "Physical size: 1080x2340"
                output = result.stdout.strip()
                if 'Physical size:' in output:
                    size_str = output.split('Physical size:')[1].strip()
                    width, height = size_str.split('x')
                    screen_info['width'] = int(width)
                    screen_info['height'] = int(height)
            
            return screen_info
            
        except Exception as e:
            self.gui_app._log_output(f"❌ 获取屏幕信息失败: {e}")
            return {}
    
    def install_required_apps(self, app_packages):
        """检查并安装必需的应用（仅检查是否已安装）"""
        if not self.is_device_connected():
            return False, "设备未连接"
        
        try:
            installed_apps = {}
            missing_apps = []
            
            for app_name, package_name in app_packages.items():
                # 检查应用是否已安装
                import subprocess
                result = subprocess.run(
                    ['adb', 'shell', 'pm', 'list', 'packages', package_name],
                    capture_output=True, text=True
                )
                
                if package_name in result.stdout:
                    installed_apps[app_name] = True
                    self.gui_app._log_output(f"✅ {app_name} 已安装")
                else:
                    installed_apps[app_name] = False
                    missing_apps.append(app_name)
                    self.gui_app._log_output(f"❌ {app_name} 未安装")
            
            if missing_apps:
                return False, f"以下应用未安装: {', '.join(missing_apps)}"
            else:
                return True, "所有必需应用已安装"
                
        except Exception as e:
            self.gui_app._log_output(f"❌ 检查应用安装状态失败: {e}")
            return False, f"检查失败: {e}" 