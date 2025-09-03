# auto-phone/src/prompt_engineering/context_expansion.py
"""
Context Expansion Implementation for UI Automation
基于02_expand_context.py的思想，实现上下文分层扩展

这个文件实现了一个分层的提示词构建系统，核心思想是：
1. 将复杂的AI提示词拆分成多个独立的"层"(Layer)
2. 每个层负责特定的功能（如角色定义、操作规则等）
3. 按优先级组合所有层，生成最终的完整提示词

📚 关键概念：
- ContextLayer: 基础层类，所有具体层都继承自它
- ExpandablePromptBuilder: 提示词构建器，负责组合所有层
- Priority: 优先级，数字越小越靠前（越重要）

🔧 常见操作：
- 修改现有规则：找到对应的Layer类，修改其build()方法
- 添加新规则：创建新的Layer类，在Builder中注册
- 调试问题：单独测试某个Layer的输出

📖 详细文档：请参考同目录下的 README_交接文档.md
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import time
from dataclasses import dataclass, field
from ..logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class ContextMetrics:
    """上下文度量指标"""
    prompt_tokens: int = 0
    response_tokens: int = 0
    token_efficiency: float = 0.0
    latency: float = 0.0
    complexity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "response_tokens": self.response_tokens,
            "token_efficiency": self.token_efficiency,
            "latency": self.latency,
            "complexity_score": self.complexity_score
        }


class ContextLayer:
    """
    上下文层基类 - 所有具体层的父类
    
    🎯 作用：定义层的基本结构和接口
    - 每个层都有名称(name)和优先级(priority) 
    - priority越小越重要，会排在提示词前面
    - enabled控制该层是否生效
    - token_count记录该层的token消耗
    
    🔧 使用方法：
    1. 继承这个类创建具体的层
    2. 实现build()方法，返回该层的提示词内容
    3. 在ExpandablePromptBuilder中注册使用
    """
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name          # 层的名称，用于标识和调试
        self.priority = priority  # 优先级：1最重要，数字越大越靠后
        self.enabled = True       # 是否启用该层（可用于调试时临时禁用）
        self.token_count = 0      # 该层消耗的token数量（用于性能监控）
        
    def build(self, **kwargs) -> str:
        """
        构建该层的提示词内容 - 子类必须实现
        
        Args:
            **kwargs: 动态参数，不同层需要的参数不同
            
        Returns:
            str: 该层的提示词文本
            
        🔧 实现要点：
        - 返回清晰、结构化的提示词文本
        - 使用self.estimate_tokens()计算并设置token_count
        - 内容要与该层的职责相符
        """
        raise NotImplementedError
        
    def estimate_tokens(self, content: str) -> int:
        """估算token数量（简单估算）"""
        # 粗略估算：中文约1.5字符/token，英文约4字符/token
        chinese_chars = len([c for c in content if ord(c) > 127])
        english_chars = len(content) - chinese_chars
        return int(chinese_chars / 1.5 + english_chars / 4)


class BasePromptLayer(ContextLayer):
    """基础提示词层 - 最小化的核心指令"""
    
    def __init__(self):
        super().__init__("base_prompt", priority=1)
        
    def build(self, task: str) -> str:
        """构建基础提示词"""
        content = f"分析手机界面并执行任务：{task}"
        self.token_count = self.estimate_tokens(content)
        return content


class RoleDefinitionLayer(ContextLayer):
    """角色定义层 - 定义AI的角色和能力"""
    
    def __init__(self):
        super().__init__("role_definition", priority=2)
        
    def build(self) -> str:
        """构建角色定义"""
        content = """你是一个专业的手机UI自动化助手。请根据XML界面结构信息和用户的操作指令，提供精确的操作信息。"""
        self.token_count = self.estimate_tokens(content)
        return content


class OutputFormatLayer(ContextLayer):
    """输出格式层 - 定义期望的输出格式"""
    
    def __init__(self):
        super().__init__("output_format", priority=10)  # 放在最后，紧挨着XML
        
    def build(self) -> str:
        """构建输出格式说明"""
        content = """请用JSON格式返回结果，格式如下：
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
        self.token_count = self.estimate_tokens(content)
        return content


class OperationRulesLayer(ContextLayer):
    """操作规则层 - 详细的操作规范"""
    
    def __init__(self):
        super().__init__("operation_rules", priority=3)
        
    def build(self, include_examples: bool = True) -> str:
        """构建操作规则"""
        rules = """操作类型说明：
- Open: 打开应用（需要app和package字段，不需要position和box）
  * 当需要启动/打开手机应用时，优先使用Open操作
  * 适用于从桌面、应用列表等场景打开应用
  * 通过应用包名直接启动，更可靠更快速
- Tap: 点击操作（需要position、box、times字段）
  * 用于点击界面元素，如按钮、链接、菜单项等
  * 不适用于打开应用，应优先使用Open操作
- Typing: 输入文本（需要position、box、text字段）
- Swipe: 滑动操作（需要start_position、stop_position、bbox、duration字段）
- End: 任务完成"""
        
        if include_examples:
            rules += """

plan字段描述规范：
* 桌面打开app："打开[app名称]"（如："打开淘宝"）- 使用Open操作而非Tap
* 搜索框操作："点击搜索框"
* 搜索按钮操作："点击搜索按钮"
* 滑动操作："向上滑动"、"向下滑动"、"向左滑动"、"向右滑动"、"向左滑动频道栏"、"向右滑动频道栏"
* 其他操作：简洁明了的中文描述"""
        
        self.token_count = self.estimate_tokens(rules)
        return rules


class ContextualInfoLayer(ContextLayer):
    """上下文信息层 - 当前状态信息"""
    
    def __init__(self):
        super().__init__("contextual_info", priority=5)
        
    def build(self, current_step: int, task_progress: str = None) -> str:
        """构建上下文信息"""
        content = f"\n=== 当前状态 ===\n当前步骤：第 {current_step} 步"
        
        if task_progress:
            content += f"\n任务进度：{task_progress}"
            
        self.token_count = self.estimate_tokens(content)
        return content


class HistoryLayer(ContextLayer):
    """历史记录层 - 执行历史"""
    
    def __init__(self):
        super().__init__("history", priority=6)
        
    def build(self, history_steps: List[Dict[str, Any]], max_steps: int = 5) -> str:
        """构建历史记录"""
        if not history_steps:
            return ""
            
        # 只保留最近的步骤
        recent_steps = history_steps[-max_steps:] if len(history_steps) > max_steps else history_steps
        
        content = "\n=== 执行历史 ===\n"
        for step in recent_steps:
            step_num = step.get('step', '')
            desc = step.get('description', '')
            obs = step.get('observation', '')
            content += f"步骤{step_num}: {obs} → {desc}\n"
            
        self.token_count = self.estimate_tokens(content)
        return content


class DomainKnowledgeLayer(ContextLayer):
    """领域知识层 - 特定应用的知识"""
    
    def __init__(self):
        super().__init__("domain_knowledge", priority=7)
        
    def build(self, app_name: str = None, task_type: str = None) -> str:
        """构建领域知识"""
        if not app_name and not task_type:
            return ""
            
        content = "\n=== 领域知识 ===\n"
        
        # 根据应用添加特定知识
        if app_name == "美团外卖":
            content += "美团外卖操作要点：先选择外卖/到店，再选择商品，最后确认订单\n"
        elif app_name == "支付宝":
            content += "支付宝操作要点：注意隐私信息保护，避免泄露敏感数据\n"
            
        self.token_count = self.estimate_tokens(content)
        return content


class ScreenContentLayer(ContextLayer):
    """屏幕内容层 - XML和视觉信息"""
    
    def __init__(self):
        super().__init__("screen_content", priority=11)  # 最后添加，通常最大
        
    def build(self, xml_content: str, visual_description: str = None) -> str:
        """构建屏幕内容"""
        content = "\n=== 当前屏幕 ===\n"
        
        if visual_description:
            content += f"视觉描述：{visual_description}\n\n"
            
        content += f"XML结构：\n{xml_content}"
        
        self.token_count = self.estimate_tokens(content)
        return content


class ObservationRulesLayer(ContextLayer):
    """观察规则层 - observation字段的格式规范"""
    
    def __init__(self):
        super().__init__("observation_rules", priority=4)
        
    def build(self) -> str:
        """构建observation字段规范"""
        content = """1. observation: 描述当前界面状态，必须按照以下格式规范：

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
3. completion_reason: 如果任务完成，说明完成的原因（中文）"""
        self.token_count = self.estimate_tokens(content)
        return content


class TaskCompletionRulesLayer(ContextLayer):
    """任务完成规则层 - 任务完成判断标准"""
    
    def __init__(self):
        super().__init__("task_completion_rules", priority=5)
        
    def build(self) -> str:
        """构建任务完成判断标准"""
        content = """**任务完成判断标准：**
- **打开应用：** 应用启动并显示主界面时完成
- **导航类：** 到达目标页面/功能时完成
- **搜索类：** 搜索结果显示时完成
- **组合任务：** 所有子任务都完成时才算完成
- 完成任务之后避免多余操作，如滑动等

**任务完成判断示例：**
- 任务要求打开美团外卖的"看病买药"功能，当成功跳转到相关页面后，即使页面XML中不包含"看病买药"字样，也应判断为任务完成
- 任务要求打开美团外卖的"客服中心"，当成功跳转到相关页面后，即使页面XML中不包含"客服中心"字样，也应判断为任务完成
- 判断任务完成应基于页面功能和上下文，而非仅依赖特定文本的出现"""
        self.token_count = self.estimate_tokens(content)
        return content


class SwipeRulesLayer(ContextLayer):
    """滑动规则层 - 滑动操作的详细指导"""
    
    def __init__(self):
        super().__init__("swipe_rules", priority=6)
        
    def build(self) -> str:
        """构建滑动操作规则"""
        content = """**滑动操作判断指导：**
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
6. **设置滑动区域bbox**：完整的区域边界框

**示例计算：**
- 如果频道栏bounds="[9,204][977,313]"
- Y中心 = (204 + 313) / 2 = 258
- start_position = [643, 258]  （493+150）
- stop_position = [343, 258]   （493-150）
- bbox = [[9, 204], [977, 313]]

**滑动操作格式：**
- type: "Swipe"
- start_position: [起始x, 中心y] (在滑动区域内，偏右位置)
- stop_position: [结束x, 中心y] (在滑动区域内，偏左位置)
- bbox: [[x1, y1], [x2, y2]] (滑动区域的完整边界框)
- duration: 0.5 (滑动持续时间)"""
        self.token_count = self.estimate_tokens(content)
        return content


class PrivacyProtectionLayer(ContextLayer):
    """隐私保护层 - 隐私信息检测规则"""
    
    def __init__(self):
        super().__init__("privacy_protection", priority=7)
        
    def build(self) -> str:
        """构建隐私保护规则"""
        content = """**隐私保护检测：**
在分析界面时，请同时检测是否存在需要隐私保护的敏感信息：

1. **手机号码检测规则：**
   - 识别11位中国大陆手机号（1开头）
   - 重点关注EditText输入框、TextView显示文本等元素

2. **隐私检测输出：**
   - 如果检测到手机号，在返回结果中包含privacy_detection字段
   - 只需提供手机号码原始文本和bounds位置信息
   - 如果没有检测到敏感信息，不输出privacy_detection字段"""
        self.token_count = self.estimate_tokens(content)
        return content


class RepeatDetectionLayer(ContextLayer):
    """重复操作检测层 - 避免无限循环"""
    
    def __init__(self):
        super().__init__("repeat_detection", priority=8)
        
    def build(self) -> str:
        """构建重复操作检测规则"""
        content = """**重复操作检测规则：**
如果在执行历史中发现以下情况，必须立即停止操作：

1. **检测条件：**
   - 最近3步历史中出现相同的操作类型（type字段相同）
   - 操作描述（description字段）完全相同
   - 操作位置（position字段）相同或非常接近
   - 操作区域（bbox字段）相同或非常接近
   - 页面观察（observation字段）基本无变化（关键词大致相同）

2. **停止操作：**
   - 将type设置为"End"
   - description设置为"检测到重复操作，停止执行避免循环"
   - is_task_completed设置为false
   - completion_reason设置为"重复操作，终止执行"

3. **判断示例：**
   - 连续3次"点击搜索框"且页面描述都是"当前是淘宝首页，顶部有搜索框"
   - 连续3次"向下滑动"且页面描述都是"当前是商品列表页面"
   - 连续3次相同位置的点击操作且观察结果无明显变化

**⚠️ 重要：不要进行复杂的相似度计算，直接比较关键字段是否重复即可。**"""
        self.token_count = self.estimate_tokens(content)
        return content


class ImportantTipsLayer(ContextLayer):
    """重要提示层 - 关键操作提示"""
    
    def __init__(self):
        super().__init__("important_tips", priority=9)
        
    def build(self, app_packages: dict = None) -> str:
        """构建重要提示"""
        app_packages_text = ""
        if app_packages:
            app_packages_text = "\n".join([f"- {app}: {pkg}" for app, pkg in app_packages.items()])
        
        content = f"""**应用包名列表：**
{app_packages_text}

**重要提示：**
- 打开应用优先使用Open操作（通过包名启动）
- 点击功能按钮后页面跳转成功即完成任务
- 如果任务已完成，将type设置为"End"，description设置为"任务已完成"
- 在订票等任务中，一般出发地为页面左边，目的地为页面右边，在选择出发地和目的地的搜索栏中，搜索栏中的提示文本可能都是"请输入目的城市/车站名"，这个不能作为判断当前是在选择出发地还是目的地的依据

**文本输入：**
- 如果任务要求输入文本，需要先点击输入框，再输入文本
- 如果页面中没有com.github.uiautomator的元素，说明当前页面并不可输入文字，需要先点击输入框，再输入文本"""
        self.token_count = self.estimate_tokens(content)
        return content


class ExpandablePromptBuilder:
    """
    可扩展的提示词构建器 - 系统的核心组件
    
    🎯 作用：将多个ContextLayer组合成完整的AI提示词
    📝 新手指南：
    - 这是使用该系统的主要入口点
    - 自动管理所有层的优先级和组合
    - 提供性能监控和调试功能
    
    🔧 主要功能：
    1. 层管理：添加、删除、启用/禁用层
    2. 提示词构建：按优先级组合所有层
    3. 性能监控：Token使用量、构建时间等
    4. 调试支持：单独测试某个层
    
    💡 使用示例：
    ```python
    builder = ExpandablePromptBuilder(max_tokens=4000)
    prompt, metrics = builder.build(
        task="执行任务：打开淘宝搜索手机",
        current_step=1,
        app_name="淘宝"
    )
    ```
    """
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens      # Token限制，防止提示词过长
        self.layers: List[ContextLayer] = []  # 所有层的列表
        self.metrics = ContextMetrics()   # 性能指标记录
        self._initialize_default_layers() # 初始化所有默认层
        
    def _initialize_default_layers(self):
        """初始化默认层"""
        self.add_layer(BasePromptLayer())
        self.add_layer(RoleDefinitionLayer())
        self.add_layer(ObservationRulesLayer())
        self.add_layer(OutputFormatLayer())
        self.add_layer(OperationRulesLayer())
        self.add_layer(TaskCompletionRulesLayer())
        self.add_layer(SwipeRulesLayer())
        self.add_layer(PrivacyProtectionLayer())
        self.add_layer(RepeatDetectionLayer())
        self.add_layer(ImportantTipsLayer())
        self.add_layer(ContextualInfoLayer())
        self.add_layer(HistoryLayer())
        self.add_layer(DomainKnowledgeLayer())
        self.add_layer(ScreenContentLayer())
        
    def add_layer(self, layer: ContextLayer):
        """添加上下文层"""
        self.layers.append(layer)
        # 按优先级排序
        self.layers.sort(key=lambda x: x.priority)
        logger.debug(f"添加上下文层: {layer.name}")
        
    def remove_layer(self, layer_name: str):
        """移除上下文层"""
        self.layers = [l for l in self.layers if l.name != layer_name]
        logger.debug(f"移除上下文层: {layer_name}")
        
    def enable_layer(self, layer_name: str, enabled: bool = True):
        """启用/禁用特定层"""
        for layer in self.layers:
            if layer.name == layer_name:
                layer.enabled = enabled
                logger.debug(f"{'启用' if enabled else '禁用'}上下文层: {layer_name}")
                break
                
    def build(self, **kwargs) -> Tuple[str, ContextMetrics]:
        """
        构建完整的AI提示词 - 系统的核心方法
        
        🎯 作用：按优先级组合所有启用的层，生成最终提示词
        📝 工作流程：
        1. 遍历所有启用的层（按priority排序）
        2. 调用每个层的build()方法获取内容
        3. 组合所有内容成为完整提示词
        4. 统计性能指标并返回
        
        Args:
            **kwargs: 动态参数，会传递给需要的层
            常用参数：
            - task: 任务描述
            - current_step: 当前步骤号
            - history_steps: 历史步骤列表
            - app_name: 应用名称
            - app_packages: 应用包名映射
            - include_examples: 是否包含示例
            
        Returns:
            Tuple[str, ContextMetrics]: (完整提示词, 性能指标)
            
        🔧 使用示例：
        ```python
        prompt, metrics = builder.build(
            task="执行任务：打开淘宝",
            current_step=1,
            app_name="淘宝"
        )
        print(f"提示词长度: {len(prompt)}")
        print(f"Token使用: {metrics.total_tokens}")
        ```
        """
        start_time = time.time()
        prompt_parts = []
        total_tokens = 0
        
        # 按优先级构建各层
        for layer in self.layers:
            if not layer.enabled:
                continue
                
            try:
                # 构建该层内容
                if layer.name == "base_prompt":
                    content = layer.build(task=kwargs.get('task', ''))
                elif layer.name == "role_definition":
                    content = layer.build()
                elif layer.name == "observation_rules":
                    content = layer.build()
                elif layer.name == "output_format":
                    content = layer.build()
                elif layer.name == "operation_rules":
                    content = layer.build(include_examples=kwargs.get('include_examples', True))
                elif layer.name == "task_completion_rules":
                    content = layer.build()
                elif layer.name == "swipe_rules":
                    content = layer.build()
                elif layer.name == "privacy_protection":
                    content = layer.build()
                elif layer.name == "repeat_detection":
                    content = layer.build()
                elif layer.name == "important_tips":
                    content = layer.build(app_packages=kwargs.get('app_packages'))
                elif layer.name == "contextual_info":
                    content = layer.build(
                        current_step=kwargs.get('current_step', 1),
                        task_progress=kwargs.get('task_progress')
                    )
                elif layer.name == "history":
                    content = layer.build(
                        history_steps=kwargs.get('history_steps', []),
                        max_steps=kwargs.get('max_history_steps', 5)
                    )
                elif layer.name == "domain_knowledge":
                    content = layer.build(
                        app_name=kwargs.get('app_name'),
                        task_type=kwargs.get('task_type')
                    )
                elif layer.name == "screen_content":
                    content = layer.build(
                        xml_content=kwargs.get('xml_content', ''),
                        visual_description=kwargs.get('visual_description')
                    )
                else:
                    content = layer.build(**kwargs)
                    
                if content:
                    # 检查是否超过token限制
                    if total_tokens + layer.token_count > self.max_tokens:
                        logger.warning(f"达到token限制，跳过层: {layer.name}")
                        break
                        
                    prompt_parts.append(content)
                    total_tokens += layer.token_count
                    
            except Exception as e:
                logger.error(f"构建层 {layer.name} 时出错: {e}")
                
        # 组装最终提示词
        final_prompt = "\n\n".join(prompt_parts)
        
        # 更新度量指标
        self.metrics.prompt_tokens = total_tokens
        self.metrics.latency = time.time() - start_time
        self.metrics.complexity_score = len([l for l in self.layers if l.enabled]) / len(self.layers)
        
        logger.info(f"构建提示词完成: {total_tokens} tokens, {len(prompt_parts)} 层")
        
        return final_prompt, self.metrics
        
    def analyze_token_distribution(self) -> Dict[str, int]:
        """分析各层的token分布"""
        distribution = {}
        for layer in self.layers:
            if layer.enabled and layer.token_count > 0:
                distribution[layer.name] = layer.token_count
        return distribution


# 便捷函数
def create_minimal_prompt(task: str, xml_content: str) -> str:
    """创建最小化提示词"""
    builder = ExpandablePromptBuilder()
    # 只启用必要的层
    for layer_name in ["role_definition", "operation_rules", "contextual_info", 
                      "domain_knowledge", "history"]:
        builder.enable_layer(layer_name, False)
        
    prompt, _ = builder.build(task=task, xml_content=xml_content)
    return prompt


def create_full_prompt(**kwargs) -> Tuple[str, ContextMetrics]:
    """创建完整提示词"""
    builder = ExpandablePromptBuilder()
    return builder.build(**kwargs)


# 预设配置
class PromptPresets:
    """预设的提示词配置"""
    
    @staticmethod
    def simple_task():
        """简单任务配置"""
        builder = ExpandablePromptBuilder()
        builder.enable_layer("domain_knowledge", False)
        builder.enable_layer("history", False)
        return builder
        
    @staticmethod
    def complex_task():
        """复杂任务配置"""
        builder = ExpandablePromptBuilder()
        # 所有层都启用
        return builder
        
    @staticmethod
    def error_recovery():
        """错误恢复配置"""
        builder = ExpandablePromptBuilder()
        # 强调历史和规则
        builder.layers[5].priority = 3  # 提高历史层优先级
        return builder