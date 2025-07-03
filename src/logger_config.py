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

def setup_logger(log_level: str = "INFO", log_file: str = None):
    """配置loguru日志系统"""
    
    # 移除默认的处理器
    logger.remove()
    
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
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
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
    
    return logger

def get_logger(name: str = None):
    """获取logger实例"""
    if name:
        return logger.bind(name=name)
    return logger

# 默认日志配置
def init_default_logger():
    """初始化默认日志配置"""
    # 创建logs目录
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成日志文件名（按日期）
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"phone_auto_{today}.log")
    
    # 设置日志
    setup_logger(log_level="INFO", log_file=log_file)
    
    return get_logger("phone_auto")

# 自动初始化
default_logger = init_default_logger() 