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
    
    def analyze_screen(self, xml_path: str, query: str, current_step: int = 1, screenshot_path: str = None, history_steps: list = None) -> dict:
        """分析当前屏幕状态并提供操作建议"""
        # 读取XML内容
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        # 如果提供了截图，使用多模态增强
        enhanced_content = xml_content
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                enhanced_content = self._enhance_with_qwenvl_html(xml_content, screenshot_path)
            except Exception as e:
                logger.warning(f"多模态增强失败，使用原始XML: {e}")
        
        # 构建提示词
        user_prompt = self._build_prompt(query, enhanced_content, current_step, history_steps)
        
        # 调用AI模型，添加稳定输出参数
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
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
                
                if config.model_name == 'qwen-max':
                    result = response.output.text
                else:
                    result = response.output.choices[0].message.content
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
    
    def _build_prompt(self, query: str, xml_content: str, current_step: int, history_steps: list = None) -> str:
        """构建AI提示词"""
        return config.get_analysis_prompt(query, xml_content, current_step, history_steps)
    
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
            logger.info("🖼️ 开始使用QwenVL HTML提取截图文本...")
            
            # 1. 使用QwenVL HTML提取截图中的文本信息
            html_content = self._extract_text_with_qwenvl_html(screenshot_path)
            
            if not html_content:
                logger.warning("QwenVL HTML提取失败，使用原始XML")
                return xml_content
            
            # 2. 将提取的HTML文本信息作为注释添加到XML开头
            enhanced_xml = f"""<!-- 
=== QwenVL HTML 提取的界面文本信息 ===
{html_content}
-->

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
                    "content": "You are an AI specialized in recognizing and extracting text from images. Your mission is to analyze the image document and generate the result in QwenVL Document Parser HTML format using specified tags while maintaining user privacy and data integrity."
                },
                {
                    "role": "user",
                    "content": [
                        {"image": image_path},
                        {"text": "QwenVL HTML"}
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
            
            logger.info(f"🤖 QwenVL HTML提取完成，响应长度: {len(html_content)} 字符")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ QwenVL HTML调用失败: {e}")
            return "" 