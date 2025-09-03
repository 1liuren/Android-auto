# Context Expansion 提示词工程系统 - 交接文档

## 📋 概述

这是一个基于**分层架构**的提示词工程系统，采用**Context Expansion（上下文扩展）**方法，将复杂的AI提示词分解为多个独立的、可管理的层次。每个层次负责特定的功能，便于维护和调试。

## 📁 文件结构

```
prompt_engineering/
├── __init__.py              # 模块导出接口
├── context_expansion.py     # 核心实现文件（重点）
└── README_交接文档.md       # 本文档
```

## 🎯 核心设计理念

### 为什么使用Context Expansion？

**原始问题：**
- 单一巨型提示词（Monolithic Prompt）难以维护
- 修改一个规则可能影响整个提示词
- 调试困难，无法定位具体问题
- 新增功能需要大幅修改现有代码

**Context Expansion解决方案：**
- ✅ **分层管理**：每个功能独立成层
- ✅ **优先级控制**：重要信息优先展示给AI
- ✅ **动态组合**：根据需要启用/禁用特定层
- ✅ **易于扩展**：新增功能只需添加新层

## 🏗️ 系统架构

### 1. 核心组件

#### `ContextLayer` (基础层类)
```python
class ContextLayer:
    def __init__(self, name: str, priority: int):
        self.name = name           # 层名称
        self.priority = priority   # 优先级（数字越小越优先）
        self.enabled = True        # 是否启用
        self.token_count = 0       # Token消耗统计
    
    def build(self, **kwargs) -> str:
        # 子类必须实现此方法，生成该层的提示词内容
        raise NotImplementedError
```

#### `ExpandablePromptBuilder` (提示词构建器)
```python
class ExpandablePromptBuilder:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens    # 最大Token限制
        self.layers = []                # 层列表
        
    def build(self, **kwargs) -> Tuple[str, ContextMetrics]:
        # 按优先级构建完整提示词
        # 返回：(提示词字符串, 性能指标)
```

### 2. 现有的层次结构

| 优先级 | 层名称 | 功能描述 | 何时修改 |
|--------|--------|----------|----------|
| 1 | `BasePromptLayer` | 基础任务描述 | 任务类型变更 |
| 2 | `RoleDefinitionLayer` | AI角色定义 | 角色能力调整 |
| 3 | `ObservationRulesLayer` | 界面观察规范 | 观察格式变更 |
| 4 | `OutputFormatLayer` | JSON输出格式 | 输出字段变更 |
| 5 | `OperationRulesLayer` | 操作类型规范 | 新增操作类型 |
| 6 | `TaskCompletionRulesLayer` | 任务完成判断 | 完成条件变更 |
| 7 | `SwipeRulesLayer` | 滑动操作指导 | 滑动逻辑优化 |
| 8 | `PrivacyProtectionLayer` | 隐私保护规则 | 隐私检测调整 |
| 9 | `RepeatDetectionLayer` | 重复操作检测 | 防死循环逻辑 |
| 10 | `ImportantTipsLayer` | 重要提示信息 | 应用包名更新 |
| 11 | `ContextualInfoLayer` | 上下文信息 | 步骤信息格式 |
| 12 | `HistoryLayer` | 历史步骤 | 历史格式调整 |
| 13 | `DomainKnowledgeLayer` | 领域知识 | 业务规则变更 |
| 14 | `ScreenContentLayer` | 屏幕内容 | XML格式变更 |

## 🚀 快速上手指南

### 步骤1：了解现有用法

在 `ai_analyzer.py` 中的使用示例：

```python
from .prompt_engineering import ExpandablePromptBuilder

class AIAnalyzer:
    def __init__(self):
        # 初始化提示词构建器，最大4000 tokens
        self.prompt_builder = ExpandablePromptBuilder(max_tokens=4000)
    
    def analyze_screen(self, query: str, current_step: int, **kwargs):
        # 构建完整提示词
        full_prompt, metrics = self.prompt_builder.build(
            task=f"执行任务：{query}",
            current_step=current_step,
            history_steps=kwargs.get('history_steps', []),
            app_name=self._extract_app_name_from_query(query),
            app_packages=config.app_packages,
            include_examples=True
        )
        
        # 使用 full_prompt 调用AI模型...
```

### 步骤2：常见维护任务

#### 🔧 任务1：修改JSON输出格式

**场景：** 需要在AI输出中新增一个字段

**操作步骤：**

1. 找到 `OutputFormatLayer` 类（约第85行）
2. 修改 `build()` 方法中的JSON示例：

```python
def build(self) -> str:
    content = """请用JSON格式返回结果，格式如下：
{
    "observation": "界面状态描述",
    "is_task_completed": true/false,
    "completion_reason": "完成原因（如果已完成）",
    "新字段名": "新字段描述",  # ← 在这里添加
    "plan": { ... }
}"""
    return content
```

#### 🔧 任务2：添加新的操作类型

**场景：** 需要支持新的手机操作（如长按、双击等）

**操作步骤：**

1. 找到 `OperationRulesLayer` 类（约第123行）
2. 在 `build()` 方法中添加新操作说明：

```python
def build(self, include_examples: bool = True) -> str:
    content = """
4. plan: 分析下一步应该执行的操作，包括：
   - type: 操作类型（Open/Tap/Typing/Swipe/LongPress/DoubleClick/End等）  # ← 添加新类型
   
操作类型说明：
- LongPress: 长按操作（需要position、box、duration字段）  # ← 添加说明
- DoubleClick: 双击操作（需要position、box字段）
"""
    return content
```

#### 🔧 任务3：新增一个全新的层

**场景：** 需要添加特定领域的规则（如游戏操作、视频播放等）

**操作步骤：**

1. 在 `context_expansion.py` 中创建新类：

```python
class GameControlLayer(ContextLayer):
    """游戏控制层 - 游戏特定操作规则"""
    
    def __init__(self):
        super().__init__("game_control", priority=8)  # 选择合适的优先级
        
    def build(self, game_type: str = None) -> str:
        """构建游戏控制规则"""
        content = f"""
**游戏操作规则：**
1. 检测到游戏界面时，优先使用游戏手势
2. 支持的游戏类型：{game_type or '通用'}
3. 游戏中的暂停、开始等操作...
"""
        self.token_count = self.estimate_tokens(content)
        return content
```

2. 在 `ExpandablePromptBuilder._initialize_default_layers()` 中注册：

```python
def _initialize_default_layers(self):
    # ... 现有层 ...
    self.layers.append(GameControlLayer())  # ← 添加新层
    # 按优先级排序
    self.layers.sort(key=lambda x: x.priority)
```

3. 在 `build()` 方法中添加调用逻辑：

```python
elif layer.name == "game_control":
    content = layer.build(game_type=kwargs.get('game_type'))
```

4. 在 `__init__.py` 中导出：

```python
from .context_expansion import (
    # ... 现有导出 ...
    GameControlLayer,  # ← 添加导出
)

__all__ = [
    # ... 现有列表 ...
    'GameControlLayer',  # ← 添加到列表
]
```

### 步骤3：调试和优化

#### 🐛 调试技巧

1. **启用/禁用特定层：**

```python
# 临时禁用某个层进行测试
builder.enable_layer("swipe_rules", False)

# 构建提示词
prompt, metrics = builder.build(...)

# 查看性能指标
print(f"总Token数：{metrics.total_tokens}")
print(f"构建时间：{metrics.build_time}秒")
print(f"活跃层数：{metrics.active_layers}")
```

2. **查看具体层的输出：**

```python
# 单独测试某个层
layer = SwipeRulesLayer()
content = layer.build()
print(f"滑动规则层内容：\n{content}")
print(f"Token消耗：{layer.token_count}")
```

#### ⚡ 性能优化

1. **Token控制：**
   - 监控 `ContextMetrics.total_tokens`
   - 当接近限制时，考虑禁用次要层

2. **优先级调整：**
   - 重要信息优先级设为1-5
   - 辅助信息优先级设为6-10
   - 上下文信息优先级设为11+

## 🚨 常见问题与解决方案

### Q1: AI输出格式错误

**问题：** AI返回的JSON格式不符合预期

**解决：**
1. 检查 `OutputFormatLayer` 中的JSON示例是否正确
2. 确认示例中的字段名和类型是否匹配代码期望
3. 考虑在示例中添加更多具体的值示例

### Q2: 提示词过长导致AI响应差

**问题：** Token超出限制，AI理解困难

**解决：**
1. 临时禁用非核心层：`builder.enable_layer("layer_name", False)`
2. 调整层的优先级，确保重要信息在前
3. 简化某些层的内容，去除冗余描述

### Q3: 新增层不生效

**问题：** 添加了新层但AI没有遵循新规则

**解决：**
1. 确认新层已在 `_initialize_default_layers()` 中注册
2. 检查 `build()` 方法中是否添加了对应的调用分支
3. 验证新层的 `priority` 设置是否合理
4. 测试新层单独的输出内容是否正确

### Q4: 某些历史功能失效

**问题：** 修改后原本工作的功能不再正常

**解决：**
1. 对比修改前后的完整提示词输出
2. 检查是否意外修改了其他层的内容
3. 使用Git比较找出具体变更
4. 逐步回滚修改，定位问题层

## 📊 性能监控

### 关键指标

```python
# 构建提示词后查看指标
prompt, metrics = builder.build(...)

print(f"""
性能报告：
- 总Token数：{metrics.total_tokens}/{builder.max_tokens}
- 构建耗时：{metrics.build_time:.3f}秒
- 活跃层数：{metrics.active_layers}
- Token使用率：{metrics.total_tokens/builder.max_tokens*100:.1f}%
""")
```

### 优化建议

- **Token使用率 > 90%**：考虑精简内容或禁用次要层
- **构建时间 > 0.1秒**：检查是否有重复计算
- **活跃层数过多**：评估是否所有层都必要

## 🔄 版本迁移指南

### 从旧版本（单一提示词）迁移

如果需要从 `config.py` 中的单一提示词迁移到Context Expansion：

1. **分析原始提示词结构**
2. **按功能拆分内容到对应层**
3. **保持原有逻辑不变**
4. **逐步测试每个层的效果**

### 向新版本迁移

添加新功能时：

1. **优先考虑在现有层中扩展**
2. **确实需要时才创建新层**
3. **保持向后兼容性**
4. **添加相应的单元测试**

## 📞 应急联系

如果遇到紧急问题：

1. **临时回滚：** 禁用所有新层，使用最小配置
2. **快速恢复：** 参考Git历史记录
3. **问题定位：** 使用调试日志逐层排查

---

## 📝 更新日志

| 日期 | 修改内容 | 修改人 |
|------|----------|--------|
| 2024-01-XX | 创建Context Expansion系统 | [原开发者] |
| 2024-01-XX | 添加RepeatDetectionLayer | [原开发者] |
| [当前日期] | 创建交接文档 | [交接人] |

---

**💡 提示：** 这个系统的核心思想是"分而治之"。遇到问题时，先定位是哪个层的问题，然后单独调试该层，最后再集成测试。

**🎯 目标：** 让每个新手都能在30分钟内理解系统，1小时内完成第一次修改！
