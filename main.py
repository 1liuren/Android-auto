#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手机UI自动化任务执行器
主入口文件
"""

import os
import sys
from src.task_executor import TaskExecutor
from src.config import config
from src.logger_config import get_logger

logger = get_logger(__name__)

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🤖 手机UI自动化任务执行器")
    logger.info("=" * 60)
    
    # 检查配置已经在config模块的__init__中进行
    logger.info("📋 配置检查完成")
    
    # 创建输出文件夹
    os.makedirs("output_样例", exist_ok=True)
    
    # 获取用户输入的任务
    logger.info("\n请输入您要执行的任务:")
    logger.info("示例: 在京东上查快递")
    logger.info("示例: 打开淘宝搜索手机")
    logger.info("示例: 进入微信发朋友圈")
    
    query = input("\n👤 任务描述: ").strip()
    if not query:
        logger.error("❌ 任务描述不能为空")
        return False
    
    logger.info(f"\n🚀 准备执行任务: {query}")
    
    # 确认执行
    confirm = input("是否开始执行？(Y/n): ").strip().lower()
    if confirm and confirm in ['n', 'no', '否']:
        logger.info("❌ 任务已取消")
        return False
    
    # 创建任务执行器并运行
    executor = TaskExecutor()
    
    try:
        success = executor.run_task(query)
        
        if success:
            logger.info("\n🎉 任务执行完成！")
            logger.info(f"📁 输出文件保存在: {os.path.abspath('output')}")
        else:
            logger.error("\n❌ 任务执行失败")
            
        return success
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断任务执行")
        logger.info("🧹 正在清理应用...")
        executor.device.clean_apps()
        executor.save_interrupted_task()
        return False
    except Exception as e:
        logger.error(f"\n❌ 任务执行异常: {e}")
        logger.info("🧹 正在清理应用...")
        executor.device.clean_apps()
        return False

if __name__ == "__main__":
    while True:
        success = main()
        
        # 询问用户是否继续
        continue_choice = input("\n是否继续执行新任务？(y/N): ").strip().lower()
        if continue_choice in ['n', 'no', '否']:
            logger.info("👋 程序已退出")
            break
        
        logger.info("\n🔄 准备执行新任务...")
    
    sys.exit(0 if success else 1)