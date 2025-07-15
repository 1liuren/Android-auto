#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口类 - 现代化版本
"""

import tkinter as tk
from tkinter import ttk, messagebox
import queue
import sys
import os

# 主题支持
try:
    from ttkthemes import ThemedTk
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False

# 统一日志系统
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from src.logger_config import init_default_logger, setup_gui_logger, get_logger

# 导入组件
from .components.control_panel import ControlPanel
from .components.config_panel import ConfigPanel
from .components.output_panel import OutputPanel
from .components.status_bar import StatusBar

# 导入管理器
from .managers.config_manager import ConfigManager
from .managers.task_manager import TaskManager
from .managers.device_manager import DeviceManager

# 导入工具函数
from .utils.ui_helpers import setup_modern_styles, set_buttons_state, open_directory, MODERN_COLORS, create_gradient_canvas


class PhoneAutomationMainWindow:
    """手机自动化工具主窗口 - 现代化版本"""
    
    def __init__(self):
        # 创建主窗口
        self._create_main_window()
        
        # 初始化变量
        self._init_variables()
        
        # 初始化统一日志系统
        self._setup_unified_logging()
        
        # 初始化管理器
        self._init_managers()
        
        # 创建界面
        self._create_widgets()
        
        # 加载初始配置
        self._load_initial_config()
        
        # 启动周期性任务
        self._start_periodic_tasks()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_main_window(self):
        """创建现代化主窗口"""
        if THEMES_AVAILABLE:
            self.root = ThemedTk(theme="arc")
        else:
            self.root = tk.Tk()
        
        self.root.title("🤖 手机自动化工具 v2.0 - 智能控制中心")
        self.root.geometry("1300x950")
        self.root.minsize(1100, 850)
        self.root.configure(bg=MODERN_COLORS['bg_primary'])
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 配置现代化样式
        self.style = setup_modern_styles()
    
    def _init_variables(self):
        """初始化变量"""
        self.current_task = None
        self.output_queue = queue.Queue()
        
        # UI变量（将在组件中初始化）
        self.task_entry = None
        self.execute_button = None
        self.batch_button = None
        self.interrupt_button = None
        self.batch_interrupt_button = None
        self.output_text = None
        self.status_label = None
        self.time_label = None
        self.device_info_label = None
        
        # 配置变量
        self.output_dir_var = None
        self.batch_output_dir_var = None
        self.api_key_var = None
        self.max_steps_var = None
        self.privacy_enabled_var = None
        self.excel_path_var = None
        
        # 统一日志系统
        self.unified_logger = None
        self._gui_log_callback = None
        self.column_var = None
        self.new_app_name_var = None
        self.new_package_name_var = None
        self.device_id_var = None
        
        # Excel相关变量
        self.sheet_vars = {}
        self.available_sheets = []
        self.sheets_container = None
        self.excel_entry = None
        self.column_combo = None
        self.app_package_tree = None
        
        # 应用包名映射
        self.app_packages = {}
    
    def _setup_unified_logging(self):
        """设置统一日志系统"""
        try:
            # 初始化统一日志系统（启用GUI输出）
            self.unified_logger = init_default_logger(enable_gui=True)
            
            # 设置GUI日志回调（将在OutputPanel创建后配置）
            self._gui_log_callback = self._handle_log_message
            
        except Exception as e:
            print(f"初始化统一日志系统失败: {e}")
    
    def _handle_log_message(self, message):
        """处理来自统一日志系统的消息"""
        try:
            # 线程安全地添加到输出队列
            self.output_queue.put(message)
        except Exception as e:
            print(f"处理日志消息失败: {e}")
    
    def _init_managers(self):
        """初始化管理器"""
        self.config_manager = ConfigManager(self)
        self.task_manager = TaskManager(self)
        self.device_manager = DeviceManager(self)
    
    def _create_widgets(self):
        """创建现代化界面组件"""
        # 创建主框架（带现代化背景）
        main_frame = tk.Frame(self.root, bg=MODERN_COLORS['bg_primary'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建标题区域（固定在顶部）
        self._create_title_section(main_frame)
        
        # 创建可滚动的内容区域
        self._create_scrollable_content(main_frame)
        
        # 状态栏（固定在底部）
        self.status_bar = StatusBar(main_frame, self)
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))
    
    def _create_scrollable_content(self, parent):
        """创建现代化可滚动的内容区域"""
        # 创建Canvas和Scrollbar框架
        canvas_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_primary'])
        canvas_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # 创建Canvas（现代化背景）
        self.canvas = tk.Canvas(canvas_frame, bg=MODERN_COLORS['bg_primary'], 
                               highlightthickness=0, relief="flat")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # 创建现代化垂直滚动条
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # 创建可滚动的框架（现代化背景）
        self.scrollable_frame = tk.Frame(self.canvas, bg=MODERN_COLORS['bg_primary'])
        self.canvas_window = self.canvas.create_window(0, 0, anchor="nw", window=self.scrollable_frame)
        
        # 创建主要内容区域
        content_frame = tk.Frame(self.scrollable_frame, bg=MODERN_COLORS['bg_primary'])
        content_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20), padx=10)
        content_frame.columnconfigure(1, weight=1)
        
        # 左侧控制面板
        left_panel_frame = tk.Frame(content_frame, bg=MODERN_COLORS['bg_primary'])
        left_panel_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        left_panel_frame.columnconfigure(0, weight=1)
        
        self.control_panel = ControlPanel(left_panel_frame, self)
        self.control_panel.grid(row=0, column=0, sticky="nsew")
        
        # 右侧配置面板
        right_panel_frame = tk.Frame(content_frame, bg=MODERN_COLORS['bg_primary'])
        right_panel_frame.grid(row=0, column=1, sticky="nsew")
        right_panel_frame.columnconfigure(0, weight=1)
        
        self.config_panel = ConfigPanel(right_panel_frame, self)
        self.config_panel.grid(row=0, column=0, sticky="nsew")
        
        # 底部输出区域
        self.output_panel = OutputPanel(self.scrollable_frame, self)
        self.output_panel.grid(row=1, column=0, sticky="nsew", pady=(20, 0), padx=10)
        
        # 设置GUI日志回调到统一日志系统
        if self._gui_log_callback:
            setup_gui_logger(self._gui_log_callback)
        
        # 配置滚动区域
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.rowconfigure(1, weight=1)
        
        # 绑定滚动事件
        self._bind_scroll_events()
        
        # 更新滚动区域
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _bind_scroll_events(self):
        """绑定滚动事件"""
        def _on_mousewheel(event):
            # 鼠标滚轮滚动
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        # 绑定鼠标进入和离开事件
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # 绑定键盘滚动
        def _on_key_scroll(event):
            if event.keysym == 'Up':
                self.canvas.yview_scroll(-1, "units")
            elif event.keysym == 'Down':
                self.canvas.yview_scroll(1, "units")
            elif event.keysym == 'Page_Up':
                self.canvas.yview_scroll(-1, "pages")
            elif event.keysym == 'Page_Down':
                self.canvas.yview_scroll(1, "pages")
        
        self.root.bind('<Key>', _on_key_scroll)
        self.root.focus_set()
    
    def _on_frame_configure(self, event):
        """当框架尺寸改变时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """当Canvas尺寸改变时更新窗口宽度"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _create_title_section(self, parent):
        """创建现代化标题区域"""
        # 创建渐变背景的标题区域
        title_frame = tk.Frame(parent, bg=MODERN_COLORS['bg_secondary'], 
                              relief="solid", bd=1, height=80)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        title_frame.columnconfigure(1, weight=1)
        title_frame.pack_propagate(False)  # 保持固定高度
        
        # 左侧标题区域
        left_title_frame = tk.Frame(title_frame, bg=MODERN_COLORS['bg_secondary'])
        left_title_frame.pack(side="left", fill="y", padx=20, pady=15)
        
        # 主标题
        title_label = tk.Label(
            left_title_frame, 
            text="🤖 手机自动化工具", 
            font=("Microsoft YaHei UI", 20, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_secondary']
        )
        title_label.pack(anchor="w")
        
        # 副标题已删除，避免显示不完全
        
        # 右侧信息区域
        right_title_frame = tk.Frame(title_frame, bg=MODERN_COLORS['bg_secondary'])
        right_title_frame.pack(side="right", fill="y", padx=20, pady=15)
        
        # 版本标签
        version_frame = tk.Frame(right_title_frame, bg=MODERN_COLORS['bg_secondary'])
        version_frame.pack(anchor="e")
        
        version_label = tk.Label(
            version_frame,
            text="v2.0",
            font=("Arial", 12, "bold"),
            fg=MODERN_COLORS['primary'],
            bg=MODERN_COLORS['bg_secondary']
        )
        version_label.pack(side="right")
        
        # 状态说明已删除，避免显示不完全
    
    def _load_initial_config(self):
        """加载初始配置"""
        try:
            # 加载配置
            self.config_manager.load_config()
            
            # 如果默认Excel文件存在，初始化时刷新信息
            if (hasattr(self, 'excel_path_var') and 
                self.excel_path_var.get() and 
                os.path.exists(self.excel_path_var.get())):
                self.root.after(200, self._initial_excel_refresh)
                
        except Exception as e:
            self._log_output(f"❌ 初始化配置失败: {e}")
    
    def _start_periodic_tasks(self):
        """启动定期任务"""
        # 定期检查输出队列
        self.root.after(100, self._check_output_queue)
        
        # 初始化设备信息刷新
        self.root.after(500, lambda: self.device_manager.refresh_device_info())
    
    def _initial_excel_refresh(self):
        """初始化时刷新Excel信息"""
        if hasattr(self.control_panel, '_refresh_excel_info'):
            self.control_panel._refresh_excel_info()
            
            # 恢复选中的sheets
            if hasattr(self.config_manager, 'gui_config'):
                try:
                    from src.gui_config import gui_config
                    selected_sheets = gui_config.get("selected_sheets", [])
                    for sheet, var in self.sheet_vars.items():
                        var.set(sheet in selected_sheets)
                except:
                    pass
    
    def _check_output_queue(self):
        """检查输出队列"""
        try:
            while True:
                message = self.output_queue.get_nowait()
                if hasattr(self.output_panel, 'append_output'):
                    self.output_panel.append_output(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._check_output_queue)
    
    def _log_output(self, message):
        """输出日志信息（使用统一日志系统）"""
        if self.unified_logger:
            # 使用统一日志系统
            if '✅' in message or '成功' in message:
                self.unified_logger.success(message)
            elif '❌' in message or '错误' in message or '失败' in message:
                self.unified_logger.error(message)
            elif '⚠️' in message or '警告' in message:
                self.unified_logger.warning(message)
            elif '🚀' in message or '开始' in message:
                self.unified_logger.info(message)
            else:
                self.unified_logger.info(message)
        else:
            # 降级到原有方式
            if hasattr(self.output_panel, 'log_message'):
                self.output_panel.log_message(message)
            else:
                print(f"[LOG] {message}")
    
    def _set_buttons_state(self, enabled):
        """设置按钮状态"""
        buttons = []
        if hasattr(self, 'execute_button') and self.execute_button:
            buttons.append(self.execute_button)
        if hasattr(self, 'batch_button') and self.batch_button:
            buttons.append(self.batch_button)
        
        set_buttons_state(buttons, enabled)
    
    def _update_status(self, text, color="black"):
        """更新状态"""
        if hasattr(self.status_bar, 'update_status'):
            self.status_bar.update_status(text, color)
    
    def _ask_open_output(self, output_path):
        """询问是否打开输出目录"""
        if messagebox.askyesno("完成", "任务执行完成！是否打开输出目录？"):
            open_directory(output_path)
    
    def _on_closing(self):
        """窗口关闭时的处理"""
        try:
            # 自动保存配置
            if hasattr(self, 'config_manager'):
                self.config_manager.auto_save_config()
                
        except Exception as e:
            self._log_output(f"⚠️ 退出时保存配置失败: {e}")
        
        # 关闭窗口
        self.root.destroy()
    
    def run(self):
        """运行GUI"""
        # 设置退出时自动保存配置
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 启动主循环
        self.root.mainloop()
    
    def get_root(self):
        """获取根窗口"""
        return self.root


def create_application():
    """创建应用程序实例"""
    # 检查Python版本
    if sys.version_info < (3, 7):
        messagebox.showerror("错误", "需要Python 3.7或更高版本！")
        return None
    
    try:
        app = PhoneAutomationMainWindow()
        return app
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败: {e}")
        return None


def main():
    """主函数"""
    app = create_application()
    if app:
        app.run()


if __name__ == "__main__":
    main() 