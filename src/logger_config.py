#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志配置模块
配置loguru日志系统
"""

import sys
import os
from loguru import logger
from datetime import datetime

class GUILogHandler:
    """GUI日志处理器 - 将loguru日志输出到GUI界面"""
    
    def __init__(self, gui_output_callback=None):
        """
        初始化GUI日志处理器
        
        Args:
            gui_output_callback: GUI输出回调函数，接收格式化的日志消息
        """
        self.gui_output_callback = gui_output_callback
        self.enabled = False
    
    def set_callback(self, callback):
        """设置GUI输出回调函数"""
        self.gui_output_callback = callback
        self.enabled = True
    
    def write(self, message):
        """写入日志消息到GUI"""
        if self.enabled and self.gui_output_callback:
            try:
                # 移除loguru的颜色标记和ANSI转义序列
                clean_message = self._clean_message(message)
                self.gui_output_callback(clean_message)
            except Exception as e:
                # 如果GUI输出失败，至少在控制台显示
                print(f"GUI日志输出失败: {e}")
    
    def _clean_message(self, message):
        """清理日志消息，移除ANSI转义序列"""
        import re
        # 移除ANSI转义序列
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', message).strip()

# 全局GUI处理器实例
gui_handler = GUILogHandler()

def setup_logger(log_level: str = "INFO", log_file: str = None, enable_gui: bool = False):
    """配置loguru日志系统"""
    
    # 移除默认的处理器
    logger.remove()
    
    # 检查是否在PyInstaller的windowed模式下
    is_windowed = getattr(sys, 'frozen', False) and sys.stdout is None
    
    # 控制台输出格式
    console_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 文件输出格式  
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    # GUI输出格式（简化版）
    gui_format = (
        "{time:HH:mm:ss} | "
        "{level: <8} | "
        "{message}"
    )
    
    # 添加控制台处理器（仅在非windowed模式下）
    if not is_windowed and sys.stdout is not None:
        logger.add(
            sys.stdout,
            format=console_format,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    elif not is_windowed and sys.stderr is not None:
        # 如果stdout不可用但不是windowed模式，尝试使用stderr
        logger.add(
            sys.stderr,
            format=console_format,
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 添加GUI处理器（如果启用）
    if enable_gui and gui_handler:
        logger.add(
            gui_handler.write,
            format=gui_format,
            level=log_level,
            colorize=False,  # GUI不需要颜色
            backtrace=False,
            diagnose=False
        )
    
    # 添加文件处理器（如果指定了日志文件或者在windowed模式下）
    if log_file or is_windowed:
        if not log_file:
            # windowed模式下如果没有指定日志文件，创建一个临时的
            import tempfile
            log_file = os.path.join(tempfile.gettempdir(), "phone_auto.log")
        
        try:
            # 确保日志目录存在
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            logger.add(
                log_file,
                format=file_format,
                level=log_level,
                rotation="10 MB",  # 文件大小超过10MB时轮转
                retention="7 days",  # 保留7天的日志
                compression="zip",  # 压缩旧日志
                backtrace=True,
                diagnose=True,
                encoding="utf-8"
            )
        except Exception as e:
            # 如果文件日志也失败了，至少确保有一个基本的处理器
            if is_windowed:
                import tempfile
                fallback_log = os.path.join(tempfile.gettempdir(), "phone_auto_fallback.log")
                try:
                    logger.add(fallback_log, format=file_format, level=log_level)
                except:
                    # 最后的备选方案：添加一个空的处理器
                    pass
    
    # 确保至少有一个处理器，否则添加一个最基本的
    if len(logger._core.handlers) == 0:
        try:
            import tempfile
            fallback_log = os.path.join(tempfile.gettempdir(), "phone_auto_emergency.log")
            logger.add(fallback_log, format=file_format, level=log_level)
        except:
            # 如果所有都失败了，添加一个null处理器
            import io
            logger.add(io.StringIO(), format=file_format, level=log_level)
    
    return logger

def get_logger(name: str = None):
    """获取logger实例"""
    if name:
        return logger.bind(name=name)
    return logger

def setup_gui_logger(gui_output_callback):
    """设置GUI日志输出回调"""
    gui_handler.set_callback(gui_output_callback)

# 默认日志配置
def init_default_logger(enable_gui: bool = False):
    """初始化默认日志配置"""
    log_file = None
    
    try:
        # 获取程序所在目录
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的环境
            app_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境
            app_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.dirname(app_dir)  # 上一级目录
        
        # 创建logs目录
        log_dir = os.path.join(app_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名（按日期）
        today = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"phone_auto_{today}.log")
        
        # 测试是否可以写入
        test_file = os.path.join(log_dir, "test.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
    except Exception as e:
        # 如果无法创建日志文件，只使用控制台输出
        print(f"警告：无法创建日志文件，将只输出到控制台: {e}")
        log_file = None
    
    # 设置日志
    setup_logger(log_level="INFO", log_file=log_file, enable_gui=enable_gui)
    
    return get_logger("phone_auto")

# 自动初始化（开发环境用）
default_logger = init_default_logger(enable_gui=False) 