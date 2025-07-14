#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
常用应用对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox


class CommonAppsDialog:
    """常用应用对话框"""
    
    def __init__(self, parent, gui_app):
        self.parent = parent
        self.gui_app = gui_app
        self.dialog = None
        
        # 常用应用列表
        self.common_apps = {
            "微信": "com.tencent.mm",
            "QQ": "com.tencent.mobileqq",
            "支付宝": "com.eg.android.AlipayGphone",
            "淘宝": "com.taobao.taobao",
            "京东": "com.jingdong.app.mall",
            "抖音": "com.ss.android.ugc.aweme",
            "微博": "com.sina.weibo",
            "网易云音乐": "com.netease.cloudmusic",
            "QQ音乐": "com.tencent.qqmusic",
            "百度地图": "com.baidu.BaiduMap",
            "高德地图": "com.autonavi.minimap",
            "钉钉": "com.alibaba.android.rimet",
            "企业微信": "com.tencent.wework",
            "知乎": "com.zhihu.android",
            "哔哩哔哩": "tv.danmaku.bili",
            "小红书": "com.xingin.xhs",
            "美团": "com.sankuai.meituan",
            "美团外卖": "com.sankuai.meituan.takeoutnew",
            "饿了么": "me.ele.android",
            "滴滴出行": "com.sdu.didi.psnger",
            "爱奇艺": "com.qiyi.video",
            "腾讯视频": "com.tencent.qqlive",
            "优酷": "com.youku.phone",
            "懂车帝": "com.ss.android.auto"
        }
    
    def show(self):
        """显示对话框"""
        # 创建对话框窗口
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("常用应用列表")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 设置窗口位置（居中）
        self._center_window()
        
        # 创建界面
        self._create_dialog_content()
    
    def _center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        
        # 获取窗口尺寸
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        # 获取屏幕尺寸
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_dialog_content(self):
        """创建对话框内容"""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="选择要添加的常用应用", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # 搜索框
        self._create_search_section(main_frame)
        
        # 应用列表
        self._create_app_list(main_frame)
        
        # 按钮区域
        self._create_button_section(main_frame)
    
    def _create_search_section(self, parent):
        """创建搜索区域"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索:").pack(side="left")
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        # 绑定搜索事件
        self.search_var.trace('w', self._on_search_change)
    
    def _create_app_list(self, parent):
        """创建应用列表"""
        # 创建滚动区域
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮事件
        canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 保存引用
        self.canvas = canvas
        
        # 创建应用按钮
        self._create_app_buttons()
    
    def _create_app_buttons(self):
        """创建应用按钮"""
        # 清除现有按钮
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # 获取搜索词
        search_term = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        
        # 过滤应用
        filtered_apps = {}
        for app_name, package_name in self.common_apps.items():
            if (not search_term or 
                search_term in app_name.lower() or 
                search_term in package_name.lower()):
                filtered_apps[app_name] = package_name
        
        # 创建应用条目
        row = 0
        for app_name, package_name in sorted(filtered_apps.items()):
            self._create_app_row(self.scrollable_frame, app_name, package_name, row)
            row += 1
        
        # 如果没有找到应用
        if not filtered_apps:
            no_result_label = ttk.Label(
                self.scrollable_frame, 
                text="没有找到匹配的应用",
                font=("Arial", 10, "italic")
            )
            no_result_label.pack(pady=20)
    
    def _create_app_row(self, parent, app_name, package_name, row):
        """创建单个应用行"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill="x", pady=2, padx=5)
        row_frame.columnconfigure(1, weight=1)
        
        # 应用名称
        name_label = ttk.Label(
            row_frame, 
            text=app_name, 
            width=12, 
            font=("Arial", 10, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # 包名
        package_label = ttk.Label(
            row_frame, 
            text=package_name, 
            font=("Consolas", 9),
            foreground="gray"
        )
        package_label.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        
        # 添加按钮
        add_button = ttk.Button(
            row_frame, 
            text="添加", 
            width=8,
            command=lambda a=app_name, p=package_name: self._add_app(a, p)
        )
        add_button.grid(row=0, column=2, sticky="e")
        
        # 检查是否已存在
        if hasattr(self.gui_app, 'app_packages') and app_name in self.gui_app.app_packages:
            add_button.config(text="已存在", state="disabled")
    
    def _create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x")
        
        # 关闭按钮
        close_button = ttk.Button(
            button_frame, 
            text="关闭", 
            command=self._close_dialog
        )
        close_button.pack(side="right")
        
        # 添加全部按钮
        add_all_button = ttk.Button(
            button_frame, 
            text="添加全部", 
            command=self._add_all_apps
        )
        add_all_button.pack(side="right", padx=(0, 10))
    
    def _on_search_change(self, *args):
        """搜索内容变化时的处理"""
        self._create_app_buttons()
    
    def _on_mousewheel(self, event):
        """鼠标滚轮事件处理"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _add_app(self, app_name, package_name):
        """添加单个应用"""
        try:
            # 检查是否已存在
            if hasattr(self.gui_app, 'app_packages') and app_name in self.gui_app.app_packages:
                if not messagebox.askyesno("确认", f"应用 '{app_name}' 已存在，是否覆盖？", parent=self.dialog):
                    return
            
            # 添加到应用包名映射
            if not hasattr(self.gui_app, 'app_packages'):
                self.gui_app.app_packages = {}
            
            self.gui_app.app_packages[app_name] = package_name
            
            # 更新显示
            if hasattr(self.gui_app, 'config_panel'):
                self.gui_app.config_panel.update_app_package_tree()
            
            # 记录日志
            self.gui_app._log_output(f"✅ 已添加常用应用: {app_name} -> {package_name}")
            
            # 刷新按钮状态
            self._create_app_buttons()
            
        except Exception as e:
            self.gui_app._log_output(f"❌ 添加应用失败: {e}")
            messagebox.showerror("错误", f"添加应用失败: {e}", parent=self.dialog)
    
    def _add_all_apps(self):
        """添加所有应用"""
        if not messagebox.askyesno("确认", "确定要添加所有常用应用吗？", parent=self.dialog):
            return
        
        try:
            if not hasattr(self.gui_app, 'app_packages'):
                self.gui_app.app_packages = {}
            
            added_count = 0
            for app_name, package_name in self.common_apps.items():
                if app_name not in self.gui_app.app_packages:
                    self.gui_app.app_packages[app_name] = package_name
                    added_count += 1
            
            # 更新显示
            if hasattr(self.gui_app, 'config_panel'):
                self.gui_app.config_panel.update_app_package_tree()
            
            # 记录日志
            self.gui_app._log_output(f"✅ 已添加 {added_count} 个常用应用")
            
            # 刷新按钮状态
            self._create_app_buttons()
            
            messagebox.showinfo("成功", f"已添加 {added_count} 个常用应用！", parent=self.dialog)
            
        except Exception as e:
            self.gui_app._log_output(f"❌ 批量添加应用失败: {e}")
            messagebox.showerror("错误", f"批量添加应用失败: {e}", parent=self.dialog)
    
    def _close_dialog(self):
        """关闭对话框"""
        if self.dialog:
            self.dialog.destroy() 