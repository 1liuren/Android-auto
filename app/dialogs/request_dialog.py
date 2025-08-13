#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
极简 Request 选择：
- 优先使用模型提供的 options；
- 2 个选项用 askyesno；>2 或 0 个选项用简单输入；
- 不创建自定义窗口，最大化稳定性。
"""

import tkinter as tk
from tkinter import simpledialog, messagebox


def _normalize_options(raw_options):
    if not raw_options:
        return []
    out = []
    for o in raw_options:
        if isinstance(o, dict):
            out.append(str(o.get("text") or o.get("label") or o.get("name") or o))
        else:
            out.append(str(o))
    # 去重保序
    seen = set()
    uniq = []
    for x in out:
        x = x.strip()
        if x and x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def show_request_dialog(parent, question_text: str, options: list | None = None):
    """优先直接选择候选；无候选则输入。
    - 2 个候选：askyesno
    - 其他：askstring，支持编号映射
    """
    opts = _normalize_options(options)
    q = question_text or "请选择"

    # if len(opts) == 2:
    #     res = messagebox.askyesno("请选择", f"{q}\n\n是/否 = {opts[0]} / {opts[1]}", parent=parent)
    #     return {"answer": opts[0] if res else opts[1]}

    hint = "\n\n可选项：\n" + "\n".join(f"- {i+1}. {v}" for i, v in enumerate(opts)) if opts else "\n\n(无候选，可直接输入)"
    ans = simpledialog.askstring("请输入", f"{q}{hint}", parent=parent)
    if not ans:
        return None
    ans = ans.strip()
    if opts and ans.isdigit():
        idx = int(ans)
        if 1 <= idx <= len(opts):
            return {"answer": opts[idx-1]}
    return {"answer": ans}


