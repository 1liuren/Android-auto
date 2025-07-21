#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量任务执行器
从Excel文件读取'示例query'列并自动执行任务
"""

import os
import pandas as pd
import json
import time
from datetime import datetime
from src.task_executor import TaskExecutor
from src.config import config
from src.logger_config import get_logger

logger = get_logger(__name__)

class BatchExecutor:
    """批量任务执行器 - 专门处理示例query"""
    
    
    def __init__(self, task_output_base_dir="output"):
        self.excel_file = "验收通过数据/标贝采集需求.xlsx"
        self.target_sheets = ['爱奇艺', '懂车帝', '美团外卖', '饿了么']
        self.output_base_dir = "batch_output_0701"
        self.task_output_base_dir = task_output_base_dir  # 单个任务的输出基础目录
        self.failed_queries = []
        self.success_count = 0
        self.total_count = 0
        self.start_time = None
        
    def run_batch_tasks(self):
        """运行批量任务"""
        logger.info("=" * 60)
        logger.info("🚀 批量任务执行器")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        # 创建输出目录
        os.makedirs(self.output_base_dir, exist_ok=True)
        
        # 检查Excel文件是否存在
        if not os.path.exists(self.excel_file):
            logger.error(f"❌ Excel文件不存在: {self.excel_file}")
            return False
        
        logger.info(f"📊 正在读取Excel文件: {self.excel_file}")
        
        # 读取Excel文件
        try:
            excel_data = pd.ExcelFile(self.excel_file)
            logger.info(f"📋 发现sheets: {excel_data.sheet_names}")
            
            # 检查目标sheets是否存在
            available_sheets = [sheet for sheet in self.target_sheets if sheet in excel_data.sheet_names]
            missing_sheets = [sheet for sheet in self.target_sheets if sheet not in excel_data.sheet_names]
            
            if missing_sheets:
                logger.warning(f"⚠️  以下sheets不存在: {missing_sheets}")
            
            if not available_sheets:
                logger.error("❌ 没有找到任何目标sheets")
                return False
            
            logger.info(f"✅ 将处理以下sheets: {available_sheets}")
            
            # 逐个处理sheet
            for sheet_name in available_sheets:
                self._process_sheet(excel_data, sheet_name)
            
            # 生成执行报告
            self._generate_report()
            
        except Exception as e:
            logger.error(f"❌ 读取Excel文件失败: {e}")
            return False
        
        return True
    
    def _process_sheet(self, excel_data, sheet_name):
        """处理单个sheet"""
        logger.info(f"\n📑 处理sheet: {sheet_name}")
        
        try:
            # 读取sheet数据
            df = pd.read_excel(excel_data, sheet_name=sheet_name)
            logger.info(f"📊 数据行数: {len(df)}")
            logger.info(f"📋 列名: {list(df.columns)}")
            
            # 检查必要的列是否存在
            required_columns = ['示例query']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"❌ 缺少必要的列: {missing_columns}")
                return
            
            # 为这个sheet创建输出目录
            sheet_output_dir = os.path.join(self.output_base_dir, sheet_name)
            os.makedirs(sheet_output_dir, exist_ok=True)
            
            # 提取所有queries（只处理示例query）
            all_queries = self._extract_queries_from_sheet(df)
            logger.info(f"📝 从{sheet_name}提取到 {len(all_queries)} 个示例查询")
            
            # 执行queries
            self._execute_queries(all_queries, sheet_name, sheet_output_dir)
            
        except Exception as e:
            logger.error(f"❌ 处理sheet {sheet_name} 失败: {e}")
    
    def _extract_queries_from_sheet(self, df):
        """从sheet中提取所有queries（只处理示例query）"""
        all_queries = []
        
        for index, row in df.iterrows():
            # 只处理示例query
            example_query = row.get('示例query')
            if pd.notna(example_query) and str(example_query).strip():
                all_queries.append({
                    'query': str(example_query).strip(),
                    'type': '示例query',
                    'row': index + 1
                })
        
        return all_queries
    
    def _execute_queries(self, queries, sheet_name, output_dir):
        """执行一组queries"""
        logger.info(f"\n🔄 开始执行{sheet_name}的{len(queries)}个查询...")
        
        # 创建任务执行器，使用指定的输出基础目录
        executor = TaskExecutor(output_base_dir=self.task_output_base_dir)
        
        # 记录执行结果
        execution_results = []
        
        for i, query_info in enumerate(queries, 1):
            query = query_info['query']
            query_type = query_info['type']
            row_num = query_info['row']
            
            logger.info(f"\n--- 执行查询 {i}/{len(queries)} ---")
            logger.info(f"📝 查询: {query}")
            logger.info(f"📋 类型: {query_type}")
            logger.info(f"📍 来源行: {row_num}")
            
            # 每个任务独立跟踪启动的应用
            task_launched_apps = set()
            
            try:
                # 执行任务
                start_time = time.time()
                success = executor.run_task(query)
                end_time = time.time()
                execution_time = end_time - start_time
                
                # # 提取当前任务启动的应用
                # if hasattr(executor, 'task_data') and executor.task_data:
                #     self._extract_launched_apps(executor.task_data, task_launched_apps)
                
                # 按query创建目标目录（限制文件名长度，避免路径过长）
                safe_query = query[:30].replace('/', '_').replace('\\', '_').replace(':', '_').replace('|', '_')
                target_output = os.path.join(output_dir, f"{safe_query}")
                
                # 移动输出文件到sheet目录
                # 使用executor的实际输出目录而不是硬编码的"output"
                original_output = executor.output_dir
                if os.path.exists(original_output):
                    # 如果目标目录存在，先删除
                    if os.path.exists(target_output):
                        import shutil
                        shutil.rmtree(target_output)
                    
                    # 移动目录
                    import shutil
                    shutil.move(original_output, target_output)
                    logger.info(f"📁 输出已保存到: {target_output}")
                
                # 记录结果
                result = {
                    'query': query,
                    'type': query_type,
                    'row': row_num,
                    'success': success,
                    'execution_time': execution_time,
                    'output_dir': target_output,
                    'launched_apps': list(task_launched_apps),  # 记录此任务启动的应用
                    'timestamp': datetime.now().isoformat()
                }
                
                if success:
                    logger.info(f"✅ 查询执行成功，用时 {execution_time:.1f} 秒")
                    self.success_count += 1
                else:
                    logger.error(f"❌ 查询执行失败，用时 {execution_time:.1f} 秒")
                    self.failed_queries.append(query_info)
                
                execution_results.append(result)
                self.total_count += 1
                
                # # 停止当前任务启动的应用，为下一个任务准备
                # logger.info(f"🛑 停止当前任务启动的应用...")
                # if task_launched_apps:
                #     logger.info(f"🎯 当前任务启动了 {len(task_launched_apps)} 个应用: {list(task_launched_apps)}")
                #     executor.device.clean_apps(target_apps=list(task_launched_apps))
                #     logger.info(f"✅ 应用已停止，为下一个任务准备")
                # else:
                #     logger.info("ℹ️  当前任务未启动新应用，执行常规停止")
                #     executor.device.clean_apps()  # 仍然执行停止，确保状态干净
                
                # # 短暂休息，避免设备过热
                # time.sleep(3)
                
            except KeyboardInterrupt:
                logger.warning(f"\n⚠️  用户中断执行")
                # 保存中断前的结果
                self._save_execution_results(execution_results, sheet_name, output_dir)
                raise
            except Exception as e:
                logger.error(f"❌ 执行查询时出错: {e}")
                self.failed_queries.append(query_info)
                self.total_count += 1
                
                # 记录失败结果
                result = {
                    'query': query,
                    'type': query_type,
                    'row': row_num,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                execution_results.append(result)
        
        # 保存执行结果
        self._save_execution_results(execution_results, sheet_name, output_dir)
    
    def _save_execution_results(self, results, sheet_name, output_dir):
        """保存执行结果"""
        results_file = os.path.join(output_dir, f"{sheet_name}_execution_results.json")
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 执行结果已保存: {results_file}")
    
    def _extract_launched_apps(self, task_data: dict, launched_apps: set):
        """从任务数据中提取启动的应用"""
        if not task_data or "data" not in task_data:
            return
        
        for step_data in task_data["data"]:
            if "plan" in step_data:
                plans = step_data["plan"]
                if isinstance(plans, list):
                    for plan in plans:
                        if isinstance(plan, dict):
                            # 检查是否是Open操作
                            if plan.get("type", "").lower() == "open":
                                # 提取应用包名
                                if "package" in plan and plan["package"]:
                                    launched_apps.add(plan["package"])
                                    logger.info(f"📱 记录启动应用: {plan['package']}")
                                # 如果没有包名，尝试从配置中获取
                                elif "app" in plan and plan["app"]:
                                    app_name = plan["app"]
                                    from src.config import config
                                    if app_name in config.app_packages:
                                        package_name = config.app_packages[app_name]
                                        launched_apps.add(package_name)
                                        logger.info(f"📱 记录启动应用: {package_name} (来自{app_name})")
    
    def _generate_report(self):
        """生成执行报告"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        logger.info(f"\n" + "=" * 60)
        logger.info("📊 批量执行报告")
        logger.info("=" * 60)
        logger.info(f"✅ 成功: {self.success_count}")
        logger.info(f"❌ 失败: {len(self.failed_queries)}")
        logger.info(f"📈 总计: {self.total_count}")
        logger.info(f"📊 成功率: {(self.success_count/self.total_count*100):.1f}%" if self.total_count > 0 else "0%")
        logger.info(f"⏰ 总用时: {total_time/60:.1f} 分钟")
        logger.info(f"⚡ 平均每个查询: {total_time/self.total_count:.1f} 秒" if self.total_count > 0 else "0 秒")
        
        if self.failed_queries:
            logger.info(f"\n❌ 失败的查询:")
            for i, query_info in enumerate(self.failed_queries, 1):
                logger.info(f"  {i}. {query_info['query']} (类型: {query_info['type']})")
        
        # 保存报告
        report = {
            'summary': {
                'total': self.total_count,
                'success': self.success_count,
                'failed': len(self.failed_queries),
                'success_rate': (self.success_count/self.total_count*100) if self.total_count > 0 else 0
            },
            'failed_queries': self.failed_queries,
            'timestamp': datetime.now().isoformat()
        }
        
        report_file = os.path.join(self.output_base_dir, "batch_execution_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 详细报告已保存: {report_file}")

def main(task_output_base_dir="output"):
    """主函数"""
    try:
        logger.info("🤖 批量任务执行器启动")
        logger.info("📋 目标sheets: 爱奇艺, 懂车帝, 美团外卖, 饿了么")
        logger.info("📝 只处理'示例query'列的查询")
        logger.info("⚠️  注意: 请确保设备已连接且屏幕保持亮起")
        logger.info(f"📁 单个任务输出基础目录: {os.path.abspath(task_output_base_dir)}")
        
        # 让用户选择执行模式
        logger.info("\n📋 执行选项:")
        logger.info("1. 全部执行 (爱奇艺 + 懂车帝 + 美团外卖 + 饿了么)")
        logger.info("2. 选择特定sheets")
        logger.info("3. 只执行一个sheet进行测试")
        
        choice = input("\n请选择 (1/2/3): ").strip()
        
        batch_executor = BatchExecutor(task_output_base_dir=task_output_base_dir)
        
        if choice == "2":
            # 让用户选择sheets
            available_sheets = ['爱奇艺', '懂车帝', '美团外卖', '饿了么']
            logger.info("\n可选择的sheets:")
            for i, sheet in enumerate(available_sheets, 1):
                logger.info(f"{i}. {sheet}")
            
            selected = input("\n请输入要执行的sheet序号(用逗号分隔，如: 1,3): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in selected.split(',')]
                batch_executor.target_sheets = [available_sheets[i] for i in indices if 0 <= i < len(available_sheets)]
                logger.info(f"✅ 已选择: {batch_executor.target_sheets}")
            except:
                logger.error("❌ 输入格式错误，使用默认全部sheets")
        
        elif choice == "3":
            # 测试模式，只执行第一个sheet
            sheet_name = input("\n请输入要测试的sheet名称 (爱奇艺/懂车帝/美团外卖/饿了么): ").strip()
            if sheet_name in ['爱奇艺', '懂车帝', '美团外卖', '饿了么']:
                batch_executor.target_sheets = [sheet_name]
                logger.info(f"🧪 测试模式: 将只执行 {sheet_name} 的示例查询")
            else:
                logger.error("❌ 无效的sheet名称")
                return
        
        logger.info(f"\n📋 执行计划:")
        logger.info(f"   目标sheets: {batch_executor.target_sheets}")
        logger.info(f"   处理列: '示例query'")
        logger.info(f"   输出目录: {batch_executor.output_base_dir}")
        
        confirm = input("\n是否开始执行？(y/N): ").strip().lower()
        if confirm in ['n', 'no', '否']:
            logger.info("❌ 任务已取消")
            return
        
        success = batch_executor.run_batch_tasks()
        
        if success:
            logger.info("\n🎉 批量任务执行完成！")
        else:
            logger.error("\n❌ 批量任务执行失败")
            
    except KeyboardInterrupt:
        logger.warning(f"\n⚠️  用户中断批量执行")
    except Exception as e:
        logger.error(f"\n❌ 批量执行出错: {e}")

if __name__ == "__main__":
    # 支持命令行参数指定单个任务的输出基础目录
    import sys
    task_output_dir = "output"
    if len(sys.argv) > 1:
        task_output_dir = sys.argv[1]
        logger.info(f"📁 使用命令行指定的任务输出目录: {task_output_dir}")
    
    main(task_output_base_dir=task_output_dir) 