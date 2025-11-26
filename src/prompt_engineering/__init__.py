# auto-phone/src/prompt_engineering/__init__.py
"""
提示词工程模块 - Context Expansion 分层提示词构建系统

🎯 主要功能：
- 分层管理AI提示词，避免单一巨型提示词的维护问题
- 支持动态启用/禁用特定层，便于调试和优化
- 提供性能监控和Token使用统计

🚀 快速开始：
```python
from prompt_engineering import ExpandablePromptBuilder

builder = ExpandablePromptBuilder(max_tokens=4000)
prompt, metrics = builder.build(
    task="执行任务：打开淘宝",
    current_step=1
)
```

📚 详细文档：参考同目录下的 README_交接文档.md
🧪 使用示例：参考 使用示例.py
"""

# 导入Context Expansion组件
from .context_expansion import (
    ContextLayer,
    ContextMetrics,
    BasePromptLayer,
    RoleDefinitionLayer,
    ObservationRulesLayer,
    OutputFormatLayer,
    OperationRulesLayer,
    TaskCompletionRulesLayer,
    SwipeRulesLayer,
    PrivacyProtectionLayer,
    RepeatDetectionLayer,
    ImportantTipsLayer,
    ContextualInfoLayer,
    HistoryLayer,
    DomainKnowledgeLayer,
    ScreenContentLayer,
    ExpandablePromptBuilder,
    create_minimal_prompt,
    create_full_prompt,
    PromptPresets
)

__all__ = [
    # Context Expansion 核心组件
    'ContextLayer',
    'ContextMetrics',
    
    # 上下文层
    'BasePromptLayer',
    'RoleDefinitionLayer',
    'ObservationRulesLayer',
    'OutputFormatLayer',
    'OperationRulesLayer',
    'TaskCompletionRulesLayer',
    'SwipeRulesLayer',
    'PrivacyProtectionLayer',
    'RepeatDetectionLayer',
    'ImportantTipsLayer',
    'ContextualInfoLayer',
    'HistoryLayer',
    'DomainKnowledgeLayer',
    'ScreenContentLayer',
    
    # 构建器和工具
    'ExpandablePromptBuilder',
    'create_minimal_prompt',
    'create_full_prompt',
    'PromptPresets'
]