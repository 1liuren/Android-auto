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
        
        # 模型配置  qwen-max、deepseek-r1、qwen-plus
        self.model_name = "deepseek-r1"  # 默认模型
        
        # 模型参数配置
        self.model_params = {
            "temperature": 0.0,
            "stream": False,
            "top_p": 0.8,
            "top_k": 50,
            "enable_thinking": False
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
            "携程": "ctrip.android.view"
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

1. observation: 描述当前界面状态，必须按照以下格式规范：

   **桌面场景（打开app）：**
   格式："当前是手机/平板桌面，包含/有[app1]、[app2]、[app3]等app"
   要求：至少包含两个app名称，其中一个是需要打开的目标app
   示例："当前是手机桌面，有淘宝、京东、百度等app"

   **搜索框场景：**
   - 搜索框未激活：格式："当前是[页面名称]，底部导航栏有[功能1]、[功能2]等功能、顶部有搜索框，点击搜索框可以进行相关搜索"
   - 搜索框已激活：格式："当前是[页面名称]，顶部搜索框已打开，可以输入搜索内容"
   示例："当前是爱奇艺首页，底部导航栏有首页、会员等功能、顶部有搜索框，点击搜索框可以进行相关搜索"

   **搜索按钮场景：**
   格式："当前是[页面名称]，底部导航栏有[功能1]、[功能2]等功能/按钮、右上角有搜索按钮，点击搜索按钮可以进行搜索"
   示例："当前为微信主页面，下方有通讯录、发现等页面按钮，右上角有搜索按钮可以搜索内容"

   **功能页面场景：**
   格式："当前是[应用名][功能名]页面"
   示例："当前是懂车帝排行榜页面"、"当前是美团外卖甜品饮品页面"
   
   **其他场景：**
   简洁描述当前界面状态和主要元素（15-25字）
   
   **⚠️ 重要说明：**
   - observation中不要提及WebView、Fragment等技术细节
   - 专注描述用户可见的功能和内容

2. is_task_completed: 布尔值，判断用户的任务是否已经完成
3. completion_reason: 如果任务完成，说明完成的原因（中文）
4. plan: 分析下一步应该执行的操作，包括：
   - description: 操作描述，必须按照以下格式规范：
     * 桌面打开app："打开[app名称]"（如："打开淘宝"）- 使用Open操作而非Tap
     * 搜索框操作："点击搜索框"
     * 搜索按钮操作："点击搜索按钮"
     * 滑动操作："向上滑动"、"向下滑动"、"向左滑动"、"向右滑动"、"向左滑动频道栏"、"向右滑动频道栏"
     * 其他操作：简洁明了的中文描述
   - type: 操作类型（Open/Tap/Typing/Swipe/End等）
   - position: 点击位置坐标（仅在Tap/Typing操作时需要，Open和Swipe操作不需要）
   - box: 元素边界框（Tap/Typing/Swipe操作时需要，Open操作不需要）
   - times: 点击次数（默认为1，仅在Tap操作时需要）
   - text: 输入文本（仅在Typing操作时需要）
   - app: 应用名称（仅在Open操作时需要）
   - package: 应用包名（仅在Open操作时需要，用于直接启动应用）
   - start_position: 滑动起始位置坐标（仅在Swipe操作时需要）
   - stop_position: 滑动结束位置坐标（仅在Swipe操作时需要）
   - duration: 滑动持续时间，单位秒（仅在Swipe操作时需要，默认0.5）

操作类型说明：
- Open: 打开应用（需要app和package字段，不需要position和box）
  * 当需要启动/打开手机应用时，优先使用Open操作
  * 适用于从桌面、应用列表等场景打开应用
  * 通过应用包名直接启动，更可靠更快速
- Tap: 点击操作（需要position、box、times字段）
  * 用于点击界面元素，如按钮、链接、菜单项等
  * 不适用于打开应用，应优先使用Open操作
- Typing: 输入文本（需要position、box、text字段）
- Swipe: 滑动操作（需要start_position、stop_position、box、duration字段）
- End: 任务完成

**应用包名列表：**
{app_packages_text}

**任务完成判断标准：**
- **打开应用：** 应用启动并显示主界面时完成
- **导航类：** 到达目标页面/功能时完成
- **搜索类：** 搜索结果显示时完成
- **组合任务：** 所有子任务都完成时才算完成
- 完成任务之后避免多余操作，如滑动等

**任务完成判断示例：**
- 任务要求打开美团外卖的"看病买药"功能，当成功跳转到相关页面后，即使页面XML中不包含"看病买药"字样，也应判断为任务完成
- 任务要求打开美团外卖的"客服中心"，当成功跳转到相关页面后，即使页面XML中不包含"客服中心"字样，也应判断为任务完成
- 判断任务完成应基于页面功能和上下文，而非仅依赖特定文本的出现

**滑动操作判断指导：**
1. **爱奇艺频道栏滑动：**
   - 如果任务要求"打开电影"、"进入电影"、"查看电影"、"电影栏目"，但当前界面只显示"首页"、"电视剧"等少数频道，需要**向左滑动频道栏**查找电影频道
   - 爱奇艺频道栏通常位于屏幕上方，包含"首页"、"电视剧"等标签，需要左右滑动来查看更多频道

2. **其他滑动场景：**
   - 当界面内容可能需要滚动查看更多选项时
   - 当搜索目标内容在当前界面不可见，但逻辑上应该存在时

**滑动操作位置计算方法：**
**重要**：滑动操作必须在目标框的中心点附近进行，确保滑动在正确的区域内！

1. **定位滑动区域**：首先从XML中找到可滑动的区域（通常是HorizontalScrollView或类似的容器）
2. **滑动操作的起点**：不能和其他元素重叠，不能和页面边缘重叠
2. **计算中心Y坐标**：使用区域的bounds="[x1,y1][x2,y2]"，计算Y中心 = (y1 + y2) / 2
3. **计算中心X坐标**：计算X中心 = (x1 + x2) / 2
4. **设置滑动起点**：start_position = [X中心 + 150, Y中心]  # 左右滑动
5. **设置滑动终点**：stop_position = [X中心 - 150, Y中心]  # 左右滑动
6. **上下滑动同理**：start_position = [X中心, Y中心 + 150]，stop_position = [X中心, Y中心 - 150]  # 上下滑动
6. **设置滑动区域box**：完整的区域边界框

**示例计算：**
- 如果频道栏bounds="[9,204][977,313]"
- Y中心 = (204 + 313) / 2 = 258
- start_position = [643, 258]  （493+150）
- stop_position = [343, 258]   （493-150）
- box = [[9, 204], [977, 313]]

**滑动操作格式：**
- type: "Swipe"
- start_position: [起始x, 中心y] (在滑动区域内，偏右位置)
- stop_position: [结束x, 中心y] (在滑动区域内，偏左位置)
- box: [[x1, y1], [x2, y2]] (滑动区域的完整边界框)
- duration: 0.5 (滑动持续时间)

**文本输入：**
- 如果任务要求输入文本，需要先点击输入框，再输入文本
- 如果页面中没有com.github.uiautomator的元素，说明当前页面并不可输入文字，需要先点击输入框，再输入文本

**重要提示：**
- 打开应用优先使用Open操作（通过包名启动）
- 点击功能按钮后页面跳转成功即完成任务
- 基于XML的bounds属性计算精确坐标：position = [(x1+x2)/2, (y1+y2)/2]
- 优先选择clickable="true"的元素
- 如果任务已完成，将type设置为"End"，description设置为"任务已完成"
- 在订票等任务中，一般出发地为页面左边，目的地为页面右边，在选择出发地和目的地的搜索栏中，搜索栏中的提示文本可能都是“请输入目的城市/车站名”，这个不能作为判断当前是在选择出发地还是目的地的依据
- 在xml信息中可能有当前页面隐藏的元素，需要上下滑动来查看，可以重点参考QwenVL提取的界面文本信息

**隐私保护检测：**
在分析界面时，请同时检测是否存在需要隐私保护的敏感信息：

1. **手机号码检测规则：**
   - 识别11位中国大陆手机号（1开头）
   - 重点关注EditText输入框、TextView显示文本等元素

2. **隐私检测输出：**
   - 如果检测到手机号，在返回结果中包含privacy_detection字段
   - 只需提供手机号码原始文本和bounds位置信息
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
                "bounds": "元素的bounds属性值"
            }}
        ]
    }},
    "plan": {{
        "description": "操作描述",
        "type": "操作类型",
        "position": [x, y],
        "box": [[x1, y1], [x2, y2]],
        "text": "输入文本（如需要）",
        "app": "应用名称（如需要）",
        "package": "应用包名（如需要）",
        "start_position": [x, y],
        "stop_position": [x, y],
        "duration": 0.5
    }}
}}"""
    
    def get_analysis_prompt(self, query: str, xml_content: str, current_step: int, history_steps: list = None) -> str:
        """获取分析用的用户提示词"""
        
        # 构建历史步骤信息
        history_text = ""
        if history_steps and len(history_steps) > 0:
            history_text = "\n=== 执行历史 ===\n"
            for i, step_info in enumerate(history_steps, 1):
                step_desc = step_info.get('description', '未知操作')
                step_type = step_info.get('type', '未知类型')
                step_obs = step_info.get('observation', '')
                history_text += f"步骤{i}: 手机界面状态为：{step_obs}；执行了: {step_desc} ;类型: {step_type})\n"
            history_text += "\n根据以上执行历史，请分析当前界面状态并决定下一步操作。如果上一步执行完任务了，请判断了任务完成。\n"
        
        return f"""
当前任务: {query}
当前步骤: {current_step}
{history_text}
XML界面结构信息:
{xml_content}

请以上信息并告诉我下一步应该如何操作。请只返回一个JSON格式的响应，不要包含其他文本。"""

# 创建全局配置实例
config = Config() 