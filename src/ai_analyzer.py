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
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
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
        api_key = "b2343050-267b-4913-8365-eb1c5251ea3d"
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
                logger.info(f"🤖 AI原始响应长度: {len(result)} 字符")
                break
            except Exception as e:
                retry_count += 1
                logger.warning(f"AI调用失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count >= max_retries:
                    logger.error(f"AI调用失败，已达到最大重试次数: {str(e)}")
                    raise
        
        # 解析AI响应（如果失败会直接抛出异常）
        print(result)
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
        cleaned_response = self._clean_response(response)
        
        # 提取第一个完整的JSON对象
        json_obj = self._extract_first_valid_json(cleaned_response)
        # 转换坐标
        json_obj["plan"]["position"] = self.position_convert(json_obj["plan"]["position"], config.default_screen_resolution) if json_obj["plan"]["position"] else None
        json_obj["plan"]["box"] = self.box_convert(json_obj["plan"]["box"], config.default_screen_resolution) if json_obj["plan"]["box"] else None
        json_obj["plan"]["start_position"] = self.position_convert(json_obj["plan"]["start_position"], config.default_screen_resolution) if json_obj["plan"]["start_position"] else None
        json_obj["plan"]["stop_position"] = self.position_convert(json_obj["plan"]["stop_position"], config.default_screen_resolution) if json_obj["plan"]["stop_position"] else None

        if json_obj:
            # 验证和修复必要字段
            return self._validate_and_fix_response(json_obj)
        else:
            # 直接抛出异常，不使用备用方案
            raise ValueError(f"无法解析AI响应为有效JSON格式。响应内容: {response[:200]}...")
    
    def _parse_doubao_response(self, response: str) -> dict:
        """解析AI响应"""
        parsed_output = json.loads(parse_action_output(response))
        print(parsed_output)

        # 转换坐标
        parsed_output["start_box"] = self.box_convert(parsed_output["start_box"], config.default_screen_resolution) if parsed_output["start_box"] else None
        parsed_output["end_box"] = self.box_convert(parsed_output["end_box"], config.default_screen_resolution) if parsed_output["end_box"] else None
        return parsed_output

    def parse_action_output(self, output_text):
        # 提取Thought部分
        thought_match = re.search(r'Thought:(.*?)\nAction:', output_text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取Action部分
        action_match = re.search(r'Action:(.*?)(?:\n|$)', output_text, re.DOTALL)
        action_text = action_match.group(1).strip() if action_match else ""

        # 初始化结果字典
        result = {
            "thought": thought,
            "action": "",
            "key": None,
            "content": None,
            "start_box": None,
            "end_box": None,
            "direction": None
        }

        if not action_text:
            return json.dumps(result, ensure_ascii=False)

        # 解析action类型
        action_parts = action_text.split('(')
        action_type = action_parts[0]
        result["action"] = action_type

        # 解析参数
        if len(action_parts) > 1:
            params_text = action_parts[1].rstrip(')')
            params = {}

            # 处理键值对参数
            for param in params_text.split(','):
                param = param.strip()
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('\'"')

                    # 处理bbox格式
                    if 'box' in key:
                        # 提取坐标数字
                        numbers = re.findall(r'\d+', value)
                        if numbers:
                            coords = [int(num) for num in numbers]
                            if len(coords) == 4:
                                if key == 'start_box':
                                    result["start_box"] = coords
                                elif key == 'end_box':
                                    result["end_box"] = coords
                    elif key == 'key':
                        result["key"] = value
                    elif key == 'content':
                        # 处理转义字符
                        value = value.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")
                        result["content"] = value
                    elif key == 'direction':
                        result["direction"] = value

        return json.dumps(result, ensure_ascii=False, indent=2)

    def box_convert(self, relative_bbox, img_size):
        """
        将相对坐标[0,1000]转换为图片上的绝对像素坐标

        参数:
            relative_bbox: 相对坐标列表/元组 [x1, y1, x2, y2] (范围0-1000)
            img_size: 图片尺寸元组 (width, height)

        返回:
            绝对坐标列表 [x1, y1, x2, y2] (单位:像素)

        示例:
            >>> coordinates_convert([500, 500, 600, 600], (1000, 2000))
            [500, 1000, 600, 1200]  # 对于2000高度的图片，y坐标×2
        """
        # 参数校验
        # if len(relative_bbox) != 4 or len(img_size) != 2:
        #     raise ValueError("输入参数格式应为: relative_bbox=[x1,y1,x2,y2], img_size=(width,height)")

        # 解包图片尺寸
        img_width, img_height = img_size

        # 计算绝对坐标
        abs_x1 = int(relative_bbox[0][0] * img_width / 1000)
        abs_y1 = int(relative_bbox[0][1] * img_height / 1000)
        abs_x2 = int(relative_bbox[1][0] * img_width / 1000)
        abs_y2 = int(relative_bbox[1][1] * img_height / 1000)

        return [[abs_x1, abs_y1], [abs_x2, abs_y2]]

    def position_convert(self, position, img_size):
        """
        将相对坐标[0,1000]转换为图片上的绝对像素坐标

        参数:
            position: 相对坐标列表/元组 [x, y] (范围0-1000)
            img_size: 图片尺寸元组 (width, height)

        返回:
            绝对坐标列表 [x1, y1, x2, y2] (单位:像素)

        示例:
            >>> coordinates_convert([500, 500, 600, 600], (1000, 2000))
            [500, 1000, 600, 1200]  # 对于2000高度的图片，y坐标×2
        """
        # 参数校验
        if len(position) != 2 or len(img_size) != 2:
            raise ValueError("输入参数格式应为: position=[x,y], img_size=(width,height)")

        # 解包图片尺寸
        img_width, img_height = img_size

        # 计算绝对坐标
        abs_x = int(position[0] * img_width / 1000)
        abs_y = int(position[1] * img_height / 1000)

        return [abs_x, abs_y]

    def draw_box_and_show(self, image, start_box=None, end_box=None, direction=None):
        """
        在图片上绘制两个边界框和指向箭头

        参数:
            image: PIL.Image对象或图片路径
            start_box: 起始框坐标 [x1,y1,x2,y2] (绝对坐标)
            end_box: 结束框坐标 [x1,y1,x2,y2] (绝对坐标)
            direction: 操作方向 ('up', 'down', 'left', 'right' 或 None)
        """
        box_color = "red"
        arrow_color = "blue"
        box_width = 10
        drag_arrow_length = 150  # drag操作箭头长度

        draw = ImageDraw.Draw(image)

        # 绘制起始框
        if start_box is not None:
            draw.rectangle(start_box, outline=box_color, width=box_width)

        # 绘制结束框
        if end_box is not None:
            draw.rectangle(end_box, outline=box_color, width=box_width)

        # 处理不同类型的操作
        if start_box is not None:
            start_center = ((start_box[0] + start_box[2]) / 2, (start_box[1] + start_box[3]) / 2)

            if end_box is not None:
                # 绘制两个框之间的连接线和箭头
                end_center = ((end_box[0] + end_box[2]) / 2, (end_box[1] + end_box[3]) / 2)
                draw.line([start_center, end_center], fill=arrow_color, width=box_width)
                draw_arrow_head(draw, start_center, end_center, arrow_color, box_width * 3)
            elif direction is not None:
                # 处理drag操作（只有start_box和direction）
                end_point = calculate_drag_endpoint(start_center, direction, drag_arrow_length)
                draw.line([start_center, end_point], fill=arrow_color, width=box_width)
                draw_arrow_head(draw, start_center, end_point, arrow_color, box_width * 3)

        # 显示结果图片
        plt.imshow(image)
        plt.axis('on')  # 不显示坐标轴
        plt.show()

    def draw_arrow_head(self, draw, start, end, color, size):
        """
        绘制箭头头部
        """
        # 计算角度
        angle = math.atan2(end[1] - start[1], end[0] - start[0])

        # 计算箭头三个点的位置
        p1 = end
        p2 = (
            end[0] - size * math.cos(angle + math.pi / 6),
            end[1] - size * math.sin(angle + math.pi / 6)
        )
        p3 = (
            end[0] - size * math.cos(angle - math.pi / 6),
            end[1] - size * math.sin(angle - math.pi / 6)
        )

        # 绘制箭头
        draw.polygon([p1, p2, p3], fill=color)

    def calculate_drag_endpoint(self, start_point, direction, length):
        """
        计算drag操作的箭头终点

        参数:
            start_point: 起点坐标 (x, y)
            direction: 方向 ('up', 'down', 'left', 'right')
            length: 箭头长度

        返回:
            终点坐标 (x, y)
        """
        x, y = start_point
        if direction == 'up':
            return (x, y - length)
        elif direction == 'down':
            return (x, y + length)
        elif direction == 'left':
            return (x - length, y)
        elif direction == 'right':
            return (x + length, y)
        else:
            return (x, y)  # 默认不移动
    
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