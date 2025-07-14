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

def main(output_base_dir="output"):
    """主函数"""
    logger.info("=" * 60)
    logger.info("🤖 手机UI自动化任务执行器")
    logger.info("=" * 60)
    
    # 检查配置已经在config模块的__init__中进行
    logger.info("📋 配置检查完成")
    
    # 创建输出文件夹
    os.makedirs("output_样例", exist_ok=True)
    os.makedirs(output_base_dir, exist_ok=True)
    
    # 获取用户输入的任务
    logger.info("\n请输入您要执行的任务:")
    logger.info("示例: 在京东上查快递")
    logger.info("示例: 打开淘宝搜索手机")
    logger.info("示例: 进入微信发朋友圈")
    
    query = input("\n👤 任务描述: ").strip()
    if not query:
        logger.error("❌ 任务描述不能为空")
        return False
    
    # 询问输出目录（可选）
    if output_base_dir == "output":
        custom_output = input(f"\n📁 输出目录 (默认: {output_base_dir}): ").strip()
        if custom_output:
            output_base_dir = custom_output
            os.makedirs(output_base_dir, exist_ok=True)
    
    logger.info(f"\n🚀 准备执行任务: {query}")
    logger.info(f"📁 输出目录: {os.path.abspath(output_base_dir)}")
    
    # 确认执行
    confirm = input("是否开始执行？(Y/n): ").strip().lower()
    if confirm and confirm in ['n', 'no', '否']:
        logger.info("❌ 任务已取消")
        return False
    
    # 创建任务执行器并运行
    executor = TaskExecutor(output_base_dir=output_base_dir)
    
    try:
        success = executor.run_task(query)
        
        if success:
            logger.info("\n🎉 任务执行完成！")
            logger.info(f"📁 输出文件保存在: {os.path.abspath(executor.output_dir)}")
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
    # 支持命令行参数指定输出目录
    output_dir = "output"
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
        logger.info(f"📁 使用命令行指定的输出目录: {output_dir}")
    
    while True:
        success = main(output_base_dir=output_dir)
        
        # 询问用户是否继续
        continue_choice = input("\n是否继续执行新任务？(y/N): ").strip().lower()
        if continue_choice in ['n', 'no', '否']:
            logger.info("👋 程序已退出")
            break
        
        logger.info("\n🔄 准备执行新任务...")
    
    sys.exit(0 if success else 1)