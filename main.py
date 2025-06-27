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

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 手机UI自动化任务执行器")
    print("=" * 60)
    
    # 检查配置
    if not config.validate():
        print("❌ 配置验证失败，程序退出")
        return False
    
    # 创建输出文件夹
    os.makedirs("output", exist_ok=True)
    
    # 获取用户输入的任务
    print("\n请输入您要执行的任务:")
    print("示例: 在京东上查快递")
    print("示例: 打开淘宝搜索手机")
    print("示例: 进入微信发朋友圈")
    
    query = input("\n👤 任务描述: ").strip()
    if not query:
        print("❌ 任务描述不能为空")
        return False
    
    print(f"\n🚀 准备执行任务: {query}")
    
    # 确认执行
    confirm = input("是否开始执行？(y/N): ").strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print("❌ 任务已取消")
        return False
    
    # 创建任务执行器并运行
    executor = TaskExecutor()
    
    try:
        success = executor.run_task(query)
        
        if success:
            print("\n🎉 任务执行完成！")
            print(f"📁 输出文件保存在: {os.path.abspath('output')}")
        else:
            print("\n❌ 任务执行失败")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断任务执行")
        executor.save_interrupted_task()
        return False
    except Exception as e:
        print(f"\n❌ 任务执行异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    input("\n按 Enter 键退出...")
    sys.exit(0 if success else 1) 