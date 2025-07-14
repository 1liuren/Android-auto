#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手机自动化工具 - 新版可视化界面启动文件
基于模块化架构重构，提高代码可读性和可维护性
"""

import sys
import os
from app.main_window import create_application


def main():
    """主函数"""
    print("="*60)
    print("🤖 手机自动化工具 v2.0 - 智能化版本")
    print("="*60)
    print("🚀 正在启动应用...")
    print("📁 项目架构: 模块化设计")
    print()
    print("✨ 新版特性:")
    print("   🎨 全新美化界面设计")
    print("   🔐 隐私保护功能")
    print("   📊 彩色日志显示")
    print("   🛡️ 增强的错误处理")
    print("   📱 优化的设备管理")
    print("   🔧 智能配置管理")
    print("   📈 批量任务执行")
    print("   💾 日志保存功能")
    print()
    print("⏳ 初始化中...")
    
    try:
        app = create_application()
        if app:
            print("✅ 应用启动成功！")
            print("🎉 欢迎使用手机自动化工具 v2.0")
            print("="*60)
            app.run()
        else:
            print("❌ 应用启动失败")
            print("🔧 请检查系统环境和依赖包")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        print("👋 感谢使用，再见！")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        print("🔧 请检查错误信息并重试")
        sys.exit(1)


if __name__ == "__main__":
    main() 