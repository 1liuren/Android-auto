#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI分析模块
负责分析界面状态并提供操作建议
"""

import json
import re
from dashscope import Generation
from .config import config

class AIAnalyzer:
    """AI分析器"""
    
    def __init__(self):
        if not config.dashscope_api_key:
            raise ValueError("未配置DASHSCOPE_API_KEY")
        
        # 显示当前模型配置
        config.print_model_config()
    
    def analyze_screen(self, xml_path: str, query: str, current_step: int = 1) -> dict:
        """分析当前屏幕状态并提供操作建议"""
        # 读取XML内容
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        # 构建提示词
        user_prompt = self._build_prompt(query, xml_content, current_step)
        
        # 调用AI模型，添加稳定输出参数
        response = Generation.call(
            api_key=config.dashscope_api_key,
            model=config.model_name,
            messages=[
                {"role": "system", "content": config.get_ai_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            # 使用配置文件中的稳定输出参数
            **config.model_params
        )
        
        result = response.output.choices[0].message.content
        print(f"🤖 AI原始响应长度: {len(result)} 字符")
        
        # 解析AI响应（如果失败会直接抛出异常）
        return self._parse_response(result)
    
    def _build_prompt(self, query: str, xml_content: str, current_step: int) -> str:
        """构建AI提示词"""
        return f"""
当前任务: {query}
当前步骤: {current_step}

XML界面结构信息:
{xml_content}

请分析XML结构并告诉我下一步应该如何操作。请只返回一个JSON格式的响应，不要包含其他文本：
{{
    "observation": "界面状态描述",
    "is_task_completed": true/false,
    "completion_reason": "完成原因（如果已完成）",
    "plan": {{
        "description": "操作描述",
        "type": "操作类型",
        "position": [x, y],
        "box": [[x1, y1], [x2, y2]],
        "text": "输入文本（如需要）",
        "app": "应用名称（如需要）"
    }}
}}
"""
    
    def _parse_response(self, response: str) -> dict:
        """解析AI响应"""
        # 清理响应文本
        cleaned_response = self._clean_response(response)
        
        # 提取第一个完整的JSON对象
        json_obj = self._extract_first_valid_json(cleaned_response)
        
        if json_obj:
            # 验证和修复必要字段
            return self._validate_and_fix_response(json_obj)
        else:
            # 直接抛出异常，不使用备用方案
            raise ValueError(f"无法解析AI响应为有效JSON格式。响应内容: {response[:200]}...")
    
    def _clean_response(self, response: str) -> str:
        """清理AI响应文本"""
        # 移除markdown代码块标记
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # 移除多余的空白字符
        response = response.strip()
        
        return response
    
    def _extract_first_valid_json(self, text: str) -> dict:
        """提取第一个有效的JSON对象"""
        # 尝试多种JSON提取策略
        strategies = [
            # 策略1: 查找第一个完整的JSON对象
            self._find_complete_json_object,
            # 策略2: 使用正则表达式提取
            self._regex_extract_json,
            # 策略3: 逐行解析
            self._line_by_line_parse
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                result = strategy(text)
                if result and isinstance(result, dict):
                    print(f"✅ JSON解析成功，使用策略{i}")
                    return result
            except Exception as e:
                print(f"⚠️  策略{i}解析失败: {e}")
                continue
        
        # 所有策略都失败，返回None
        return None
    
    def _find_complete_json_object(self, text: str) -> dict:
        """查找第一个完整的JSON对象"""
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # 找到完整的JSON对象
                    json_str = text[start_idx:i+1]
                    return json.loads(json_str)
        
        return None
    
    def _regex_extract_json(self, text: str) -> dict:
        """使用正则表达式提取JSON"""
        # 查找第一个JSON对象
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        return None
    
    def _line_by_line_parse(self, text: str) -> dict:
        """逐行解析，适用于格式化的JSON"""
        lines = text.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('{'):
                in_json = True
                brace_count += stripped.count('{') - stripped.count('}')
                json_lines.append(line)
            elif in_json:
                brace_count += stripped.count('{') - stripped.count('}')
                json_lines.append(line)
                if brace_count <= 0:
                    break
        
        if json_lines:
            json_str = '\n'.join(json_lines)
            return json.loads(json_str)
        
        return None
    
    def _validate_and_fix_response(self, json_obj: dict) -> dict:
        """验证和修复AI响应"""
        # 确保必要字段存在
        if not isinstance(json_obj.get("observation"), str):
            json_obj["observation"] = "AI分析结果"
        
        if "is_task_completed" not in json_obj:
            json_obj["is_task_completed"] = False
        
        if "completion_reason" not in json_obj:
            json_obj["completion_reason"] = ""
        
        if "plan" not in json_obj or not isinstance(json_obj["plan"], dict):
            json_obj["plan"] = self._get_default_plan()
        else:
            # 修复plan字段
            plan = json_obj["plan"]
            if "description" not in plan:
                plan["description"] = "继续操作"
            if "type" not in plan:
                plan["type"] = "Manual"
            if "position" not in plan:
                plan["position"] = [540, 1200]
            if "box" not in plan:
                plan["box"] = [[515, 1180], [565, 1220]]
        
        print(f"✅ AI分析成功: {json_obj['observation']}")
        return json_obj
    
    def _get_default_plan(self) -> dict:
        """获取默认操作计划"""
        return {
            "description": "请手动操作",
            "type": "Manual",
            "position": [540, 1200],
            "box": [[515, 1180], [565, 1220]]
        } 