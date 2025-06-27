#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

import os
from typing import Dict, Any

class Config:
    """配置管理类"""
    
    def __init__(self):
        # AI模型配置
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY')
        self.model_name = 'deepseek-r1'
        
        # 大模型参数配置（用于稳定输出）
        self.model_params = {
            'temperature': 0.1,        # 降低随机性，0.0-2.0，越低越稳定
            'top_p': 0.8,             # 核采样参数，0.0-1.0，降低采样范围
            'top_k': 50,              # 限制候选词数量，减少意外输出
            'seed': 42,               # 固定种子，增强可重复性
            # 'max_tokens': 1000,       # 限制输出长度，避免过长响应
            'repetition_penalty': 1.1, # 重复惩罚，1.0-2.0，减少重复内容
            'stop': ["```", "---", "===", "\n\n\n"]  # 停止标记，避免多余输出
        }
        
        # 设备配置
        self.device_id = "AQQRVB1629003418"  # 可以通过环境变量覆盖
        if os.getenv('DEVICE_ID'):
            self.device_id = os.getenv('DEVICE_ID')
        
        # 任务配置
        self.max_steps = 10
        
        # 界面配置
        self.default_screen_resolution = [1080, 2400]
        self.default_phone_model = "Redmi K50"
        self.default_os = "Xiaomi HyperOS"
    
    def validate(self) -> bool:
        """验证配置是否正确"""
        valid = True
        
        if not self.dashscope_api_key:
            print("❌ 错误: 未设置 DASHSCOPE_API_KEY 环境变量")
            print("   请设置: set DASHSCOPE_API_KEY=your_api_key")
            valid = False
        
        if not self.device_id:
            print("❌ 错误: 未设置设备ID")
            valid = False
            
        return valid
    
    def print_model_config(self):
        """打印当前模型配置参数"""
        print(f"\n🤖 大模型配置:")
        print(f"   模型名称: {self.model_name}")
        print(f"   参数配置:")
        for key, value in self.model_params.items():
            print(f"     {key}: {value}")
        print()
    
    def update_model_param(self, param_name: str, value):
        """更新单个模型参数"""
        if param_name in self.model_params:
            old_value = self.model_params[param_name]
            self.model_params[param_name] = value
            print(f"✅ 参数 {param_name} 已更新: {old_value} -> {value}")
        else:
            print(f"❌ 未知参数: {param_name}")
            print(f"   可用参数: {list(self.model_params.keys())}")
    
    def set_conservative_mode(self):
        """设置保守模式（更稳定的输出）"""
        self.model_params.update({
            'temperature': 0.05,
            'top_p': 0.7,
            'top_k': 30,
            'repetition_penalty': 1.2
        })
        print("🛡️  已切换到保守模式（更稳定的输出）")
    
    def set_balanced_mode(self):
        """设置平衡模式（默认设置）"""
        self.model_params.update({
            'temperature': 0.1,
            'top_p': 0.8,
            'top_k': 50,
            'repetition_penalty': 1.1
        })
        print("⚖️  已切换到平衡模式（默认设置）")
    
    def set_creative_mode(self):
        """设置创新模式（更多样化的输出）"""
        self.model_params.update({
            'temperature': 0.3,
            'top_p': 0.9,
            'top_k': 100,
            'repetition_penalty': 1.0
        })
        print("🎨 已切换到创新模式（更多样化的输出）")
    
    def get_task_template(self, query: str, episode_id: str = "task") -> Dict[str, Any]:
        """获取任务数据模板"""
        return {
            "phone": self.default_phone_model,
            "os": self.default_os,
            "screen_resolution": self.default_screen_resolution,
            "query": query,
            "episode_id": episode_id,
            "data": []
        }
    
    def get_ai_system_prompt(self) -> str:
        """获取AI系统提示词"""
        return """你是一个专业的手机UI自动化助手。请根据XML界面结构信息和用户的操作指令，提供精确的操作信息：

1. observation: 描述当前界面状态，必须按照以下格式规范：

   **桌面场景（打开app）：**
   格式："当前是手机/平板桌面，包含/有[app1]、[app2]、[app3]等app"
   要求：至少包含两个app名称，其中一个是需要打开的目标app
   示例："当前是手机桌面，有淘宝、京东、百度等app"

   **搜索框场景：**
   格式："当前是[页面名称]，底部导航栏有[功能1]、[功能2]等功能/按钮、顶部有搜索框，点击搜索框可以进行相关搜索"
   示例："当前是淘宝首页，底部导航栏有我的、购物车、首页等功能、顶部有搜索框，点击搜索框可以进行相关搜索"

   **搜索按钮场景：**
   格式："当前是[页面名称]，底部导航栏有[功能1]、[功能2]等功能/按钮、右上角有搜索按钮，点击搜索按钮可以进行搜索"
   示例："当前为微信主页面，下方有通讯录、发现等页面按钮，右上角有搜索按钮可以搜索内容"

   **其他场景：**
   简洁描述当前界面状态和主要元素（15-25字）

2. is_task_completed: 布尔值，判断用户的任务是否已经完成（重要！）
3. completion_reason: 如果任务完成，说明完成的原因（中文）
4. plan: 分析下一步应该执行的操作，包括：
   - description: 操作描述，必须按照以下格式规范：
     * 桌面打开app："打开[app名称]"（如："打开淘宝"）
     * 搜索框操作："点击搜索框"
     * 搜索按钮操作："点击搜索按钮"
     * 其他操作：简洁明了的中文描述
   - type: 操作类型（Open/Tap/Typing/End等）
   - position: 点击位置坐标（仅在Tap/Typing操作时需要，Open操作不需要）
   - box: 元素边界框（仅在Tap/Typing操作时需要，Open操作不需要）
   - times: 点击次数（默认为1，仅在Tap操作时需要）
   - text: 输入文本（仅在Typing操作时需要）
   - app: 应用名称（仅在Open操作时需要）
   - package: 应用包名（仅在Open操作时需要，用于直接启动应用）

操作类型说明：
- Open: 打开应用（需要app和package字段，不需要position和box）
- Tap: 点击操作（需要position、box、times字段）
- Typing: 输入文本（需要position、box、text字段）
- End: 任务完成

**常见应用包名参考：**
- 京东: com.jingdong.app.mall
- 淘宝: com.taobao.taobao
- 微信: com.tencent.mm
- 支付宝: com.eg.android.AlipayGphone
- 网易云音乐: com.netease.cloudmusic
- QQ: com.tencent.mobileqq
- 抖音: com.ss.android.ugc.aweme
- 百度: com.baidu.searchbox
- 美团: com.sankuai.meituan
- 饿了么: me.ele.app
- 滴滴出行: com.sdu.didi.psnger
- 高德地图: com.autonavi.minimap
- 知乎: com.zhihu.android
- 哔哩哔哩: tv.danmaku.bili
- 小红书: com.xingin.xhs

任务完成判断标准：
- 如果用户要求"打开某个应用"，当该应用的主界面显示时，任务完成
- 如果用户要求"查找某个内容"，当搜索结果或相关页面显示时，任务完成
- 如果用户要求"进入某个页面"，当目标页面显示时，任务完成
- 如果当前界面已经满足用户的最终目标，任务完成

重要提示：
- 严格按照上述observation和description格式规范生成内容
- Open操作时：优先使用package包名启动，不需要position和box坐标
- Tap/Typing操作时：完全基于XML信息计算精确坐标
- 从XML的bounds属性（格式：[x1,y1][x2,y2]）中计算中心点坐标
- position坐标 = [(x1+x2)/2, (y1+y2)/2]
- 优先选择clickable="true"的元素
- 如果任务已完成，将type设置为"End"，description设置为"任务已完成"

请用JSON格式返回结果。"""

# 全局配置实例
config = Config() 