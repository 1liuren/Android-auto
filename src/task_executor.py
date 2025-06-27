#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务执行器
负责协调各模块完成任务执行
"""

import os
import json
import uuid
from .config import config
from .device_controller import DeviceController
from .ai_analyzer import AIAnalyzer
from utils.image_marker import ImageMarker

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.device = DeviceController()
        self.ai_analyzer = AIAnalyzer()
        self.task_data = None
        self.output_dir = None
    
    def run_task(self, query: str) -> bool:
        """运行任务"""
        print(f"\n🚀 开始执行任务: {query}")
        
        # 测试设备连接
        if not self.device.test_connection():
            print("❌ 设备连接测试失败")
            return False
        
        # 初始化任务数据
        self._initialize_task(query)
        
        # 执行任务步骤
        success = self._execute_task_steps()
        
        # 保存任务结果
        self._save_task_result()
        
        return success
    
    def _initialize_task(self, query: str):
        """初始化任务数据"""
        episode_id = str(uuid.uuid4())[:8]
        self.task_data = config.get_task_template(query, episode_id)
        
        # 创建输出目录
        self.output_dir = f"output/{query}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📱 设备: {self.task_data['phone']} ({self.task_data['os']})")
        print(f"🆔 任务ID: {self.task_data['episode_id']}")
        print(f"📁 输出目录: {self.output_dir}")
    
    def _execute_task_steps(self) -> bool:
        """执行任务步骤"""
        step = 1
        
        while step <= config.max_steps:
            print(f"\n=== 步骤 {step} ===")
            
            # 1. 截图和获取XML
            screenshot_path, xml_path = self._capture_screen_state(step)
            
            # 2. AI分析
            ai_result = self.ai_analyzer.analyze_screen(xml_path, self.task_data['query'], step)
            
            # 3. 显示分析结果
            self._display_analysis_result(ai_result, step)
            
            # 4. 检查任务是否完成
            if self._is_task_completed(ai_result):
                self._handle_task_completion(ai_result, step, screenshot_path, xml_path)
                return True
            
            # 5. 生成标记图片（Open操作不需要标记）
            label_path = None
            plan = ai_result.get("plan", {})
            action_type = plan.get("type", "").lower()
            
            # Open操作不生成标记，其他操作生成标记
            if action_type != "open":
                label_path = self._generate_labeled_image(ai_result, step, screenshot_path)
            
            # 6. 保存步骤数据
            self._save_step_data(ai_result, step, screenshot_path, xml_path, label_path)
            
            # 7. 执行操作
            if not self._execute_action(ai_result.get("plan", {})):
                print(f"⚠️  步骤 {step} 操作执行失败，但继续下一步...")
            
            step += 1
        
        print(f"\n⚠️  任务执行达到最大步骤数 ({config.max_steps})，自动结束")
        return False
    
    def _capture_screen_state(self, step: int) -> tuple:
        """截图和获取XML状态"""
        screenshot_path = os.path.join(self.output_dir, f"1-{step}.jpg")
        xml_path = os.path.join(self.output_dir, f"1-{step}.xml")
        
        self.device.screenshot(screenshot_path)
        self.device.get_xml_hierarchy(xml_path)
        
        return screenshot_path, xml_path
    
    def _display_analysis_result(self, ai_result: dict, step: int):
        """显示AI分析结果"""
        observation = ai_result.get("observation", "无法分析当前界面")
        is_completed = ai_result.get("is_task_completed", False)
        completion_reason = ai_result.get("completion_reason", "")
        plan = ai_result.get("plan", {})
        
        print(f"\n📊 AI分析结果:")
        print(f"   观察: {observation}")
        print(f"   任务完成: {'✅ 是' if is_completed else '❌ 否'}")
        if completion_reason:
            print(f"   完成原因: {completion_reason}")
        print(f"   建议: {plan.get('description', '无建议')}")
        print(f"   位置: {plan.get('position', '未提供')}")
    
    def _is_task_completed(self, ai_result: dict) -> bool:
        """检查任务是否完成"""
        return (ai_result.get("is_task_completed", False) or 
                ai_result.get("plan", {}).get("type", "").lower() == "end")
    
    def _handle_task_completion(self, ai_result: dict, step: int, screenshot_path: str, xml_path: str):
        """处理任务完成"""
        completion_reason = ai_result.get("completion_reason", "任务目标已达到")
        
        print(f"\n🎉 任务执行完成！")
        print(f"✅ 完成原因: {completion_reason}")
        
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
        print(f"📝 任务总共执行了 {step} 个步骤")
    
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
            if "package" in plan and plan["package"]:
                cleaned_plan["package"] = plan["package"]
        
        elif action_type == "tap":
            # Tap操作需要box、times、position字段
            if "box" in plan:
                cleaned_plan["box"] = plan["box"]
            if "times" in plan:
                cleaned_plan["times"] = plan["times"]
            elif "position" in plan:
                # 如果没有times字段，默认为1
                cleaned_plan["times"] = 1
            if "position" in plan:
                cleaned_plan["position"] = plan["position"]
        
        elif action_type == "typing":
            # Typing操作需要box、text、position字段
            if "box" in plan:
                cleaned_plan["box"] = plan["box"]
            if "text" in plan and plan["text"]:
                cleaned_plan["text"] = plan["text"]
            if "position" in plan:
                cleaned_plan["position"] = plan["position"]
        
        elif action_type == "end":
            # End操作只需要description和type
            pass
        
        return cleaned_plan
    
    def _execute_action(self, plan: dict) -> bool:
        """执行操作"""
        action_type = plan.get("type", "").lower()
        
        if action_type == "tap" and "position" in plan:
            x, y = int(plan["position"][0]), int(plan["position"][1])
            return self.device.click(x, y)
            
        elif action_type == "typing" and "text" in plan:
            return self.device.input_text(plan["text"])
            
        elif action_type == "open" and "app" in plan:
            # 优先使用AI提供的包名
            if "package" in plan and plan["package"]:
                print(f"🚀 使用包名启动应用: {plan['package']}")
                return self.device.start_app(plan["package"])
            
            # 如果有position，点击应用图标
            if "position" in plan:
                x, y = int(plan["position"][0]), int(plan["position"][1])
                print(f"👆 点击应用图标启动: ({x}, {y})")
                return self.device.click(x, y)
            
            # 尝试内置包名映射
            app_packages = {
                "京东": "com.jingdong.app.mall",
                "淘宝": "com.taobao.taobao", 
                "微信": "com.tencent.mm",
                "支付宝": "com.eg.android.AlipayGphone",
                "网易云音乐": "com.netease.cloudmusic",
                "QQ": "com.tencent.mobileqq",
                "抖音": "com.ss.android.ugc.aweme",
                "百度": "com.baidu.searchbox",
                "美团": "com.sankuai.meituan",
                "饿了么": "me.ele.app",
                "滴滴出行": "com.sdu.didi.psnger",
                "高德地图": "com.autonavi.minimap",
                "知乎": "com.zhihu.android",
                "哔哩哔哩": "tv.danmaku.bili",
                "小红书": "com.xingin.xhs"
            }
            app_name = plan["app"]
            if app_name in app_packages:
                print(f"📱 使用内置包名启动应用: {app_packages[app_name]}")
                return self.device.start_app(app_packages[app_name])
            else:
                print(f"❌ 未找到应用 '{app_name}' 的包名，无法启动")
                return False
        
        elif action_type in ["manual", "end"]:
            print(f"⚠️  {action_type} 操作，跳过自动执行")
            return True
        
        print(f"❌ 未知操作类型: {action_type}")
        return False
    
    def _save_task_result(self):
        """保存任务结果"""
        task_file = os.path.join(self.output_dir, "task.json")
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(self.task_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 任务数据已保存: {task_file}")
    
    def save_interrupted_task(self):
        """保存中断的任务"""
        if self.task_data and self.output_dir:
            interrupted_file = os.path.join(self.output_dir, "task_interrupted.json")
            
            with open(interrupted_file, "w", encoding="utf-8") as f:
                json.dump(self.task_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 中断任务已保存: {interrupted_file}")
    
    def _generate_labeled_image(self, ai_result: dict, step: int, screenshot_path: str) -> str:
        """生成标记图片"""
        plan = ai_result.get("plan", {})
        label_path = os.path.join(self.output_dir, f"1-{step}_label.jpg")
        
        ImageMarker.mark_action(
            screenshot_path,
            label_path,
            position=plan.get("position"),
            box=plan.get("box"),
            description=plan.get("description", "")
        )
        
        return label_path 