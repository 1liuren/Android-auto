#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
外部知识库：领域提问与流程指南（可扩展）
使用方法：在识别到相关意图后，将对应领域规则拼接进系统提示词。
本模块提供统一的意图检测与规则拼接接口，便于后续添加新品牌/新领域。
"""

from typing import List, Dict, Any, Optional


def _contains_any(text: str, keywords: List[str]) -> bool:
    if not text:
        return False
    for kw in keywords:
        if kw and kw.lower() in text.lower():
            return True
    return False


# ===== 可扩展关键字配置 =====
ORDERING_HOTWORDS: List[str] = [
    "点餐", "外卖", "到店", "下单", "买", "来一份", "小程序", "订餐", "点杯", "点一杯",
    "饿了么", "美团", "支付宝", "给我买", "给我点", "帮我点", "点份", "我要买", "我要点",
    "来份", "来杯", "订", "叫", "点个", "买个", "来个", "堂食", "自提", "送餐"
]

BRAND_KEYWORDS: Dict[str, List[str]] = {
    "星巴克": ["星巴克", "starbucks", "啡快", "专星送", "星爸爸"],
    "瑞幸": ["瑞幸", "luckin", "小蓝杯", "luckin coffee"],
    "肯德基": ["肯德基", "kfc", "开封菜"],
    "麦当劳": ["麦当劳", "mcdonald", "麦乐送", "金拱门", "m记"],
    "咖啡": [
        "咖啡", "拿铁", "美式", "卡布奇诺", "摩卡", "冷萃", "冰美式",
        "馥芮白", "焦糖玛奇朵", "dirty", "生椰拿铁", "厚乳拿铁", "燕麦拿铁",
        "浓缩", "澳白", "玛奇朵", "可可碎片星冰乐", "抹茶星冰乐"
    ],
}


# ===== 规则构建器（可扩展） =====
def _general_ordering_rules() -> str:
    return (
        "【外部知识-点餐/外卖（通用）】\n"
        "- 目标：通过应用打开品牌官方小程序后，完成从搜索到下单前的流程。\n"
        "\n"
        "【query中的信息约束】\n"
        "- 必需信息（至少包含其一以识别意图，推荐包含品牌）：品牌名（麦当劳、肯德基、星巴克、瑞幸）\n"
        "- 可选信息（尽量包含以减少提问）：\n"
        "  · 取餐方式：外卖、到店\n"
        "  · 地址：与取餐方式搭配使用\n"
        "  · 商品名：比如麦辣鸡腿堡套餐、吉士汉堡包\n"
        "  · 数量：与商品名搭配使用（默认1份）\n"
        "  · 规格：商品规格的自然语言描述（如套餐中的小食/饮料、咖啡的杯型/温度/甜度）\n"
        "\n"
        "【Request优先级规则】（仅提问，不做结构化填充）\n"
        "1. 取餐方式优先：缺少时优先询问\n"
        "2. 商品名次优：有取餐方式但缺商品名时询问\n"
        "3. 规格最后：仅在页面显示为必选项时询问\n"
        "\n"
        "【Request提问模板】\n"
        "- 缺取餐方式：\"请问你要外卖还是到店呢？\"\n"
        "- 缺商品名：\"请问你要购买品牌的什么商品呢？（如：麦辣鸡腿堡套餐）\"\n"
        "- 缺规格：只询问页面首屏展示且为必需项的规格\n"
        "\n"
        "【基本流程】\n"
        "1) Open启动应用并进入搜索\n"
        "2) 搜索品牌并进入官方小程序\n"
        "3) 首页确认取餐方式（询问用户选择）\n"
        "4) 点击用户选择的取餐方式按钮（执行界面操作）\n"
        "5) 选择/搜索商品（必须有商品名）\n"
        "6) 进入商品详情页，根据页面必选规格发起Request\n"
        "7) 加入购物车，核对后在支付确认时输出type=\"End\"\n"
    )


def _coffee_rules() -> str:
    return (
        "【外部知识-咖啡规格】\n"
        "- 咖啡规格选项：\n"
        "  · 杯型：中杯、大杯、超大杯\n"
        "  · 温度：热、冰、少冰、全冰\n"
        "  · 甜度：不加糖、少甜、标准甜\n"
        "- Request原则：\n"
        "  · 进入商品详情页后，根据页面首屏展示的必选规格询问\n"
        "  · 一次只询问页面当前显示的规格项\n"
        "  · 如果页面同时显示多个规格，按\"杯型→温度→甜度\"顺序逐项询问\n"
        "- 示例提问：\n"
        "  · 缺杯型：\"请选择杯型\"\n"
        "  · 缺温度：\"请选择温度\"\n"
        "  · 缺甜度：\"请选择甜度\"\n"
        "- 润色表达：将\"美式咖啡大杯冰\"润色为\"大杯冰美式\"\n"
    )


def _starbucks_rules() -> str:
    return (
        "【外部知识-星巴克】\n"
        "- 取餐方式特殊映射：\n"
        "  · 啡快 = 到店自取\n"
        "  · 专星送 = 外卖配送\n"
        "  · 其他外卖表达：使用外卖服务、立即给我配送、给我送过来、使用专星送服务\n"
        "  · 其他到店表达：堂食、到店取餐、到店就餐、店内自提、我马上到店里\n"
        "- 小程序首页Request：\n"
        "  · 标准提问：\"请问你要啡快（到店）还是专星送（外卖）呢？\"\n"
        "  · 通用提问：\"请问你要外卖还是到店呢？\"\n"
        "- 商品类型：咖啡、茶饮、糕点、轻食等\n"
        "- 规格询问流程：\n"
        "  1) 先确认取餐方式\n"
        "  2) 再确认商品名\n"
        "  3) 最后在商品详情页询问规格（杯型、温度、甜度）\n"
        + _coffee_rules()
    )


def _luckin_rules() -> str:
    return (
        "【外部知识-瑞幸】\n"
        "- 取餐方式：自取、外卖\n"
        "- 商品类型：咖啡、茶饮、轻食等\n"
        + _coffee_rules()
    )


def _kfc_rules() -> str:
    return (
        "【外部知识-肯德基】\n"
        "- 套餐类商品规格：\n"
        "  · 规格大小：中套餐、大套餐\n"
        "  · 饮料：可口可乐、雪碧、乌龙茶、果汁等\n"
        "  · 小食/配餐：薯条、鸡块、玉米杯、沙拉等\n"
        "- Request策略：\n"
        "  · 进入商品详情页后，根据页面显示的必选项询问\n"
        "  · 套餐类商品通常需要选择规格大小和饮料\n"
        "  · 单品类商品可能不需要额外规格\n"
        "- 示例提问：\n"
        "  · \"请选择套餐规格\"\n"
        "  · \"请选择饮料\"\n"
        "  · \"请选择配餐\"\n"
    )


def _mcdonalds_rules() -> str:
    return (
        "【外部知识-麦当劳】\n"
        "- 套餐类商品规格：\n"
        "  · 规格大小：中套餐、大套餐\n"
        "  · 饮料：可口可乐、雪碧、乌龙茶、咖啡、果汁等\n"
        "  · 小食/配餐：薯条、麦乐鸡、玉米杯、苹果片等\n"
        "- Request策略：\n"
        "  · 进入商品详情页后，根据页面显示的必选项询问\n"
        "  · 汉堡套餐通常需要选择规格大小和饮料\n"
        "  · 单品类商品可能不需要额外规格\n"
        "- 示例提问：\n"
        "  · \"请选择套餐规格\"\n"
        "  · \"请选择饮料\"\n"
        "  · \"请选择配餐\"\n"
    )


# 品牌 -> 规则构建器映射（便于扩展）
BRAND_RULE_BUILDERS: Dict[str, Any] = {
    "星巴克": _starbucks_rules,
    "瑞幸": _luckin_rules,
    "肯德基": _kfc_rules,
    "麦当劳": _mcdonalds_rules,
}


def _merge_text_for_detection(query: str, known_slots: Optional[Dict[str, Any]], history_steps: Optional[list]) -> str:
    parts: List[str] = []
    if query:
        parts.append(str(query))
    # 槽位中的品牌、商品等也参与意图判定
    if known_slots:
        brand = known_slots.get("brand")
        item = known_slots.get("item")
        if brand:
            parts.append(str(brand))
        if item:
            parts.append(str(item))
    # 最近一次观察/计划文本也可作为线索
    if history_steps:
        last = history_steps[-1]
        parts.append(str(last.get("observation", "")))
        parts.append(str(last.get("description", "")))
    return "\n".join([p for p in parts if p])


def get_domain_rules_by_intent(
    query: str,
    known_slots: Optional[Dict[str, Any]] = None,
    history_steps: Optional[list] = None,
    step: Optional[int] = None,
) -> str:
    """
    返回需要拼接的领域规则文本：
    - 第一步不返回任何规则（保持原始prompt）；
    - 从第二步开始，若检测到点餐/品牌意图，则返回通用点餐规则 + 品牌/咖啡细则；
    - 便于扩展：新增品牌只需在 BRAND_KEYWORDS 和 BRAND_RULE_BUILDERS 中各加一项。
    """
    # 第1步不注入任何外部规则
    if step is not None and step <= 1:
        return ""

    merged_text = _merge_text_for_detection(query, known_slots, history_steps)
    if not merged_text.strip():
        return ""

    # 未命中点餐类热点词则不注入
    if not _contains_any(merged_text, ORDERING_HOTWORDS + sum(BRAND_KEYWORDS.values(), [])):
        return ""

    rules: List[str] = [_general_ordering_rules()]

    # 收集命中的品牌
    matched_any_brand = False
    for brand_name in ["肯德基", "瑞幸", "星巴克", "麦当劳"]:
        if _contains_any(merged_text, BRAND_KEYWORDS[brand_name]):
            builder = BRAND_RULE_BUILDERS.get(brand_name)
            if builder:
                rules.append(builder())
                matched_any_brand = True

    # 未命中已知品牌，但出现咖啡词汇，则附加咖啡规格规则
    if not matched_any_brand and _contains_any(merged_text, BRAND_KEYWORDS["咖啡"]):
        rules.append(_coffee_rules())

    return "\n".join(rules)


