#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XML精简处理器
用于减少XML冗余信息，只保留对AI模型判断有用的关键部分
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from .logger_config import get_logger

logger = get_logger(__name__)


class XMLSimplifier:
    """XML精简处理器"""
    
    def __init__(self):
        # 需要保留的关键属性（精简版）
        self.key_attributes = {
            'text',           # 文本内容
            'content-desc',   # 内容描述
            'resource-id',    # 资源ID
            'class',          # 组件类型
            'bounds',         # 边界坐标
            'clickable',      # 是否可点击
            'scrollable',     # 是否可滚动
            'enabled',        # 是否启用
            'selected',       # 是否选中
            'checked',        # 是否勾选
            'focused',        # 是否聚焦
            'password',       # 是否密码框
            'checkable',      # 是否可勾选
        }
        
        # 需要过滤的无用类名（扩展版）
        self.useless_classes = {
            'android.view.View',
            'android.widget.FrameLayout', 
            'android.widget.LinearLayout',
            'android.widget.RelativeLayout',
            'android.support.v7.widget.RecyclerView',
            'androidx.recyclerview.widget.RecyclerView',
            'android.view.ViewGroup',
            'android.widget.ScrollView',
            'android.widget.HorizontalScrollView',
        }
        
        # 重要的可交互类名
        self.important_classes = {
            'android.widget.Button',
            'android.widget.ImageButton', 
            'android.widget.TextView',
            'android.widget.EditText',
            'android.widget.ImageView',
            'android.widget.CheckBox',
            'android.widget.RadioButton',
            'android.widget.Switch',
            'android.widget.SeekBar',
            'android.widget.Spinner',
            'android.widget.ListView',
            'android.widget.GridView',
            'android.widget.ScrollView',
            'android.widget.HorizontalScrollView',
            'android.widget.ViewPager',
            'android.widget.TabHost',
            'android.widget.WebView',
        }
    
    def simplify_xml(self, xml_content: str) -> str:
        """
        精简XML内容
        
        Args:
            xml_content: 原始XML内容
            
        Returns:
            str: 精简后的XML内容
        """
        try:
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 精简XML树
            simplified_root = self._simplify_node(root)
            
            # 如果根节点被过滤掉，创建一个空的根节点
            if simplified_root is None:
                simplified_root = ET.Element(root.tag)
                # 保留根节点的基本属性
                for attr_name, attr_value in root.attrib.items():
                    if attr_name in self.key_attributes:
                        simplified_root.set(attr_name, attr_value)
            
            # 转换回字符串
            simplified_xml = ET.tostring(simplified_root, encoding='unicode')
            
            # 格式化输出
            simplified_xml = self._format_xml(simplified_xml)
            
            # 统计精简效果
            original_size = len(xml_content)
            simplified_size = len(simplified_xml)
            reduction_ratio = (original_size - simplified_size) / original_size * 100
            
            logger.info(f"📊 XML精简完成: {original_size} -> {simplified_size} 字符 (减少 {reduction_ratio:.1f}%)")
            
            return simplified_xml
            
        except Exception as e:
            logger.warning(f"⚠️ XML精简失败，使用原始内容: {e}")
            return xml_content
    
    def _simplify_node(self, node: ET.Element) -> Optional[ET.Element]:
        """
        精简单个节点
        
        Args:
            node: XML节点
            
        Returns:
            Optional[ET.Element]: 精简后的节点，如果应该过滤则返回None
        """
        # 检查是否应该保留此节点
        if not self._should_keep_node(node):
            return None
        
        # 创建新节点
        new_node = ET.Element(node.tag)
        
        # 只保留关键属性
        for attr_name, attr_value in node.attrib.items():
            if attr_name in self.key_attributes and attr_value.strip():
                new_node.set(attr_name, attr_value)
        
        # 递归处理子节点
        for child in node:
            simplified_child = self._simplify_node(child)
            if simplified_child is not None:
                new_node.append(simplified_child)
        
        return new_node
    
    def _should_keep_node(self, node: ET.Element) -> bool:
        """
        判断是否应该保留节点（优化版）
        
        Args:
            node: XML节点
            
        Returns:
            bool: 是否保留
        """
        class_name = node.get('class', '')
        text = node.get('text', '').strip()
        content_desc = node.get('content-desc', '').strip()
        resource_id = node.get('resource-id', '').strip()
        clickable = node.get('clickable', 'false') == 'true'
        scrollable = node.get('scrollable', 'false') == 'true'
        enabled = node.get('enabled', 'true') == 'true'
        
        # 过滤掉明显无用的节点
        if not enabled:
            return False
            
        # 过滤掉无用的容器类（除非有特殊属性）
        if (class_name in self.useless_classes and 
            not text and not content_desc and not resource_id and 
            not clickable and not scrollable):
            return False
        
        # 保留条件（优先级排序）：
        # 1. 有文本内容且不为空
        if text and len(text) > 0:
            return True
        
        # 2. 有内容描述且不为空
        if content_desc and len(content_desc) > 0:
            return True
        
        # 3. 可点击的元素
        if clickable:
            return True
        
        # 4. 可滚动的元素
        if scrollable:
            return True
        
        # 5. 有资源ID的重要元素
        if resource_id and class_name in self.important_classes:
            return True
        
        # 6. 特殊状态的节点（选中、勾选等）
        if (node.get('selected') == 'true' or 
            node.get('checked') == 'true' or 
            node.get('focused') == 'true'):
            return True
        
        # 7. 重要的组件类型（即使没有文本）
        if class_name in self.important_classes:
            return True
        
        # 8. 有子节点的非容器类
        if len(node) > 0 and class_name not in self.useless_classes:
            # 检查是否有有用的子节点
            for child in node:
                if self._should_keep_node(child):
                    return True
        
        return False
    
    def _format_xml(self, xml_content: str) -> str:
        """
        格式化XML内容，使其更易读
        
        Args:
            xml_content: XML内容
            
        Returns:
            str: 格式化后的XML内容
        """
        # 简单的格式化处理
        xml_content = re.sub(r'><', '>\n<', xml_content)
        
        # 添加缩进
        lines = xml_content.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 减少缩进（结束标签）
            if line.startswith('</'):
                indent_level = max(0, indent_level - 1)
            
            # 添加缩进
            formatted_lines.append('  ' * indent_level + line)
            
            # 增加缩进（开始标签，但不是自闭合标签）
            if line.startswith('<') and not line.startswith('</') and not line.endswith('/>'):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    def get_interactive_elements_summary(self, xml_content: str) -> Dict:
        """
        获取可交互元素摘要
        
        Args:
            xml_content: XML内容
            
        Returns:
            Dict: 可交互元素摘要
        """
        try:
            root = ET.fromstring(xml_content)
            
            summary = {
                'clickable_elements': [],
                'input_elements': [],
                'scrollable_elements': [],
                'text_elements': []
            }
            
            self._collect_interactive_elements(root, summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 获取交互元素摘要失败: {e}")
            return {}
    
    def _collect_interactive_elements(self, node: ET.Element, summary: Dict):
        """
        收集可交互元素
        
        Args:
            node: XML节点
            summary: 摘要字典
        """
        class_name = node.get('class', '')
        text = node.get('text', '').strip()
        content_desc = node.get('content-desc', '').strip()
        resource_id = node.get('resource-id', '').strip()
        bounds = node.get('bounds', '')
        clickable = node.get('clickable', 'false') == 'true'
        scrollable = node.get('scrollable', 'false') == 'true'
        
        # 可点击元素
        if clickable and (text or content_desc or resource_id):
            summary['clickable_elements'].append({
                'text': text,
                'content_desc': content_desc,
                'resource_id': resource_id,
                'bounds': bounds,
                'class': class_name
            })
        
        # 输入元素
        if 'EditText' in class_name:
            summary['input_elements'].append({
                'text': text,
                'content_desc': content_desc,
                'resource_id': resource_id,
                'bounds': bounds
            })
        
        # 可滚动元素
        if scrollable:
            summary['scrollable_elements'].append({
                'class': class_name,
                'resource_id': resource_id,
                'bounds': bounds
            })
        
        # 文本元素
        if text and 'TextView' in class_name:
            summary['text_elements'].append({
                'text': text,
                'bounds': bounds
            })
        
        # 递归处理子节点
        for child in node:
            self._collect_interactive_elements(child, summary)


# 创建全局实例
xml_simplifier = XMLSimplifier()
