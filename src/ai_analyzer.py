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
from .prompt import MOBILE_USE_DOUBAO
import base64
# from volcenginesdkarkruntime import Ark
import math
from openai import OpenAI

logger = get_logger(__name__)

class AIAnalyzer:
    """AI分析器"""
    
    def __init__(self):
        if not config.dashscope_api_key:
            raise ValueError("未配置DASHSCOPE_API_KEY")
        
        # 显示当前模型配置
        # self.client = Ark(
        #     api_key=config.ark_api_key,
        # )
        api_key = config.ark_api_key
        self.client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
        config.print_model_config()
    
    # 图片转 Base64 工具函数
    def encode_image(self, image_path):
        
        image_format = image_path.split('.')[-1]  # 提取图片格式（如png）
        
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8'), image_format
    
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
        
        # 构建提示词
        
        # system_prompt = MOBILE_USE_DOUBAO.format(language="Chinese", instruction=config.get_ai_system_prompt())
        system_prompt = config.get_ai_system_prompt()
        user_prompt = self._build_prompt(query,xml_path, current_step, history_steps, intervention_prompt, restart_from_step)
        
        base64_image, image_format = self.encode_image(screenshot_path)
        # 调用AI模型，添加稳定输出参数
        # 构建多轮对话消息列表
        messages = [
            {
                "role": "user",
                "content": system_prompt + user_prompt
            }
        ]
        
        # 如果有历史步骤，添加到消息列表中
        # if history_steps:
        #     for step in history_steps:
        #         messages.append({
        #             "role": "assistant",
        #             "content": f"{step.get('content', '')}"
        #         })
        
        # 添加当前图片消息
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_format};base64,{base64_image}"
                    }
                }
            ]
        })
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # logger.info(f"模型输入: {user_prompt}")
                response = self.client.chat.completions.create(
                    model=config.model_name,
                    messages=messages,
                    # 使用配置文件中的稳定输出参数
                    **config.model_params
                )
                
                if config.model_name in ['qwen-max', 'qwen-plus', 'qwen-plus-latest', 'qwen-max-latest']:
                    result = response.output.text
                elif config.model_name in ['doubao-1-5-thinking-vision-pro-250428']:
                    result = response.choices[0].message.content
                else:
                    result = response.output.choices[0].message.content
                # result = response.output.choices[0].message.content
                logger.debug(f"🤖 AI原始响应: {result} ")
                logger.debug(f"🤖 AI原始响应: {response.choices[0].message.reasoning_content}")
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
        # return config.get_ai_system_prompt()

    def _parse_response(self, response: str) -> dict:
        """解析AI响应"""
        # 清理响应文本
        cleaned_response = self._clean_response(response, config.default_screen_resolution)
        
        # 提取第一个完整的JSON对象
        json_obj = self._extract_first_valid_json(cleaned_response)


        if json_obj:
            # 验证和修复必要字段
            return self._validate_and_fix_response(json_obj)
        else:
            # 直接抛出异常，不使用备用方案
            raise ValueError(f"无法解析AI响应为有效JSON格式。响应内容: {response[:200]}...")

    
    def _clean_response(self, response: str, img_size: tuple) -> str:
        """
        清理AI响应文本，将包含坐标的自定义标签转换为JSON数组，并进行坐标转换。
        
        Args:
            response: AI响应的原始文本。
            img_size: 图片尺寸元组 (width, height)，用于坐标转换。
            
        Returns:
            处理和转换后的响应字符串。
        """
        response = re.sub(r'```json\s*|```\s*', '', response).strip()
        img_width, img_height = img_size

        def convert_bbox(match):
            coords = match.group(1).strip().split()
            if len(coords) == 4:
                x1, y1, x2, y2 = map(int, coords)
                rel_x1 = int(x1 * img_width / 1000)
                rel_y1 = int(y1 * img_height / 1000)
                rel_x2 = int(x2 * img_width / 1000)
                rel_y2 = int(y2 * img_height / 1000)
                return json.dumps([[rel_x1, rel_y1], [rel_x2, rel_y2]])
            return match.group(0)

        def convert_point(match):
            coords = match.group(1).strip().split()
            if len(coords) == 2:
                x, y = map(int, coords)
                rel_x = int(x * img_width / 1000)
                rel_y = int(y * img_height / 1000)
                return json.dumps([rel_x, rel_y])
            return match.group(0)

        # 使用 re.sub 和替换函数来处理坐标
        response = re.sub(r'"<bbox>(.*?)</bbox>"', convert_bbox, response)
        response = re.sub(r'"<point>(.*?)</point>"', convert_point, response)
        
        return response.strip()
    
    def _extract_first_valid_json(self, text: str) -> dict:
        """提取第一个有效的JSON对象"""
        
        try:
            result = self._find_complete_json_object(text)
            if result and isinstance(result, dict):
                logger.debug(f"✅ JSON解析成功")
                return result
        except Exception as e:
            logger.warning(f"⚠️  JSON解析失败: {e}")
        
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
    
    
    
    def _validate_and_fix_response(self, json_obj: dict) -> dict:
        """验证和修复AI响应"""
        # 确保必要字段存在
        if not isinstance(json_obj.get("observation"), str):
            json_obj["observation"] = "AI分析结果"
        
        if "is_task_completed" not in json_obj:
            json_obj["is_task_completed"] = False
        
        if "completion_reason" not in json_obj:
            json_obj["completion_reason"] = ""
        
        
        logger.info(f"✅ AI分析成功: {json_obj['observation']}")
        return json_obj
    
    
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