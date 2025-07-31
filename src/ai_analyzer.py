#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI分析模块
负责分析界面状态并提供操作建议
"""

import json
import re
import os
from dashscope import Generation
from dashscope import MultiModalConversation
from .config import config
from .logger_config import get_logger

logger = get_logger(__name__)

class AIAnalyzer:
    """AI分析器"""
    
    def __init__(self):
        if not config.dashscope_api_key:
            raise ValueError("未配置DASHSCOPE_API_KEY")
        
        # 显示当前模型配置
        config.print_model_config()
    
    def analyze_screen(self, xml_path: str, query: str, current_step: int = 1, screenshot_path: str = None, history_steps: list = None, intervention_prompt: str = None, restart_from_step: int = None) -> dict:
        """分析当前屏幕状态并提供操作建议
        
        Args:
            xml_path: XML文件路径
            query: 任务查询
            current_step: 当前步骤
            screenshot_path: 截图路径
            history_steps: 历史步骤
            intervention_prompt: 人工介入的补充说明
            restart_from_step: 从哪一步重新开始（用于插入人工介入）
        """
        # 读取XML内容
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        # 精简XML内容，减少冗余信息
        # from .xml_simplifier import xml_simplifier
        # simplified_xml = xml_simplifier.simplify_xml(xml_content)
        
        # 如果提供了截图且启用了多模态增强，使用多模态增强
        enhanced_content = xml_content
        if (screenshot_path and os.path.exists(screenshot_path) and 
            config.multimodal_enhancement.get("enabled", False)):
            try:
                enhanced_content = self._enhance_with_qwenvl_html(xml_content, screenshot_path)
                if config.multimodal_enhancement.get("debug_mode", False):
                    logger.info("🔍 多模态增强成功")
            except Exception as e:
                if config.multimodal_enhancement.get("fallback_to_xml", True):
                    logger.warning(f"多模态增强失败，回退到原始XML: {e}")
                else:
                    logger.error(f"多模态增强失败: {e}")
                    raise
        
        # 构建提示词
        user_prompt = self._build_prompt(query, enhanced_content, current_step, history_steps, intervention_prompt, restart_from_step)
        
        # 调用AI模型，添加稳定输出参数
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # logger.info(f"模型输入: {user_prompt}")
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
                
                if config.model_name in ['qwen-max', 'qwen-plus', 'qwen-plus-latest', 'qwen-max-latest']:
                    result = response.output.text
                else:
                    result = response.output.choices[0].message.content
                # result = response.output.choices[0].message.content
                logger.info(f"🤖 AI原始响应长度: {len(result)} 字符")
                break
            except Exception as e:
                retry_count += 1
                logger.warning(f"AI调用失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count >= max_retries:
                    logger.error(f"AI调用失败，已达到最大重试次数: {str(e)}")
                    raise
        
        # 解析AI响应（如果失败会直接抛出异常）
        return self._parse_response(result)
    
    def _build_prompt(self, query: str, xml_content: str, current_step: int, history_steps: list = None, intervention_prompt: str = None, restart_from_step: int = None) -> str:
        """构建 AI提示词
        
        Args:
            query: 任务描述
            xml_content: XML内容
            current_step: 当前步骤
            history_steps: 历史步骤
            intervention_prompt: 人工介入的补充说明
            restart_from_step: 从哪一步重新开始（用于插入人工介入）
        """
        return config.get_analysis_prompt(query, xml_content, current_step, history_steps, intervention_prompt, restart_from_step)
    
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
                    logger.debug(f"✅ JSON解析成功，使用策略{i}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️  策略{i}解析失败: {e}")
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
        # else:
        #     # 修复plan字段
        #     plan = json_obj["plan"]
        #     if "description" not in plan:
        #         plan["description"] = "继续操作"
        #     if "type" not in plan:
        #         plan["type"] = "Manual"
        #     if "position" not in plan:
        #         plan["position"] = [540, 1200]
        #     if "box" not in plan:
        #         plan["box"] = [[515, 1180], [565, 1220]]
        
        logger.info(f"✅ AI分析成功: {json_obj['observation']}")
        return json_obj
    
    def _get_default_plan(self) -> dict:
        """获取默认操作计划"""
        return {
            "description": "请手动操作",
            "type": "Manual",
            "position": [540, 1200],
            "box": [[515, 1180], [565, 1220]]
        }
    
    def _enhance_with_qwenvl_html(self, xml_content: str, screenshot_path: str) -> str:
        """使用QwenVL HTML提取文本信息并增强XML"""
        try:
            logger.info("🖼️ 开始使用QwenVL 提取截图文本...")
            
            # 1. 使用QwenVL HTML提取截图中的文本信息
            html_content = self._extract_text_with_qwenvl_html(screenshot_path)
            
            if not html_content:
                logger.warning("QwenVL HTML提取失败，使用原始XML")
                return xml_content
            
            # 2. 将提取的HTML文本信息作为注释添加到XML开头
            enhanced_xml = f"""<!-- 
=== QwenVL 提取的界面文本信息，其中信息可能在xml中不是以明文出现，这个结果可以以便理解界面，从而更好的执行任务 ===
{html_content}
=== 原始XML内容，可能未包含图像中的全部文本 ===

{xml_content}"""
            
            logger.info("✅ XML已通过QwenVL HTML增强")
            return enhanced_xml
            
        except Exception as e:
            logger.error(f"❌ QwenVL HTML增强失败: {e}")
            return xml_content
    
    def _extract_text_with_qwenvl_html(self, screenshot_path: str) -> str:
        """使用QwenVL HTML提取截图中的文本信息"""
        try:
            # 构建多模态请求
            image_path = f"file://{os.path.abspath(screenshot_path)}"
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant specialized in recognizing and extracting text from images of mobile phone UI, describe the information you find."
                },
                {
                    "role": "user",
                    "content": [
                        {"image": image_path},
                        {"text": "请详细描述手机界面中的文字、按钮、图标等元素。如果有选中状态、数据输入框、选择控件等交互元素，请特别说明其当前状态和选中值。提供完整、准确的界面描述，以便更好地执行操作。"}
                    ]
                }
            ]
            
            # 调用多模态模型
            response = MultiModalConversation.call(
                api_key=config.dashscope_api_key,
                model='qwen-vl-max-latest',
                messages=messages,
                parameters={
                    "incremental_output": True
                }
            )
            
            result = response["output"]["choices"][0]["message"]["content"]
            
            # 如果返回的是列表（可能包含多个内容块）
            if isinstance(result, list):
                html_content = ""
                for item in result:
                    if isinstance(item, dict) and "text" in item:
                        html_content += item["text"]
            else:
                html_content = result
            
            # logger.info(f"🤖 QwenVL HTML提取完成，响应: {html_content}")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ QwenVL HTML调用失败: {e}")
            return "" 