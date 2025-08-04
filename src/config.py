#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

import os
from .logger_config import get_logger

logger = get_logger(__name__)

class Config:
    """配置管理类"""
    
    def __init__(self):
        # API配置
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        self.ark_api_key = os.getenv("ARK_API_KEY")
        
        # 模型配置  qwen-max-latest、deepseek-r1、qwen-plus-latest、doubao-1-5-pro-32k-250115
        self.model_name = "doubao-1-5-thinking-vision-pro-250428"  # 默认模型
        
        # 模型参数配置
        self.model_params = {
            "temperature": 0.0,
            "stream": False
            # "top_p": 0.9,
            # "top_k": 10,
            # "enable_thinking": False
        }
        
        # 多模态增强配置
        self.multimodal_enhancement = {
            "enabled": True,  # 是否启用多模态增强
            "fallback_to_xml": True,  # 增强失败时是否回退到XML
            "debug_mode": False  # 多模态调试模式
        }
        
        # 设备配置
        self.device_id = "auto"  # 自动检测设备
        
        # 默认屏幕分辨率
        self.default_screen_resolution = [1080, 2400]
        
        # 应用包名映射
        self.app_packages = {
            "美团外卖": "com.sankuai.meituan.takeoutnew", 
            "饿了么": "me.ele",
            "爱奇艺": "com.qiyi.video",
            "懂车帝": "com.ss.android.auto",
            "滴滴出行": "com.sdu.didi.psnger",
            "携程": "ctrip.android.view",
            "抖音": "com.ss.android.ugc.aweme"
        }
        
        #最大执行次数
        self.max_execution_times = 50
        
        # 隐私保护配置
        self.privacy_protection = {
            "enabled": True,  # 是否启用隐私保护
            "auto_detect": True,  # 是否自动检测隐私敏感信息
            "phone_anonymization": True,  # 是否启用手机号假名化
            "debug_mode": False,  # 隐私处理调试模式
            "temp_file_cleanup": True,  # 是否自动清理临时文件
            "protection_keywords": [  # 隐私敏感关键词
                '手机号', '电话', '联系方式', '个人信息', 
                '隐私', '填写', '注册', '登录', '验证',
                '联系人', '通讯录', '短信', '验证码'
            ]
        }
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置是否完整"""
        if not self.dashscope_api_key:
            logger.warning("DASHSCOPE_API_KEY 环境变量未设置")
            logger.info("请设置环境变量: set DASHSCOPE_API_KEY=your_api_key")
        else:
            logger.info("DashScope API密钥已配置")
    
    def print_model_config(self):
        """打印当前模型配置"""
        logger.info("🤖 大模型配置:")
        logger.info(f"   模型名称: {self.model_name}")
        logger.info("   参数配置:")
        for key, value in self.model_params.items():
            logger.info(f"     {key}: {value}")
        
        logger.info("   多模态增强配置:")
        for key, value in self.multimodal_enhancement.items():
            logger.info(f"     {key}: {value}")
    
    def get_app_package(self, app_name: str) -> str:
        """获取应用包名"""
        package = self.app_packages.get(app_name)
        if package:
            logger.debug(f"找到应用包名: {app_name} -> {package}")
        else:
            logger.warning(f"未找到应用包名: {app_name}")
        return package
    
    def update_screen_resolution(self, width: int, height: int):
        """更新屏幕分辨率"""
        self.default_screen_resolution = [width, height]
        logger.info(f"屏幕分辨率已更新: {width}x{height}")
        
    
    def get_ai_system_prompt(self) -> str:
        """获取AI系统提示词"""
        # 生成应用包名列表文本
        app_packages_text = "\n".join([f"- {app}: {package}" for app, package in self.app_packages.items()])
        
        return f"""你是一个专业的手机UI自动化助手。请根据XML界面结构信息和用户的操作指令，提供精确的操作信息：

1. observation: 描述当前界面状态，控制在20字以内：
2. is_task_completed: 布尔值，判断用户的任务是否已经完成
3. completion_reason: 如果任务完成，说明完成的原因（中文）
4. plan: 分析下一步应该执行的操作，包括：
   - description: 操作描述，必须按照以下格式规范：
     * 桌面打开app："打开[app名称]"（如："打开淘宝"）- 使用Open操作
     * 点击操作："点击搜索框"、"点击确认按钮"
     * 长按操作："长按[元素名称]"
     * 滑动操作："向上滑动"、"向下滑动"、"向左滑动"、"向右滑动"、"向左滑动频道栏"、"向右滑动频道栏"
     * 拖动操作："拖动进度条到80%"、"拖动[元素]到[位置]"
     * 输入操作："输入用户名"、"输入搜索内容"
     * 等待操作："等待广告结束"、"等待页面加载"
     * 其他操作：简洁明了的中文描述
   - type: 操作类型（Open/touch/long_touch/input/scroll/drag/wait/End等）
   - position: 点击位置坐标（仅在touch/long_touch/input操作时需要）
   - box: 元素边界框（touch/long_touch/input/scroll/drag操作时需要，Open和wait操作不需要）
   - times: 点击次数（默认为1，仅在touch操作时需要）
   - text: 输入文本（仅在input操作时需要）
   - app: 应用名称（仅在Open操作时需要）
   - package: 应用包名（仅在Open操作时需要，用于直接启动应用）
   - start_position: 滑动/拖动起始位置坐标（仅在scroll/drag操作时需要）
   - stop_position: 滑动/拖动结束位置坐标（仅在scroll/drag操作时需要）
   - duration: 滑动/拖动持续时间，单位秒（仅在scroll/drag操作时需要，默认0.5）
   - wait_time: 等待时长，单位秒（仅在wait操作时需要）
   - wait_reason: 等待原因（仅在wait操作时需要，如"广告播放"、"页面加载"等）

**应用包名列表：**
{app_packages_text}

**重要提示：**
- 打开应用优先使用Open操作（通过包名启动）
- 遇到广告页面，优先判断为等待操作
- 如果任务已完成，将type设置为"End"，description设置为"任务已完成"
- 文本输入：如果页面中没有com.github.uiautomator或者Switch IME的元素，说明当前页面并不可输入文字，需要先touch点击输入框激活
- 滑动和拖动操作注意方向，需要寻找的元素在上方时，需要向下滑动，其他方向同理
- 滑动和拖动操作注意bbox，起始点和结束点需要再bbox范围内
- 滑动的拖动操作前并不需要激活点击操作，直接滑动即可

**隐私保护检测：**
在分析界面时，请同时检测是否存在需要隐私保护的敏感信息：

1. **隐私信息检测规则：**
   - 手机号码：识别11位中国大陆手机号（1开头），重点关注EditText输入框、TextView显示文本等元素。
   - 姓名：检测常见中文姓名，优先关注“姓名”、“联系人”等字段，或明显为人名的文本。
   - 地址：检测包含“地址”、“收货地址”、“居住地”等关键词的文本，区分省市区（如“北京市海淀区”）与具体街道、楼栋、单元等详细信息。

2. **隐私信息替换规则：**
   - 姓名：生成可替换的虚假姓名，要求姓氏保持不变，名字部分用与原名长度一致的随机常见汉字替换，保证姓名结构合理，不能使用"*"号、某某、XX等代替。
   - 地址：省、市、区级别（如“北京市海淀区”）无需替换，街道、居住地等具体信息（如“中关村东升科技园A栋4单元”）需要用与原文字长度一致的合理伪造文本替换，伪造内容应为真实存在的街道、园区、楼栋等名称，保持格式和长度一致，不能使用"*"号、某某、XX等代替。
3. **隐私检测输出：**
   - 如果检测到隐私信息，在返回结果中包含privacy_detection字段，结构如下：
     - phone_numbers: 手机号原始文本和bbox
     - names: 姓名原始文本、bbox、替换后的虚假姓名
     - addresses: 地址原始文本、bbox、替换后的虚假地址
   - 如果没有检测到敏感信息，不输出privacy_detection字段


请用JSON格式返回结果，格式如下：
{{
    "observation": "界面状态描述",
    "is_task_completed": true/false,
    "completion_reason": "完成原因（如果已完成）",
    "privacy_detection": {{
        "phone_numbers": [
            {{
                "phone_number": "手机号码原始文本",
                "bbox": "<bbox>x1 y1 x2 y2</bbox>"
            }}
        ],
        "names": [
            {{
                "name": "姓名原始文本",
                "bbox": "<bbox>x1 y1 x2 y2</bbox>",
                "replacement": "伪造姓名"
            }}
        ],
        "addresses": [
            {{
                "address": "地址原始文本",
                "bbox": "<bbox>x1 y1 x2 y2</bbox>",
                "replacement": "伪造地址"
            }}
        ]
    }},
    "plan": {{
        "description": "操作描述",
        "type": "操作类型(Open/touch/long_touch/input/scroll/drag/wait/End)",
        "position": "<point>x y</point>",
        "box": "<bbox>x1 y1 x2 y2</bbox>",
        "times": 1,
        "text": "输入文本（input操作时需要）",
        "app": "应用名称（Open操作时需要）",
        "package": "应用包名（Open操作时需要）",
        "start_position": "<point>x y</point>",
        "stop_position": "<point>x y</point>",
        "duration": 在scroll/drag操作时需要,
        "wait_time": 在wait操作时需要,
        "wait_reason": "等待原因（wait操作时需要）"
    }}
}}"""
    
    def get_analysis_prompt(self, query: str, xml_content: str, current_step: int, history_steps: list = None, intervention_prompt: str = None, restart_from_step: int = None) -> str:
        """获取分析用的用户提示词
        
        Args:
            query: 原始任务描述
            xml_content: 当前界面XML内容
            current_step: 当前步骤数
            history_steps: 历史步骤列表
            intervention_prompt: 人工介入的补充说明
            restart_from_step: 从哪一步重新开始（用于插入人工介入）
        """
        
        # 构建历史步骤信息，并在适当位置插入人工介入
        history_text = ""
        if history_steps and len(history_steps) > 0:
            history_text = "\n=== 执行历史 ===\n"
            
            for i, step_info in enumerate(history_steps, 1):
                step_desc = step_info.get('description', '未知操作')
                step_type = step_info.get('type', '未知类型')
                step_obs = step_info.get('observation', '')
                step_number = step_info.get('step', i)  # 使用记录中的步骤号，如果没有则使用索引
                
                history_text += f"步骤{step_number}: 手机界面状态为：{step_obs}；执行了: {step_desc} ;类型: {step_type})\n"
                
                # 在重新开始的步骤后插入人工介入指导
                if (intervention_prompt and intervention_prompt.strip() and 
                    restart_from_step is not None and step_number == restart_from_step-1):
                    history_text += f"\n【人工介入指导】在第{restart_from_step}步后补充指导：{intervention_prompt.strip()}，请重点参考\n\n"
            
            history_text += "\n根据以上执行历史，请分析当前界面状态并决定下一步操作。如果上一步执行完任务了，请判断了任务完成。\n"
        
        # 如果没有历史记录但有人工介入，单独显示
        intervention_text = ""
        if (intervention_prompt and intervention_prompt.strip() and 
            (not history_steps or restart_from_step is None)):
            intervention_text = f"\n=== 人工介入指导 ===\n重要提示：{intervention_prompt.strip()}\n请特别注意上述人工指导，并根据指导内容调整后续操作策略。\n"
        
        return f"""
当前任务: {query}
当前步骤: {current_step}
{history_text}
{intervention_text}

请以上信息并告诉我下一步应该如何操作。请只返回一个JSON格式的响应，不要包含其他文本。"""

# 创建全局配置实例
config = Config()