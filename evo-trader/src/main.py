#!/usr/bin/env python3
"""
进化交易系统 - 主程序
"""
import os
import sys
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from data_fetcher_v2 import DataFetcherV2 as DataFetcher
    print("✅ 使用数据获取模块 v2 (腾讯API)")
except ImportError:
    from data_fetcher import DataFetcher
    print("⚠️ 使用数据获取模块 v1 (akshare)")
from strategy_gene import StrategyGene, StrategyPool
from backtest import BacktestRunner

class EvolutionTrader:
    """进化交易主控制器"""
    
    def __init__(self, data_dir="data", initial_capital=100000):
        self.data_dir = Path(data_dir)
        self.initial_capital = initial_capital
        
        # 初始化组件
        self.fetcher = DataFetcher(str(self.data_dir))
        self.pool = StrategyPool(pool_size=20)
        self.runner = BacktestRunner(self.fetcher, initial_capital)
        
        # 状态文件
        self.state_file = self.data_dir / "evolution_state.json"
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    def initialize(self):
        """初始化系统"""
        print("🔧 初始化进化交易系统...")
        
        # 更新数据
        print("📊 更新行情数据...")
        self.fetcher.update_all_data()
        
        # 初始化策略池
        print("🧬 初始化策略池...")
        if self.state_file.exists():
            self.pool.load_from_file(self.state_file)
            print(f"  从文件加载 {len(self.pool.strategies)} 个策略")
        else:
            self.pool.initialize_random()
            print(f"  生成 {len(self.pool.strategies)} 个随机策略")
        
        # 获取股票池用于测试
        self.stock_pool = [s['code'] for s in self.fetcher.stock_pool[:15]]  # 用前15只股票测试
        print(f"  使用 {len(self.stock_pool)} 只股票进行策略测试")
        
        print("✅ 初始化完成")
    
    def evaluate_strategies(self):
        """评估所有策略"""
        print("\n📈 开始策略评估...")
        
        # 获取策略基因
        genes = [s['gene'] for s in self.pool.strategies]
        
        # 批量测试策略
        results = self.runner.batch_test_strategies(self.stock_pool, genes)
        
        # 更新策略池适应度
        for i, result in enumerate(results):
            if i < len(self.pool.strategies):
                self.pool.update_fitness(
                    self.pool.strategies[i]['id'],
                    result['fitness'],
                    result['returns'],
                    result['sharpe'],
                    result['max_drawdown'],
                    result['win_rate'],
                    result['trade_count']
                )
        
        # 保存状态
        self.pool.save_to_file(self.state_file)
        
        print(f"✅ 策略评估完成，共测试 {len(results)} 个策略")
        
        return results
    
    def evolve(self):
        """执行进化操作"""
        print("\n🧬 执行策略进化...")
        
        # 按适应度排序
        self.pool.strategies.sort(key=lambda x: x['fitness'], reverse=True)
        
        # 显示当前最优策略
        best = self.pool.get_best_strategy()
        if best:
            print(f"🏆 当前最优策略:")
            print(f"  适应度: {best['fitness']:.4f}")
            print(f"  收益率: {best['returns']:.2%}")
            print(f"  夏普比率: {best['sharpe']:.2f}")
            print(f"  最大回撤: {best['max_drawdown']:.2%}")
            print(f"  胜率: {best['win_rate']:.2%}")
            print(f"  交易次数: {best['trade_count']}")
        
        # 执行进化
        self.pool.evolve(elite_count=3, mutation_rate=0.15)
        
        # 保存进化后状态
        self.pool.save_to_file(self.state_file)
        
        print(f"✅ 进化完成，淘汰弱策略，生成新策略")
        
        return self.pool.strategies
    
    def generate_report(self):
        """生成日报"""
        print("\n📋 生成进化日报...")
        
        # 按适应度排序
        self.pool.strategies.sort(key=lambda x: x['fitness'], reverse=True)
        
        # 获取市场数据
        market_df = self.fetcher.get_market_data(5)
        if market_df is not None and len(market_df) > 0:
            market_return = (market_df['close'].iloc[-1] - market_df['close'].iloc[0]) / market_df['close'].iloc[0]
        else:
            market_return = 0.0
        
        # 构建报告
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'market_return': market_return,
            'total_strategies': len(self.pool.strategies),
            'best_strategy': None,
            'top_strategies': [],
            'evolution_stats': {
                'elite_kept': 3,
                'new_generated': len(self.pool.strategies) - 3
            }
        }
        
        # 最优策略详情
        best = self.pool.get_best_strategy()
        if best:
            report['best_strategy'] = {
                'fitness': best['fitness'],
                'returns': best['returns'],
                'sharpe': best['sharpe'],
                'max_drawdown': best['max_drawdown'],
                'win_rate': best['win_rate'],
                'trade_count': best['trade_count'],
                'gene_params': best['gene'].to_dict()
            }
        
        # 前5名策略
        for i, s in enumerate(self.pool.strategies[:5]):
            report['top_strategies'].append({
                'rank': i + 1,
                'fitness': s['fitness'],
                'returns': s['returns'],
                'sharpe': s['sharpe'],
                'max_drawdown': s['max_drawdown']
            })
        
        # 保存报告
        report_file = self.results_dir / f"report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成可读的报告文本
        text_report = self._format_text_report(report)
        
        print("✅ 日报生成完成")
        
        return text_report, report
    
    def _format_text_report(self, report):
        """格式化文本报告"""
        lines = []
        lines.append("🔬 进化交易系统日报")
        lines.append(f"日期: {report['date']} {report['time']}")
        lines.append("=" * 40)
        
        lines.append(f"📈 市场表现: {report['market_return']:.2%}")
        lines.append(f"🧬 策略池: {report['total_strategies']} 个策略")
        lines.append("")
        
        if report['best_strategy']:
            best = report['best_strategy']
            lines.append("🏆 今日最优策略:")
            lines.append(f"  适应度: {best['fitness']:.4f}")
            lines.append(f"  收益率: {best['returns']:.2%}")
            lines.append(f"  夏普比率: {best['sharpe']:.2f}")
            lines.append(f"  最大回撤: {best['max_drawdown']:.2%}")
            lines.append(f"  胜率: {best['win_rate']:.2%}")
            lines.append(f"  交易次数: {best['trade_count']}")
            lines.append("")
        
        lines.append("📊 策略排名（前5）:")
        for s in report['top_strategies']:
            lines.append(f"  {s['rank']}. 适应度:{s['fitness']:.3f} 收益:{s['returns']:.2%} 夏普:{s['sharpe']:.2f}")
        
        lines.append("")
        lines.append("🔄 进化统计:")
        lines.append(f"  保留精英策略: {report['evolution_stats']['elite_kept']}")
        lines.append(f"  新生策略: {report['evolution_stats']['new_generated']}")
        
        lines.append("")
        lines.append("📅 明日计划:")
        lines.append("  - 启用最优策略进行模拟交易")
        lines.append("  - 继续监控策略表现")
        lines.append("  - 收盘后进行下一轮进化")
        
        return "\n".join(lines)
    
    def run_daily_cycle(self):
        """运行每日完整周期"""
        print("=" * 60)
        print("🚀 启动进化交易每日周期")
        print("=" * 60)
        
        # 1. 初始化
        self.initialize()
        
        # 2. 评估策略
        results = self.evaluate_strategies()
        
        # 3. 进化
        evolved = self.evolve()
        
        # 4. 生成报告
        report_text, report_data = self.generate_report()
        
        print("\n" + "=" * 60)
        print("✅ 每日周期完成")
        print("=" * 60)
        
        return report_text

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='进化交易系统')
    parser.add_argument('--init', action='store_true', help='初始化系统')
    parser.add_argument('--eval', action='store_true', help='评估策略')
    parser.add_argument('--evolve', action='store_true', help='执行进化')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--daily', action='store_true', help='运行完整每日周期')
    parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    
    args = parser.parse_args()
    
    # 创建进化交易器
    trader = EvolutionTrader(initial_capital=args.capital)
    
    if args.init:
        trader.initialize()
    
    if args.eval:
        trader.evaluate_strategies()
    
    if args.evolve:
        trader.evolve()
    
    if args.report:
        report_text, _ = trader.generate_report()
        print(report_text)
    
    if args.daily:
        report = trader.run_daily_cycle()
        print("\n" + report)
    
    # 如果没有指定任何参数，运行完整周期
    if not any([args.init, args.eval, args.evolve, args.report, args.daily]):
        print("进化交易系统")
        print("使用 --daily 运行完整每日周期")
        print("使用 --init 初始化系统")
        print("使用 --report 生成报告")
        print("使用 --capital 设置初始资金（默认10万）")

if __name__ == "__main__":
    main()