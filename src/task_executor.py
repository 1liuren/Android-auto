#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务执行器
负责协调各模块完成任务执行
"""

import os
import json
import time
import uuid
import re
from typing import Optional, List
from .config import config
from .device_controller import DeviceController
from .ai_analyzer import AIAnalyzer
from .privacy_protector import PrivacyProtector
from utils.image_marker import ImageMarker
from .logger_config import get_logger
from datetime import datetime

logger = get_logger(__name__)

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, output_base_dir="output"):
        self.device = DeviceController()
        self.ai_analyzer = AIAnalyzer()
        self.privacy_protector = PrivacyProtector()
        self.task_data = None
        self.output_dir = None
        self.output_base_dir = output_base_dir  # 自定义输出基础目录
        self.history_steps = []  # 添加历史步骤记录
        self.privacy_enabled = False  # 隐私保护开关
        self.is_interrupted = False  # 中断标志
    
    def interrupt_task(self):
        """中断当前任务"""
        self.is_interrupted = True
        logger.info("🛑 收到任务中断请求")
    
    def run_task(self, query: str) -> bool:
        """运行任务"""
        logger.info(f"\n🚀 开始执行任务: {query}")
        
        # 重置中断标志
        self.is_interrupted = False
        
        # 检查中断
        if self.is_interrupted:
            logger.info("🛑 任务在开始前被中断")
            return False
        
        # 测试设备连接
        if not self.device.test_connection():
            logger.error("❌ 设备连接测试失败")
            return False
        
        # 初始化任务数据
        self._initialize_task(query)
        
        # 执行任务步骤
        success = self._execute_task_steps()
        
        # 检查是否被中断
        if self.is_interrupted:
            logger.info("🛑 任务被用户中断")
            self.save_interrupted_task()
            success = False
        
        # 保存任务结果
        if not self.is_interrupted:
            self._save_task_result()
        
        # 无论任务是否成功完成，都清理应用
        logger.info(f"\n🧹 任务结束，正在清理应用...")
        self.device.clean_apps()
        
        return success
    
    def _initialize_task(self, query: str):
        """初始化任务数据"""
        # 重置历史步骤
        self.history_steps = []
        self.privacy_protector = PrivacyProtector()
        
        pattern = r'[（(].*?[）)]'
        if re.search(pattern, query):
            # 去除括号内容
            clean_query = re.sub(pattern, '', query)
            logger.info(f"🔄 原始查询: {query}")
            logger.info(f"🔄 处理后查询: {clean_query}")
        else:
            clean_query = query
        
        episode_id = str(uuid.uuid4())[:8]
        self.query = query
        self.task_data = {
            "phone": "Unknown Device",
            "os": "Unknown OS", 
            "screen_resolution": config.default_screen_resolution,
            "query": clean_query,
            "episode_id": episode_id,
            "data": []
        }
        
        # 获取真实设备信息并更新任务数据
        device_info = self.device.get_device_info()
        if device_info:
            # 更新设备信息
            self.task_data['phone'] = f"{device_info.get('brand', 'Unknown')} {device_info.get('model', 'Unknown')}"
            self.task_data['os'] = f"Android {device_info.get('version', 'Unknown')}"
            
            logger.info(f"📱 设备: {self.task_data['phone']}")
            logger.info(f"🤖 系统: {self.task_data['os']}")
            logger.info(f"🏗️  架构: {device_info.get('arch', 'Unknown')}")
            logger.info(f"📲 SDK: {device_info.get('sdk', 'Unknown')}")
        
        # 创建输出目录
        self.output_dir = f"{self.output_base_dir}/{clean_query}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 判断是否需要启用隐私保护
        if config.privacy_protection.get("enabled", True):
            self.privacy_enabled = True
            logger.info(f"🔒 隐私保护模式已启用")
        else:
            self.privacy_enabled = False
            logger.info(f"📄 隐私保护功能已关闭")
        
        logger.info(f"🆔 任务ID: {self.task_data['episode_id']}")
        logger.info(f"📁 输出目录: {self.output_dir}")
    
    def _execute_task_steps(self) -> bool:
        """执行任务步骤"""
        step = 1
        
        while step <= config.max_execution_times:  # 最大步骤数
            # 检查中断请求
            if self.is_interrupted:
                logger.info(f"🛑 步骤 {step} 开始前检测到中断请求，停止执行")
                return False
                
            logger.info(f"\n=== 步骤 {step} ===")
            
            # 1. 截图和获取XML
            screenshot_path, xml_path = self._wait_for_page_load(step)
            
            # 检查中断请求
            if self.is_interrupted:
                logger.info(f"🛑 步骤 {step} 页面加载后检测到中断请求，停止执行")
                return False
            
            # 2. AI分析（包含隐私检测）
            try:
                ai_result = self.ai_analyzer.analyze_screen(
                    xml_path, 
                    self.query, 
                    step,
                    screenshot_path=screenshot_path,
                    history_steps = self.history_steps
                )
            except Exception as e:
                logger.error(f"❌ AI分析失败: {str(e)}")
                return False
            
            # 检查中断请求
            if self.is_interrupted:
                logger.info(f"🛑 步骤 {step} AI分析后检测到中断请求，停止执行")
                return False
            
            # 3. 隐私保护处理（基于AI分析结果）
            final_screenshot_path = screenshot_path
            if self.privacy_enabled and ai_result.get("privacy_detection"):
                privacy_info = self._process_privacy_from_ai_result(ai_result, screenshot_path)
                if privacy_info.get("protected_screenshot"):
                    final_screenshot_path = privacy_info["protected_screenshot"]
            
            # 4. 显示分析结果
            self._display_analysis_result(ai_result, step)
            
            # 5. 检查任务是否完成
            if self._is_task_completed(ai_result):
                self._handle_task_completion(ai_result, step, final_screenshot_path, xml_path)
                return True
            
            # 6. 生成标记图片（某些操作不需要标记）
            label_path = None
            plan = ai_result.get("plan", {})
            action_type = plan.get("type", "").lower()
            
            # 兼容旧操作类型名称
            if action_type == "tap":
                action_type = "touch"
            elif action_type == "typing":
                action_type = "input"
            elif action_type == "swipe":
                action_type = "scroll"
            
            # Open和wait操作不生成标记，其他操作生成标记
            if action_type not in ["open", "wait", "end"]:
                label_path = self._generate_labeled_image(ai_result, step, final_screenshot_path)
            
            # 7. 保存步骤数据
            self._save_step_data(ai_result, step, final_screenshot_path, xml_path, label_path)
            
            # 8. 执行操作
            if not self._execute_action(ai_result.get("plan", {})):
                logger.warning(f"⚠️  步骤 {step} 操作执行失败，但继续下一步...")
            
            # 检查中断请求
            if self.is_interrupted:
                logger.info(f"🛑 步骤 {step} 操作执行后检测到中断请求，停止执行")
                return False
            
            # 9. 记录历史步骤（在执行操作后）
            observation = ai_result.get("observation", "")
            self._record_history_step(plan, observation)
            
            # 执行操作后等待时间，同时检查中断
            # if action_type == "open":
            #     for i in range(50):  # 5秒等待，每0.1秒检查一次中断
            #         if self.is_interrupted:
            #             logger.info(f"🛑 步骤 {step} 等待过程中检测到中断请求，停止执行")
            #             return False
            #         time.sleep(0.1)
            
            step += 1
        
        logger.warning(f"\n⚠️  任务执行达到最大步骤数 (10)，自动结束")
        return False
    
    def _capture_screen_state(self, step: int) -> tuple:
        """捕获屏幕状态，返回截图路径和XML路径"""
        
        # 截图
        screenshot_name = f"1-{step}.jpg"
        screenshot_path = os.path.join(self.output_dir, screenshot_name)
        self.device.screenshot(screenshot_path)
        
        # 获取XML
        xml_name = f"1-{step}.xml"
        xml_path = os.path.join(self.output_dir, xml_name)
        self.device.get_xml_hierarchy(xml_path)
        
        # logger.info(f"📱 已捕获屏幕状态: {screenshot_name}, {xml_name}")
        return screenshot_path, xml_path
    
    def _is_page_loading(self, xml_path: str) -> bool:
        """检测页面是否正在加载中"""
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # 检测加载状态的特征
            loading_indicators = [
                # WebView加载状态
                'NAF="true"' in xml_content and 'android.webkit.WebView' in xml_content,
                # 常见的加载文本
                any(keyword in xml_content.lower() for keyword in [
                    'loading', '加载中', '正在加载', 'please wait', '请稍候'
                ]),
                # 空白页面特征（主要内容区域为空）
                xml_content.count('<node') < 50 and 'WebView' in xml_content
            ]
            
            # 如果有任何一个指标为True，认为页面正在加载
            is_loading = any(loading_indicators)
            
            if is_loading:
                logger.info("🔄 检测到页面正在加载中...")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ 检测页面加载状态失败: {e}")
            return False
    
    def _wait_for_page_load(self, step: int, max_retries: int = 3) -> tuple:
        """等待页面加载完成，返回最终的截图和XML路径"""
        for retry in range(max_retries):
            screenshot_path, xml_path = self._capture_screen_state(step)
            
            if not self._is_page_loading(xml_path):
                logger.info("✅ 页面加载完成")
                return screenshot_path, xml_path
            
            if retry < max_retries - 1:  # 不是最后一次重试
                logger.info(f"⏳ 页面加载中，等待2秒后重试... (第{retry + 1}/{max_retries}次)")
                
                # 删除加载中的临时文件，避免保存中间状态
                try:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        logger.debug(f"🗑️ 删除加载中的截图: {os.path.basename(screenshot_path)}")
                    if os.path.exists(xml_path):
                        os.remove(xml_path)
                        logger.debug(f"🗑️ 删除加载中的XML: {os.path.basename(xml_path)}")
                except Exception as e:
                    logger.warning(f"⚠️ 删除临时文件失败: {e}")
                
                time.sleep(2)
            else:
                logger.warning("⚠️ 页面可能仍在加载，但已达到最大重试次数，保留当前文件")
        
        return screenshot_path, xml_path
    
    def _display_analysis_result(self, ai_result: dict, step: int):
        """显示AI分析结果"""
        observation = ai_result.get("observation", "无法分析当前界面")
        is_completed = ai_result.get("is_task_completed", False)
        completion_reason = ai_result.get("completion_reason", "")
        plan = ai_result.get("plan", {})
        privacy_detection = ai_result.get("privacy_detection", {})
        
        logger.info(f"\n📊 AI分析结果:")
        logger.info(f"   观察: {observation}")
        logger.info(f"   任务完成: {'✅ 是' if is_completed else '❌ 否'}")
        if completion_reason:
            logger.info(f"   完成原因: {completion_reason}")
        
        # 显示隐私检测结果
        if privacy_detection:
            phone_numbers = privacy_detection.get("phone_numbers", [])
            if phone_numbers:
                phone_count = len(phone_numbers)
                logger.info(f"   🔒 隐私检测: 发现 {phone_count} 个敏感手机号")
                for i, phone_data in enumerate(phone_numbers, 1):
                    phone_num = phone_data.get("phone_number", "")
                    logger.info(f"      {i}. {phone_num}")
            else:
                logger.info(f"   🔒 隐私检测: 未发现敏感信息")
        else:
            logger.info(f"   🔒 隐私检测: 未发现敏感信息")
        
        logger.info(f"   建议: {plan.get('description', '无建议')}")
        logger.info(f"   位置: {plan.get('position', '未提供')}")
    
    def _is_task_completed(self, ai_result: dict) -> bool:
        """检查任务是否完成"""
        return (ai_result.get("is_task_completed", False) or 
                ai_result.get("plan", {}).get("type", "").lower() == "end")
    
    def _handle_task_completion(self, ai_result: dict, step: int, screenshot_path: str, xml_path: str):
        """处理任务完成"""
        completion_reason = ai_result.get("completion_reason", "任务目标已达到")
        
        logger.info(f"\n🎉 任务执行完成！")
        logger.info(f"✅ 完成原因: {completion_reason}")
        
        # 保存完成步骤数据
        plan = ai_result.get("plan", {})
        
        # 创建End类型的plan
        end_plan = {
            "description": "任务已完成",
            "type": "End"
        }
        
        step_data = {
            "step": step,
            "screenshot": os.path.basename(screenshot_path),
            "xml": os.path.basename(xml_path),
            "observation": ai_result.get("observation", ""),
            "plan": [end_plan]
        }
        
        self.task_data["data"].append(step_data)
        logger.info(f"📝 任务总共执行了 {step} 个步骤")
    
    def _save_step_data(self, ai_result: dict, step: int, screenshot_path: str, xml_path: str, label_path: str):
        """保存步骤数据"""
        plan = ai_result.get("plan", {})
        
        # 清理plan中的空字段
        cleaned_plan = self._clean_plan_data(plan)
        
        step_data = {
            "step": step,
            "screenshot": os.path.basename(screenshot_path),
            "xml": os.path.basename(xml_path),
            "observation": ai_result.get("observation", ""),
            "plan": [cleaned_plan]
        }
        
        # 只有当存在label_path时才添加label字段
        if label_path:
            step_data["label"] = os.path.basename(label_path)
        
        self.task_data["data"].append(step_data)
    
    def _clean_plan_data(self, plan: dict) -> dict:
        """清理plan数据，移除空字段"""
        cleaned_plan = {}
        
        # 必需字段
        if "description" in plan:
            cleaned_plan["description"] = plan["description"]
        if "type" in plan:
            cleaned_plan["type"] = plan["type"]
        
        # 根据操作类型添加相应字段
        action_type = plan.get("type", "").lower()
        
        if action_type == "open":
            # Open操作需要app和package字段
            if "app" in plan and plan["app"]:
                cleaned_plan["app"] = plan["app"]
            # if "package" in plan and plan["package"]:
            #     cleaned_plan["package"] = plan["package"]
        
        elif action_type in ["tap", "touch"]:
            # touch操作需要box、times、position字段
            if "box" in plan:
                cleaned_plan["box"] = plan["box"]
            if "times" in plan:
                cleaned_plan["times"] = plan["times"]
            elif "position" in plan:
                # 如果没有times字段，默认为1
                cleaned_plan["times"] = 1
            if "position" in plan:
                cleaned_plan["position"] = plan["position"]
        
        elif action_type == "long_touch":
            # long_touch操作需要box、position字段
            if "box" in plan:
                cleaned_plan["box"] = plan["box"]
            if "position" in plan:
                cleaned_plan["position"] = plan["position"]
        
        elif action_type in ["typing", "input"]:
            # input操作需要box、text、position字段
            if "box" in plan:
                cleaned_plan["box"] = plan["box"]
            if "text" in plan and plan["text"]:
                cleaned_plan["text"] = plan["text"]
            if "position" in plan:
                cleaned_plan["position"] = plan["position"]
        
        elif action_type in ["swipe", "scroll", "drag"]:
            # scroll/drag操作需要start_position、stop_position、box、duration字段
            if "box" in plan:
                cleaned_plan["box"] = plan["box"]
            if "start_position" in plan:
                cleaned_plan["start_position"] = plan["start_position"]
            if "stop_position" in plan:
                cleaned_plan["stop_position"] = plan["stop_position"]
            # 兼容旧格式
            if "swipe_start" in plan and "start_position" not in plan:
                cleaned_plan["start_position"] = plan["swipe_start"]
            if "swipe_end" in plan and "stop_position" not in plan:
                cleaned_plan["stop_position"] = plan["swipe_end"]
            if "duration" in plan:
                cleaned_plan["duration"] = plan["duration"]
            else:
                cleaned_plan["duration"] = 0.5  # 默认滑动时间
        
        elif action_type == "wait":
            # wait操作需要wait_time、wait_reason字段
            if "wait_time" in plan:
                cleaned_plan["wait_time"] = plan["wait_time"]
            else:
                cleaned_plan["wait_time"] = 3  # 默认等待时间
            if "wait_reason" in plan:
                cleaned_plan["wait_reason"] = plan["wait_reason"]
            else:
                cleaned_plan["wait_reason"] = "页面处理"
        
        elif action_type == "end":
            # End操作只需要description和type
            pass
        
        return cleaned_plan
    
    def _execute_action(self, plan: dict) -> bool:
        """执行操作"""
        action_type = plan.get("type", "").lower()
        
        # 兼容旧的操作类型名称
        if action_type == "tap":
            action_type = "touch"
        elif action_type == "typing":
            action_type = "input"
        elif action_type == "swipe":
            action_type = "scroll"
        
        if action_type == "touch" and "position" in plan:
            x, y = int(plan["position"][0]), int(plan["position"][1])
            times = plan.get("times", 1)
            logger.info(f"👆 执行点击: ({x}, {y}), 次数: {times}")
            for i in range(times):
                if not self.device.click(x, y):
                    return False
                if times > 1 and i < times - 1:
                    time.sleep(0.5)  # 多次点击间隔
            return True
            
        elif action_type == "long_touch" and "position" in plan:
            x, y = int(plan["position"][0]), int(plan["position"][1])
            logger.info(f"👆 执行长按: ({x}, {y})")
            return self.device.long_click(x, y)
            
        elif action_type == "input" and "text" in plan:
            text = plan["text"]
            logger.info(f"⌨️ 执行输入: {text}")
            return self.device.input_text(text)
        
        elif action_type in ["scroll", "drag"]:
            # 优先使用新格式字段
            start_pos = plan.get("start_position") or plan.get("swipe_start")
            stop_pos = plan.get("stop_position") or plan.get("swipe_end")
            
            if start_pos and stop_pos:
                fx, fy = int(start_pos[0]), int(start_pos[1])
                tx, ty = int(stop_pos[0]), int(stop_pos[1])
                duration = plan.get("duration", 0.5)
                
                if action_type == "scroll":
                    logger.info(f"📜 执行滑动: ({fx}, {fy}) -> ({tx}, {ty})")
                else:  # drag
                    logger.info(f"🖱️ 执行拖动: ({fx}, {fy}) -> ({tx}, {ty})")
                
                return self.device.swipe(fx, fy, tx, ty, duration)
            else:
                logger.error(f"❌ {action_type}操作缺少必要参数: start_position={start_pos}, stop_position={stop_pos}")
                return False
        
        elif action_type == "wait":
            wait_time = plan.get("wait_time", 3)
            wait_reason = plan.get("wait_reason", "页面处理")
            logger.info(f"⏰ 执行等待: {wait_reason}, 时长: {wait_time}秒")
            
            # 可中断的等待
            for i in range(int(wait_time * 10)):  # 每0.1秒检查一次中断
                if self.is_interrupted:
                    logger.info(f"🛑 等待过程中检测到中断请求")
                    return False
                time.sleep(0.1)
            
            logger.info(f"✅ 等待完成: {wait_reason}")
            return True
            
        elif action_type == "open" and "app" in plan:
            app_name = plan["app"]
            
            # 第一优先级：使用AI提供的包名
            if "package" in plan and plan["package"]:
                package_name = plan["package"]
                # logger.info(f"🤖 使用AI提供的包名启动应用: {package_name}")
                try:
                    success = self.device.start_app(package_name)
                    if success:
                        return True
                    else:
                        logger.warning(f"⚠️  AI包名启动失败，尝试其他方式")
                except Exception as e:
                    logger.warning(f"⚠️  AI包名启动异常: {e}，尝试其他方式")
            
            # 第二优先级：使用配置中的内置包名映射
            if app_name in config.app_packages:
                package_name = config.app_packages[app_name]
                logger.info(f"📱 使用内置包名启动应用: {app_name} -> {package_name}")
                try:
                    success = self.device.start_app(package_name)
                    if success:
                        return True
                    else:
                        logger.warning(f"⚠️  内置包名启动失败，尝试点击方式")
                except Exception as e:
                    logger.warning(f"⚠️  内置包名启动异常: {e}，尝试点击方式")
            
            # 第三优先级：点击应用图标（如果AI提供了position）
            if "position" in plan:
                x, y = int(plan["position"][0]), int(plan["position"][1])
                logger.info(f"👆 点击应用图标启动: {app_name} at ({x}, {y})")
                return self.device.click(x, y)
            
            # 如果所有方式都失败
            logger.error(f"❌ 无法启动应用 '{app_name}':")
            logger.error(f"   - AI未提供有效包名")
            logger.error(f"   - 未在内置映射中找到包名")
            logger.error(f"   - AI未提供点击位置")
            return False
        
        elif action_type in ["manual", "end"]:
            logger.info(f"⚠️  {action_type} 操作，跳过自动执行")
            return True
        
        logger.error(f"❌ 未知操作类型: {action_type}")
        return False
    
    def _save_task_result(self):
        """保存任务结果"""
        task_file = os.path.join(self.output_dir, "task.json")
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(self.task_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 任务数据已保存: {task_file}")
    
    def save_interrupted_task(self):
        """保存中断的任务"""
        if self.task_data and self.output_dir:
            interrupted_file = os.path.join(self.output_dir, "task_interrupted.json")
            
            with open(interrupted_file, "w", encoding="utf-8") as f:
                json.dump(self.task_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 中断任务已保存: {interrupted_file}")
    
    def _generate_labeled_image(self, ai_result: dict, step: int, screenshot_path: str) -> str:
        """生成标记图片"""
        plan = ai_result.get("plan", {})
        label_path = os.path.join(self.output_dir, f"1-{step}_label.jpg")
        
        action_type = plan.get("type", "").lower()
        
        ImageMarker.mark_action(
            screenshot_path,
            label_path,
            position=plan.get("position"),
            box=plan.get("box"),
            description=plan.get("description", ""),
            action_type=action_type,
            start_position=plan.get("start_position"),
            stop_position=plan.get("stop_position"),
            swipe_start=plan.get("swipe_start"),
            swipe_end=plan.get("swipe_end")
        )
        
        return label_path

    def _record_history_step(self, plan: dict, observation: str = ""):
        """记录历史步骤"""
        if plan and "description" in plan and "type" in plan:
            history_item = {
                "description": plan["description"],
                "type": plan["type"],
                "observation": observation
            }
            self.history_steps.append(history_item)
            logger.debug(f"📝 历史步骤已记录: {history_item['description']} ({history_item['type']})") 

    def _process_privacy_data(self, data_list: List[dict], data_type: str) -> List[dict]:
        """处理隐私数据的通用方法"""
        result = []
        
        for data_item in data_list:
            # 解析bounds字符串
            bounds_str = data_item.get("bounds", "")
            bbox = self._parse_bounds_string(bounds_str)
            
            if bbox:
                if data_type == "phone_numbers":
                    info = {
                        "display_number": data_item.get("phone_number", ""),
                        "bbox": bbox,
                        "replacement": data_item.get("replacement", "13800138000")
                    }
                elif data_type == "names":
                    info = {
                        "content": data_item.get("name", ""),
                        "bbox": bbox,
                        "replacement": data_item.get("replacement", "王一一")
                    }
                elif data_type == "addresses":
                    info = {
                        "content": data_item.get("address", ""),
                        "bbox": bbox,
                        "replacement": data_item.get("replacement", "北京市海淀区山河园街道")
                    }
                else:
                    continue  # 未知类型，跳过
                
                result.append(info)
        
        return result

    def _process_privacy_from_ai_result(self, ai_result: dict, screenshot_path: str) -> dict:
        """基于AI分析结果处理隐私保护"""
        try:
            privacy_detection = ai_result.get("privacy_detection", {})
                       
            # 检查是否有隐私数据
            phone_numbers_data = privacy_detection.get("phone_numbers", [])
            names_data = privacy_detection.get("names", [])
            addresses_data = privacy_detection.get("addresses", [])
            
            # 如果没有任何隐私数据，直接返回
            if not phone_numbers_data and not names_data and not addresses_data:
                return {"protected_screenshot": screenshot_path}
            
            # 使用通用方法处理各类隐私数据
            phone_numbers = self._process_privacy_data(phone_numbers_data, "phone_numbers")
            names = self._process_privacy_data(names_data, "names")
            addresses = self._process_privacy_data(addresses_data, "addresses")
            
            # 如果有任何隐私数据，进行处理
            if phone_numbers or names or addresses:
                # 构建简化的隐私信息
                privacy_info = {}
                if phone_numbers:
                    privacy_info["phone_numbers"] = phone_numbers
                if names:
                    privacy_info["names"] = names
                if addresses:
                    privacy_info["addresses"] = addresses
                
                # 进行隐私保护处理
                protected_path = self.privacy_protector.protect_screenshot(screenshot_path, privacy_info)
                
                # 统计信息
                privacy_types = []
                if phone_numbers:
                    privacy_types.append(f"{len(phone_numbers)} 个手机号")
                if names:
                    privacy_types.append(f"{len(names)} 个姓名")
                if addresses:
                    privacy_types.append(f"{len(addresses)} 个地址")
                
                logger.info(f"🔒 AI检测到隐私信息，已应用保护: {', '.join(privacy_types)}")
                return {"protected_screenshot": protected_path, "privacy_info": privacy_info}
            
            return {"protected_screenshot": screenshot_path}
            
        except Exception as e:
            logger.error(f"❌ AI隐私保护处理失败: {e}")
            return {"protected_screenshot": screenshot_path}
    
    def _parse_bounds_string(self, bounds_str: str) -> Optional[List[List[int]]]:
        """解析bounds字符串"""
        try:
            import re
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

 