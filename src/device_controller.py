#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设备控制模块
负责与Android设备的连接和操作
"""

import uiautomator2 as u2
import adbutils
import time
from .config import config
from .logger_config import get_logger

logger = get_logger(__name__)

class DeviceController:
    """设备控制器"""
    
    def __init__(self):
        self.device = None
        self.screen_size = None
        self._connect()
    
    def _connect(self):
        """智能连接设备"""
        try:
            # 如果配置了设备ID，直接连接
            if hasattr(config, 'device_id') and config.device_id and config.device_id != "auto":
                try:
                    self.device = u2.connect(config.device_id)
                    logger.info(f"✅ 使用配置的设备ID连接成功: {config.device_id}")
                    self._get_screen_info()
                    return
                except Exception as e:
                    logger.warning(f"⚠️  配置的设备ID连接失败: {e}")
            
            # 自动检测并连接设备
            logger.info("🔍 正在自动检测设备...")
            devices = adbutils.adb.device_list()
            
            if not devices:
                raise Exception("未找到连接的设备，请检查USB调试是否开启")
            
            if len(devices) == 1:
                # 只有一个设备，直接连接
                device = devices[0]
                self.device = u2.connect(device)
                logger.info(f"✅ 自动连接设备成功: {device.serial}")
                config.device_id = device.serial  # 更新配置
            else:
                # 多个设备，让用户选择
                logger.info(f"📱 发现 {len(devices)} 个设备:")
                for i, dev in enumerate(devices):
                    logger.info(f"  {i+1}. {dev.serial}")
                
                choice = input("请选择设备序号 (1-{}): ".format(len(devices)))
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(devices):
                        device = devices[index]
                        self.device = u2.connect(device)
                        logger.info(f"✅ 连接设备成功: {device.serial}")
                        config.device_id = device.serial  # 更新配置
                    else:
                        raise ValueError("无效的设备序号")
                except ValueError:
                    # 默认连接第一个设备
                    device = devices[0]
                    self.device = u2.connect(device)
                    logger.info(f"✅ 默认连接第一个设备: {device.serial}")
                    config.device_id = device.serial
            
            self._get_screen_info()
            
        except Exception as e:
            logger.error(f"❌ 设备连接失败: {e}")
            logger.error("请检查设备连接和adb调试是否开启")
            raise
    
    def _get_screen_info(self):
        """获取屏幕信息"""
        try:
            self.screen_size = self.device.window_size()
            width, height = self.screen_size
            logger.info(f"📱 屏幕尺寸: {width}x{height}")
            
            # 更新配置中的屏幕分辨率
            config.default_screen_resolution = [width, height]
        except Exception as e:
            logger.warning(f"⚠️  获取屏幕信息失败: {e}")
            self.screen_size = (1080, 2400)  # 默认值
    
    def test_connection(self) -> bool:
        """测试设备连接和功能"""
        try:
            logger.info("🔍 正在测试设备连接...")
            
            # 测试屏幕信息
            if self.screen_size:
                width, height = self.screen_size
                logger.info(f"📱 屏幕尺寸: {width}x{height}")
            else:
                logger.warning("⚠️  无法获取屏幕信息")
            
            # 测试截图功能
            logger.info("📸 测试截图功能...")
            test_screenshot_path = "test_connection.jpg"
            self.device.screenshot(test_screenshot_path)
            
            # 测试完成后立即删除测试文件
            try:
                import os
                if os.path.exists(test_screenshot_path):
                    os.remove(test_screenshot_path)
            except Exception as e:
                logger.warning(f"⚠️ 清理测试截图文件失败: {e}")
            
            logger.info("✅ 截图功能正常")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 设备连接测试失败: {e}")
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
            width, height = self.screen_size if self.screen_size else (1080, 2400)
            
            if 0 <= x <= width and 0 <= y <= height:
                logger.info(f"🎯 点击位置: ({x}, {y})")
                self.device.click(x, y)
                time.sleep(3)  # 等待界面响应
                return True
            else:
                logger.error(f"❌ 坐标超出屏幕范围: ({x}, {y}) vs ({width}x{height})")
                return False
                
        except Exception as e:
            logger.error(f"❌ 点击操作失败: {e}")
            return False
    
    def long_click(self, x: int, y: int, duration: float = 2.0) -> bool:
        """长按指定坐标"""
        try:
            # 验证坐标是否在屏幕范围内
            width, height = self.screen_size if self.screen_size else (1080, 2400)
            
            if 0 <= x <= width and 0 <= y <= height:
                logger.info(f"👆 长按位置: ({x}, {y}), 持续时间: {duration}秒")
                self.device.long_click(x, y, duration)
                time.sleep(1)  # 等待界面响应
                return True
            else:
                logger.error(f"❌ 坐标超出屏幕范围: ({x}, {y}) vs ({width}x{height})")
                return False
                
        except Exception as e:
            logger.error(f"❌ 长按操作失败: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """输入文本"""
        try:
            logger.info(f"⌨️  输入文本: {text}")
            self.device.send_keys(text)
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"❌ 文本输入失败: {e}")
            return False
    
    def start_app(self, package_name: str) -> bool:
        """启动应用"""
        try:
            logger.info(f"📱 启动应用: {package_name}")
            self.device.app_start(package_name)
            time.sleep(3)  # 等待应用启动
            return True
        except Exception as e:
            logger.error(f"❌ 应用启动失败: {e}")
            return False
    
    def swipe(self, fx: int, fy: int, tx: int, ty: int, duration: float = 0.5) -> bool:
        """滑动操作"""
        try:
            # 验证坐标是否在屏幕范围内
            width, height = self.screen_size if self.screen_size else (1080, 2400)
            
            if not (0 <= fx <= width and 0 <= fy <= height):
                logger.error(f"❌ 起始坐标超出屏幕范围: ({fx}, {fy}) vs ({width}x{height})")
                return False
            
            if not (0 <= tx <= width and 0 <= ty <= height):
                logger.error(f"❌ 结束坐标超出屏幕范围: ({tx}, {ty}) vs ({width}x{height})")
                return False
            
            logger.info(f"👆 滑动操作: ({fx}, {fy}) -> ({tx}, {ty}), 持续时间: {duration}s")
            self.device.swipe(fx, fy, tx, ty, duration)
            time.sleep(2)  # 等待界面响应
            return True
                
        except Exception as e:
            logger.error(f"❌ 滑动操作失败: {e}")
            return False
    
    def get_current_app(self) -> dict:
        """获取当前应用信息"""
        try:
            return self.device.app_current()
        except:
            return {"package": "unknown", "activity": "unknown"}
    
    def get_device_info(self) -> dict:
        """获取设备信息"""
        try:
            device_info = self.device.device_info
            logger.info(f"📱 设备信息: {device_info}")
            return device_info
        except Exception as e:
            logger.warning(f"⚠️  获取设备信息失败: {e}")
            return {}
    
    def home(self) -> bool:
        """回到桌面"""
        try:
            logger.info("🏠 回到桌面")
            self.device.press("home")
            time.sleep(1)  # 等待桌面加载
            return True
        except Exception as e:
            logger.error(f"❌ 回到桌面失败: {e}")
            return False
    
    def kill_app(self, package_name: str) -> bool:
        """杀死指定应用（强制停止）"""
        try:
            logger.info(f"🔪 强制停止应用: {package_name}")
            self.device.app_stop(package_name)  # equivalent to `am force-stop`
            # self.device.app_clear(package_name) # equivalent to `pm clear`
            time.sleep(1)  # 等待应用完全关闭
            return True
        except Exception as e:
            logger.error(f"❌ 强制停止应用失败: {e}")
            return False
    
    
    def clean_apps(self, target_apps: list = None) -> bool:
        """停止指定的应用（不回到桌面，不清除数据）"""
        try:
            # 获取当前应用信息
            current_app = self.get_current_app()
            current_package = current_app.get("package", "")
            
            # 桌面应用列表
            launcher_packages = [
                "com.android.launcher3", 
                "com.miui.home", 
                "com.huawei.android.launcher",
                "com.hihonor.android.launcher",  # 荣耀桌面
                "com.oneplus.launcher",
                "com.samsung.android.launcher"
            ]
            
            apps_to_stop = set()  # 使用集合避免重复
            
            # 添加当前应用（如果不是桌面应用）
            if current_package and current_package not in launcher_packages:
                apps_to_stop.add(current_package)
            
            # 添加指定的目标应用
            if target_apps:
                apps_to_stop.update(target_apps)
            
            # 执行停止
            if apps_to_stop:
                logger.info(f"🛑 停止应用: {list(apps_to_stop)}")
                for app_package in apps_to_stop:
                    # 只强制停止应用，不清除数据
                    self.kill_app(app_package)
                logger.info(f"✅ 成功停止 {len(apps_to_stop)} 个应用")
                return True
            else:
                logger.info("ℹ️  没有需要停止的应用")
                return True
                
        except Exception as e:
            logger.error(f"❌ 停止应用失败: {e}")
            return False