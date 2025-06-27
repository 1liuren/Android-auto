import uiautomator2 as u2
import time
import json
from PIL import Image, ImageDraw, ImageFont
from lxml import etree
import os
from dashscope import Generation
import re
import uuid
from config import config
from xml.etree import ElementTree as ET

# 初始化设备
try:
    # d = u2.connect_usb()  # 或 u2.connect("device_ip")
    d = u2.connect(config.device_id)
    print(f"✅ 成功连接设备: {config.device_id}")
except Exception as e:
    print(f"❌ 设备连接失败: {e}")
    print("请检查设备连接和adb调试是否开启")
    exit(1)

# 任务数据结构
task_data = None  # 将在运行时初始化

def is_task_likely_completed(query, observation, xml_content=None):
    """
    分析任务是否可能已完成（本地辅助判断）
    """
    query_lower = query.lower()
    obs_lower = observation.lower()
    
    # 定义任务完成的关键词匹配
    completion_indicators = {
        "打开": ["已进入", "打开成功", "应用启动", "主界面", "首页"],
        "查找": ["搜索结果", "找到", "已显示", "结果页面", "查询结果"],
        "搜索": ["搜索结果", "找到", "已显示", "结果页面", "查询结果"],
        "进入": ["已进入", "页面显示", "界面加载", "成功进入"],
        "京东": ["京东主页", "京东首页", "京东应用", "商城主页"],
        "快递": ["快递查询", "物流信息", "快递单号", "快递页面", "查快递"]
    }
    
    # 检查任务关键词
    for task_type, indicators in completion_indicators.items():
        if task_type in query_lower:
            for indicator in indicators:
                if indicator in obs_lower:
                    return True, f"检测到任务完成指标: {indicator}"
    
    # 特殊情况：京东快递查询
    if "京东" in query_lower and "快递" in query_lower:
        jd_indicators = ["快递查询", "我的快递", "物流查询", "查快递", "快递服务"]
        for indicator in jd_indicators:
            if indicator in obs_lower:
                return True, f"京东快递查询功能已显示: {indicator}"
    
    # 检查XML内容中的关键元素（如果提供）
    if xml_content:
        try:
            # 根据任务类型查找特定的UI元素
            if "快递" in query_lower:
                express_elements = ["快递查询", "快递单号", "物流查询", "查快递", "快递信息", "express", "tracking"]
                for element in express_elements:
                    if element in xml_content:
                        return True, f"界面显示快递功能: {element}"
            
            if "搜索" in query_lower or "查找" in query_lower:
                search_elements = ["搜索结果", "查询结果", "找到", "search_result", "结果页"]
                for element in search_elements:
                    if element in xml_content:
                        return True, f"界面显示搜索结果: {element}"
            
            # 通用完成状态元素
            completion_elements = ["完成", "成功", "已完成", "完成页面"]
            for element in completion_elements:
                if element in xml_content:
                    return True, f"界面显示完成状态: {element}"
        except:
            pass
    
    return False, ""

def save_screenshot_and_xml(step_num, folder="screenshots"):
    """保存截图和XML文件"""
    os.makedirs(folder, exist_ok=True)
    screenshot_path = f"{folder}/{step_num}.jpg"
    xml_path = f"{folder}/{step_num}.xml"
    
    d.screenshot(screenshot_path)
    xml = d.dump_hierarchy()
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)
    
    return screenshot_path, xml_path


def parse_xml_for_elements(xml_content, keywords=None, action_type="tap"):
    """从XML中解析UI元素并返回坐标信息"""
    try:
        tree = etree.fromstring(xml_content.encode())
        elements = []
        
        print(f"🔍 在XML中搜索关键词: {keywords}")
        
        if keywords:
            for keyword in keywords:
                # 搜索text、content-desc、resource-id属性
                found_nodes = tree.xpath(f"""
                    //node[
                        contains(@text, '{keyword}') or 
                        contains(@content-desc, '{keyword}') or 
                        contains(@resource-id, '{keyword}')
                    ]
                """)
                
                print(f"   关键词 '{keyword}': 找到 {len(found_nodes)} 个元素")
                
                for node in found_nodes:
                    element_info = extract_element_info(node)
                    if element_info:
                        elements.append(element_info)
                        print(f"     {element_info}")
        
        # 如果没有找到，搜索所有可点击元素
        if not elements and action_type == "tap":
            clickable_nodes = tree.xpath("//node[@clickable='true']")
            print(f"🔍 搜索所有可点击元素: 找到 {len(clickable_nodes)} 个")
            
            for node in clickable_nodes[:10]:  # 限制显示前10个
                element_info = extract_element_info(node)
                if element_info:
                    elements.append(element_info)
        
        return elements
        
    except Exception as e:
        print(f"❌ XML解析失败: {e}")
        return []


def extract_element_info(node):
    """从XML节点提取元素信息"""
    try:
        text = node.attrib.get('text', '')
        content_desc = node.attrib.get('content-desc', '')
        resource_id = node.attrib.get('resource-id', '')
        bounds = node.attrib.get('bounds', '')
        clickable = node.attrib.get('clickable', 'false')
        
        if bounds:
            # 解析bounds [x1,y1][x2,y2]
            import re
            matches = re.findall(r'\[(\d+),(\d+)\]', bounds)
            if len(matches) == 2:
                x1, y1 = int(matches[0][0]), int(matches[0][1])
                x2, y2 = int(matches[1][0]), int(matches[1][1])
                
                # 计算中心点
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                return {
                    'text': text,
                    'content_desc': content_desc,
                    'resource_id': resource_id,
                    'bounds': bounds,
                    'clickable': clickable,
                    'position': [center_x, center_y],
                    'box': [[x1, y1], [x2, y2]]
                }
    except Exception as e:
        print(f"❌ 提取元素信息失败: {e}")
    
    return None


def query_text_model(xml_path, query, current_step=1):
    """使用阿里云文本模型分析XML界面结构"""
    try:
        # 检查API密钥
        if not config.dashscope_api_key:
            return {
                "observation": "未配置DASHSCOPE_API_KEY，请设置环境变量",
                "plan": {
                    "description": "手动操作",
                    "type": "Manual", 
                    "position": [540, 1200]
                }
            }
        
        # 读取XML内容
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        # 获取设备信息
        device_info = d.device_info
        device_width = device_info.get('display', {}).get('width', 1080)
        device_height = device_info.get('display', {}).get('height', 2400)
        
        # 使用系统提示词
        system_prompt = config.get_ai_system_prompt()

        user_prompt = f"""
当前任务: {query}
当前步骤: {current_step}
设备分辨率: {device_width}x{device_height}

XML界面结构信息:
{xml_content}

请分析XML结构并告诉我下一步应该如何操作。返回JSON格式：
{{
    "observation": "界面状态描述",
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

        response = Generation.call(
            api_key=config.dashscope_api_key,
            model=config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        result = response.output.choices[0].message.content
        if not result:
            # 尝试其他可能的响应格式
            result = response.get("output", {}).get("text", "") or str(response)
        print(f"🤖 模型分析结果: {result}")
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分（可能包含其他文本）
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_result = json.loads(json_str)
                return parsed_result
            else:
                raise json.JSONDecodeError("No JSON found", result, 0)
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试提取有用信息
            return {
                "observation": result[:200] + "..." if len(result) > 200 else result,
                "plan": {
                    "description": "AI分析中，请手动操作",
                    "type": "Manual",
                    "position": [540, 1200]
                }
            }
    
    except Exception as e:
        print(f"❌ 模型调用错误: {e}")
        return {
            "observation": f"模型调用失败: {str(e)}",
            "plan": {
                "description": "手动操作",
                "type": "Manual",
                "position": [540, 1200]
            }
        }


def draw_label_with_text(screenshot_path, box, label_path, description="", position=None):
    """在截图上绘制点击中心点和小范围标记框"""
    try:
        img = Image.open(screenshot_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 获取点击中心位置
        center_x, center_y = None, None
        
        if position:
            # 如果直接提供了position，优先使用
            center_x, center_y = int(position[0]), int(position[1])
        elif box:
            # 从box计算中心点
            if isinstance(box, list) and len(box) >= 2:
                # 检查是否是 [[x1,y1], [x2,y2]] 格式
                if isinstance(box[0], list) and len(box[0]) >= 2:
                    x1, y1 = int(box[0][0]), int(box[0][1])
                    x2, y2 = int(box[1][0]), int(box[1][1])
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                # 检查是否是 [x1, y1, x2, y2] 格式
                elif len(box) >= 4:
                    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        
        if center_x is not None and center_y is not None:
            # 绘制点击中心点（红色圆点）
            point_size = 8
            draw.ellipse([center_x - point_size, center_y - point_size, 
                         center_x + point_size, center_y + point_size], 
                        fill="red", outline="red")
            
            # 绘制小范围标记框（30x30像素的方框）
            box_size = 15
            small_box = [center_x - box_size, center_y - box_size, 
                        center_x + box_size, center_y + box_size]
            draw.rectangle(small_box, outline="red", width=2)
            
            # 绘制十字中心线
            line_length = 12
            # 横线
            draw.line([center_x - line_length, center_y, center_x + line_length, center_y], 
                     fill="red", width=2)
            # 竖线
            draw.line([center_x, center_y - line_length, center_x, center_y + line_length], 
                     fill="red", width=2)
            
            # 添加坐标标注
            coord_text = f"({center_x}, {center_y})"
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # 在点击位置旁边显示坐标
            text_x = center_x + 20
            text_y = center_y - 30
            
            # 确保文字不会超出图片边界
            if text_x + 100 > img.width:
                text_x = center_x - 120
            if text_y < 0:
                text_y = center_y + 20
            
            # 绘制坐标文字（带背景）
            text_bbox = draw.textbbox((text_x, text_y), coord_text, font=font)
            draw.rectangle([text_bbox[0] - 2, text_bbox[1] - 2, 
                           text_bbox[2] + 2, text_bbox[3] + 2], 
                          fill="white", outline="red")
            draw.text((text_x, text_y), coord_text, fill="red", font=font)
            
            # 添加操作描述
            if description:
                desc_y = text_y + 20
                if desc_y + 20 > img.height:
                    desc_y = text_y - 20
                
                # 限制描述文字长度
                if len(description) > 20:
                    description = description[:20] + "..."
                
                desc_bbox = draw.textbbox((text_x, desc_y), description, font=font)
                draw.rectangle([desc_bbox[0] - 2, desc_bbox[1] - 2, 
                               desc_bbox[2] + 2, desc_bbox[3] + 2], 
                              fill="white", outline="blue")
                draw.text((text_x, desc_y), description, fill="blue", font=font)
            
            print(f"✅ 标记点击位置: ({center_x}, {center_y})")
        else:
            print("⚠️  无法确定点击位置，保存原图")
        
        img.save(label_path)
        return True
        
    except Exception as e:
        print(f"❌ 绘制标记失败: {e}")
        print(f"   position: {position}, box: {box}")
        return False





def test_device_connection():
    """测试设备连接和功能"""
    try:
        print("🔍 正在测试设备连接...")
        
        # 测试设备信息
        device_info = d.device_info
        print(f"📱 设备信息: {device_info.get('display', {}).get('width', 'unknown')}x{device_info.get('display', {}).get('height', 'unknown')}")
        
        # 测试截图功能
        print("📸 测试截图功能...")
        d.screenshot("test_screenshot.jpg")
        print("✅ 截图功能正常")
        
        # 测试点击功能（点击屏幕中央）
        width = device_info.get('display', {}).get('width', 1080)
        height = device_info.get('display', {}).get('height', 2400)
        center_x, center_y = width // 2, height // 2
        
        print(f"🧪 测试点击功能（点击屏幕中央: {center_x}, {center_y}）...")
        d.click(center_x, center_y)
        time.sleep(1)
        print("✅ 点击功能测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 设备连接测试失败: {e}")
        return False


def auto_execute_action(plan):
    """自动执行操作（可选功能）"""
    try:
        print(f"🚀 准备执行操作: {plan}")
        action_type = plan.get("type", "").lower()
        
        # 检查设备是否响应
        try:
            current_app = d.app_current()
            print(f"📱 当前应用: {current_app.get('package', 'unknown')}")
        except:
            print("⚠️  无法获取当前应用信息")
        
        if action_type == "tap" and "position" in plan:
            x, y = int(plan["position"][0]), int(plan["position"][1])
            print(f"🎯 准备点击位置: ({x}, {y})")
            
            # 验证坐标是否在屏幕范围内
            device_info = d.device_info
            width = device_info.get('display', {}).get('width', 1080)
            height = device_info.get('display', {}).get('height', 2400)
            
            if 0 <= x <= width and 0 <= y <= height:
                print(f"✅ 坐标在屏幕范围内 ({width}x{height})")
                d.click(x, y)
                print(f"✅ 已执行点击 ({x}, {y})")
                time.sleep(3)
                return True
            else:
                print(f"❌ 坐标超出屏幕范围: ({x}, {y}) vs ({width}x{height})")
                return False
            
        elif action_type == "typing" and "text" in plan:
            text = plan["text"]
            print(f"⌨️  准备输入文本: {text}")
            d.send_keys(text)
            print(f"✅ 已输入文本: {text}")
            time.sleep(1)
            return True
            
        elif action_type == "open" and "app" in plan:
            app_name = plan["app"]
            print(f"📱 准备打开应用: {app_name}")
            
            # 如果有position信息，直接点击应用图标
            if "position" in plan:
                x, y = int(plan["position"][0]), int(plan["position"][1])
                print(f"🎯 点击{app_name}应用图标: ({x}, {y})")
                d.click(x, y)
                print(f"✅ 已点击{app_name}图标")
                time.sleep(4)  # 等待应用启动
                return True
            else:
                # 尝试通过应用名称启动
                try:
                    print(f"📦 尝试通过包名启动京东...")
                    d.app_start("com.jingdong.app.mall")
                    print(f"✅ 已启动京东应用")
                    time.sleep(4)
                    return True
                except Exception as e:
                    print(f"❌ 无法通过包名启动{app_name}: {e}")
                    return False
        else:
            print(f"❌ 未知操作类型或缺少必要参数: {action_type}")
            return False
            
    except Exception as e:
        print(f"❌ 自动执行操作失败: {e}")
        import traceback
        traceback.print_exc()
    
    return False


def run_task_with_ai(query: str):
    """使用AI分析运行任务"""
    global task_data
    
    # 初始化任务数据
    episode_id = str(uuid.uuid4())[:8]
    task_data = config.get_task_template(query, episode_id)
    
    step = 1
    max_steps = config.max_steps
    
    print(f"🚀 开始执行任务: {task_data['query']}")
    print(f"📱 设备: {task_data['phone']} ({task_data['os']})")
    print(f"🆔 任务ID: {task_data['episode_id']}")
    
    while step <= max_steps:
        print(f"\n=== 步骤 {step} ===")
        
        # 自动执行AI建议
        print("🤖 AI自动模式：将自动执行AI建议的操作")
        print("💡 提示: 按 Ctrl+C 可随时中断程序")
        time.sleep(2)  # 给用户2秒时间看清信息
        user_input = 'auto'
        
        if user_input == 'end':
            break
        
        # 截图和获取XML
        screenshot_path, xml_path = save_screenshot_and_xml(step)
        
        # 使用AI分析XML结构
        ai_result = query_text_model(xml_path, task_data['query'], step)
        
        observation = ai_result.get("observation", "无法分析当前界面")
        is_completed_ai = ai_result.get("is_task_completed", False)
        completion_reason_ai = ai_result.get("completion_reason", "")
        
        # 读取XML内容用于本地判断
        try:
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content_for_analysis = f.read()
        except:
            xml_content_for_analysis = None
        
        # 结合AI判断和本地判断
        is_completed_local, completion_reason_local = is_task_likely_completed(
            task_data['query'], observation, xml_content_for_analysis)
        
        # 如果任一方法判断完成，则认为任务完成
        is_completed = is_completed_ai or is_completed_local
        completion_reason = completion_reason_ai or completion_reason_local
        
        plan = ai_result.get("plan", {})
        
        print(f"\n📊 AI分析结果:")
        print(f"   观察: {observation}")
        print(f"   AI判断完成: {'✅ 是' if is_completed_ai else '❌ 否'}")
        print(f"   本地判断完成: {'✅ 是' if is_completed_local else '❌ 否'}")
        print(f"   综合判断: {'✅ 是' if is_completed else '❌ 否'}")
        if completion_reason:
            print(f"   完成原因: {completion_reason}")
        print(f"   建议: {plan.get('description', '无建议')}")
        print(f"   位置: {plan.get('position', '未提供')}")
        
        # 检查任务是否完成
        if is_completed or plan.get("type", "").lower() == "end":
            print(f"\n🎉 任务执行完成！")
            if completion_reason:
                print(f"✅ 完成原因: {completion_reason}")
            else:
                print(f"✅ AI判断任务目标已达到")
            
            # 保存最终状态的标记图
            final_position = plan.get("position", [540, 1200])
            box = plan.get("box")
            if not box:
                box = [[final_position[0]-50, final_position[1]-30], 
                       [final_position[0]+50, final_position[1]+30]]
            
            label_path = f"screenshots/{step}_final.jpg"
            draw_label_with_text(screenshot_path, box, label_path, 
                               f"任务完成: {completion_reason or '目标达到'}", final_position)
            
            # 保存任务完成信息
            step_data = {
                "step": step,
                "screenshot": os.path.basename(screenshot_path),
                "xml": os.path.basename(xml_path),
                "observation": observation,
                "plan": [{
                    "description": f"任务完成: {completion_reason or plan.get('description', '目标达到')}",
                    "type": "End",
                    "position": final_position,
                    "box": box
                }],
                "label": os.path.basename(label_path),
                "task_completed": True,
                "completion_reason": completion_reason
            }
            
            task_data["data"].append(step_data)
            print(f"📝 任务总共执行了 {step} 个步骤")
            break
        
        # 如果AI没有提供有效位置，尝试从XML中直接解析
        if not plan.get("position") or plan.get("position") == [540, 1200]:
            description = plan.get("description", "")
            
            # 根据描述提取关键词
            keywords = []
            if "京东" in description:
                keywords = ["京东", "JD", "jd"]
            elif "搜索" in description:
                keywords = ["搜索", "search", "输入"]
            elif "快递" in description:
                keywords = ["快递", "查快递", "物流"]
            else:
                # 从描述中提取可能的关键词
                import re
                potential_keywords = re.findall(r'([点击打开][^，,。！!]+)', description)
                if potential_keywords:
                    keywords = [kw.replace("点击", "").replace("打开", "") for kw in potential_keywords]
            
            if keywords:
                with open(xml_path, "r", encoding="utf-8") as f:
                    xml_content = f.read()
                
                elements = parse_xml_for_elements(xml_content, keywords, plan.get("type", "tap").lower())
                
                if elements:
                    # 选择最合适的元素（优先可点击的）
                    best_element = None
                    for element in elements:
                        if element['clickable'] == 'true':
                            best_element = element
                            break
                    
                    if not best_element:
                        best_element = elements[0]
                    
                    plan["position"] = best_element["position"]
                    plan["box"] = best_element["box"]
                    
                    print(f"🔍 从XML中找到精确位置:")
                    print(f"   元素: {best_element['text'] or best_element['content_desc'] or best_element['resource_id']}")
                    print(f"   位置: {best_element['position']}")
                    print(f"   边界: {best_element['bounds']}")
        
        # 确保有位置信息
        final_position = plan.get("position", [540, 1200])
        if not plan.get("position"):
            plan["position"] = final_position
        
        # 确保有边界框
        box = plan.get("box")
        if not box:
            pos = plan["position"]
            box = [[pos[0]-75, pos[1]-40], [pos[0]+75, pos[1]+40]]
            plan["box"] = box
        
        print(f"🎯 最终操作位置: {plan['position']}")
        
        # 绘制标记
        label_path = f"screenshots/{step}_label.jpg"
        draw_label_with_text(screenshot_path, box, label_path, plan.get("description", ""), plan.get("position"))
        
        # 构建步骤数据
        step_data = {
            "step": step,
            "screenshot": os.path.basename(screenshot_path),
            "xml": os.path.basename(xml_path),
            "observation": observation,
            "plan": [plan],
            "label": os.path.basename(label_path)
        }
        
        # 自动执行操作（如果用户选择）
        if user_input == 'auto':
            success = auto_execute_action(plan)
            if success:
                print("✅ 自动操作执行成功")
            else:
                print("❌ 自动操作执行失败，请手动操作")
        
        task_data["data"].append(step_data)
        
        # 检查是否完成
        if plan.get("type", "").lower() == "end":
            print("🎉 任务完成！")
            break
        
        step += 1
    
    # 保存结果
    with open("task.json", "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=4, ensure_ascii=False)
    
    print("✅ 任务数据已保存到 task.json")


def run_manual_task(query: str):
    """手动模式运行任务（原始逻辑）"""
    global task_data
    
    # 初始化任务数据
    episode_id = str(uuid.uuid4())[:8]
    task_data = config.get_task_template(query, episode_id)
    
    steps = [
        {"query": "打开京东", "action_type": "Open", "app": "京东"},
        {"query": "点击搜索框", "action_type": "Tap"},
        {"query": "输入查快递", "action_type": "Typing", "text": "查快递"},
        {"query": "点击搜索按钮", "action_type": "Tap"},
        {"query": "点击查快递入口", "action_type": "Tap"},
    ]
    
    print(f"🚀 开始手动任务: {task_data['query']}")
    print(f"📱 设备: {task_data['phone']} ({task_data['os']})")

    for idx, step in enumerate(steps, start=1):
        input(f"请执行：{step['query']}，完成后按 Enter...")
        screenshot_path, xml_path = save_screenshot_and_xml(f"{idx}")
        
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        # 尝试从XML中找到相关元素
        keywords = ["快递", "搜索", "京东"]
        elements = parse_xml_for_elements(xml_content, keywords)
        
        if elements:
            best_element = elements[0]
            box = best_element["box"]
            position = best_element["position"]
        else:
            # 使用默认边界框位置
            box = [[100, 200], [300, 300]]
            position = [200, 250]
        
        label_path = f"screenshots/{idx}_label.jpg"
        draw_label_with_text(screenshot_path, box, label_path, step["query"], position)

        step_data = {
            "step": idx,
            "screenshot": os.path.basename(screenshot_path),
            "xml": os.path.basename(xml_path),
            "observation": f"执行操作：{step['query']}",
            "plan": [{
                "description": step["query"],
                "type": step["action_type"],
                "position": position,
                "box": box
            }],
            "label": os.path.basename(label_path)
        }

        if step["action_type"] == "Typing":
            step_data["plan"][0]["text"] = step["text"]

        task_data["data"].append(step_data)

    # 终止步骤
    task_data["data"].append({
        "step": len(steps) + 1,
        "screenshot": f"{len(steps)+1}.jpg",
        "xml": f"{len(steps)+1}.xml",
        "observation": "任务已完成",
        "plan": [{"description": "任务完成", "type": "End"}],
        "task_completed": True,
        "completion_reason": "手动任务所有步骤已执行完毕"
    })
    
    print("🎉 手动任务执行完成！")
    print(f"📝 总共执行了 {len(steps)} 个步骤")


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 手机UI自动化任务执行器")
    print("=" * 50)
    
    # 创建截图文件夹
    os.makedirs(config.screenshot_folder, exist_ok=True)
    
    # 测试设备连接
    print("\n🔧 设备连接测试:")
    if not test_device_connection():
        print("\n❌ 设备连接测试失败，请检查：")
        print("1. 手机是否已连接并开启USB调试")
        print("2. 是否已安装uiautomator2服务：python -m uiautomator2 init")
        print("3. 设备ID是否正确")
        print("4. 是否需要在手机上开启无障碍服务")
        choice = input("\n是否继续？(y/n): ").lower()
        if choice != 'y':
            exit(1)
    
    # 获取用户任务
    query = input("\n📝 请输入任务描述（默认：我想在京东上查快递）: ").strip()
    if not query:
        query = "我想在京东上查快递"
    
    print("\n🤖 使用AI智能自动模式")
    print("📋 重要提示:")
    print("- 程序将自动执行AI建议的操作")
    print("- 请保持手机屏幕亮起")
    print("- 程序会自动修正京东位置识别错误")
    print("- 按 Ctrl+C 可随时中断程序")
    input("\n按Enter键开始AI自动模式...")
    
    try:
        run_task_with_ai(query)
        
        # 保存结果
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"task_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ 全部任务完成，结果已保存为 {output_file}")
        print(f"📊 共执行 {len(task_data['data'])} 个步骤")
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        if task_data and task_data.get("data"):
            output_file = f"task_interrupted_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(task_data, f, indent=4, ensure_ascii=False)
            print(f"📄 已保存中断前的数据到 {output_file}")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
