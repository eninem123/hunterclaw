#!/usr/bin/env python3
"""
进化交易系统 - 演示脚本
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def run_demo():
    """运行演示"""
    print("🚀 进化交易系统演示")
    print("=" * 60)
    
    # 导入模块
    try:
        from data_fetcher import DataFetcher
        from strategy_gene import StrategyGene, StrategyPool
        from backtest import BacktestEngine
        print("✅ 模块导入成功")
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return
    
    # 1. 测试数据获取
    print("\n1. 📊 测试数据获取...")
    fetcher = DataFetcher("data")
    
    # 获取平安银行数据
    df = fetcher.get_daily_data('000001', 30)
    if df is not None:
        print(f"  获取到平安银行 {len(df)} 天数据")
        print(f"  最新收盘价: ¥{df['close'].iloc[-1]:.2f}")
        print(f"  近期涨跌: {(df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]:.2%}")
    else:
        print("  数据获取失败，使用模拟数据")
        # 创建模拟数据
        import pandas as pd
        import numpy as np
        dates = pd.date_range('2026-01-01', periods=60, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(60) * 2)
        df = pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(100000, 1000000, 60),
            'amount': prices * np.random.randint(100000, 1000000, 60)
        }, index=dates)
    
    # 2. 测试策略基因
    print("\n2. 🧬 测试策略基因...")
    gene1 = StrategyGene.random_gene()
    gene2 = StrategyGene.random_gene()
    
    print(f"  基因1: MA({gene1.ma_fast}/{gene1.ma_slow}) RSI({gene1.rsi_period})")
    print(f"  基因2: MA({gene2.ma_fast}/{gene2.ma_slow}) RSI({gene2.rsi_period})")
    
    # 测试交叉
    child = gene1.crossover(gene2)
    print(f"  子代基因: MA({child.ma_fast}/{child.ma_slow}) RSI({child.rsi_period})")
    
    # 3. 测试回测
    print("\n3. 📈 测试回测引擎...")
    engine = BacktestEngine(initial_capital=100000)
    
    # 运行回测
    metrics = engine.run('000001', df.tail(30), child)
    
    print(f"  回测结果:")
    print(f"    总收益率: {metrics['total_return']:.2%}")
    print(f"    夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"    最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"    胜率: {metrics['win_rate']:.2%}")
    print(f"    交易次数: {metrics['trade_count']}")
    print(f"    最终资金: ¥{metrics['final_capital']:.2f}")
    
    # 显示交易记录
    summary = engine.get_trade_summary()
    if summary['trades']:
        print(f"\n  最近交易记录:")
        for trade in summary['trades']:
            pnl_str = f" 盈亏: ¥{trade['pnl']:.2f}" if trade['pnl'] is not None else ""
            print(f"    {trade['date']} {trade['symbol']} {trade['action']} {trade['shares']}股 @ ¥{trade['price']:.2f}{pnl_str}")
    
    # 4. 测试策略池
    print("\n4. 🏊 测试策略池进化...")
    pool = StrategyPool(pool_size=10)
    pool.initialize_random()
    
    # 设置模拟适应度
    for i, s in enumerate(pool.strategies):
        # 模拟适应度计算
        pool.update_fitness(s['id'], 
                           random.random(),
                           random.uniform(-0.05, 0.2),
                           random.uniform(0, 1.5),
                           random.uniform(0, 0.1),
                           random.uniform(0.4, 0.7),
                           random.randint(3, 20))
    
    # 获取最优策略
    best = pool.get_best_strategy()
    if best:
        print(f"  最优策略适应度: {best['fitness']:.3f}")
        print(f"  最优策略收益率: {best['returns']:.2%}")
    
    # 执行一轮进化
    pool.evolve(elite_count=2, mutation_rate=0.1)
    print(f"  进化完成，策略池更新")
    
    # 5. 完整系统演示
    print("\n5. 🔄 完整系统工作流演示")
    print("   [数据获取] → [策略评估] → [进化优化] → [模拟交易]")
    print("")
    print("   每天收盘后:")
    print("   1. 获取当日市场数据")
    print("   2. 评估所有策略表现")
    print("   3. 淘汰弱策略，进化新策略")
    print("   4. 选择最优策略用于次日交易")
    print("   5. 生成进化日报")
    
    # 6. 展示输出格式
    print("\n6. 📋 日报输出示例:")
    print("=" * 40)
    print("🔬 进化交易系统日报")
    print("日期: 2026-04-16 18:44:00")
    print("-" * 40)
    print("📈 市场表现: +0.34%")
    print("🧬 策略池: 20 个策略")
    print("")
    print("🏆 今日最优策略:")
    print("  适应度: 0.854")
    print("  收益率: +2.3%")
    print("  夏普比率: 1.8")
    print("  最大回撤: -1.2%")
    print("  胜率: 62.5%")
    print("  交易次数: 24")
    print("")
    print("📊 策略排名（前5）:")
    print("  1. 适应度:0.854 收益:+2.3% 夏普:1.8")
    print("  2. 适应度:0.721 收益:+1.8% 夏普:1.5")
    print("  3. 适应度:0.698 收益:+1.5% 夏普:1.3")
    print("  4. 适应度:0.654 收益:+1.2% 夏普:1.2")
    print("  5. 适应度:0.612 收益:+0.9% 夏普:1.0")
    print("")
    print("🔄 进化统计:")
    print("  保留精英策略: 3")
    print("  新生策略: 17")
    print("")
    print("📅 明日计划:")
    print("  - 启用最优策略进行模拟交易")
    print("  - 继续监控策略表现")
    print("  - 收盘后进行下一轮进化")
    print("=" * 40)
    
    print("\n✅ 演示完成")
    print("\n💡 下一步:")
    print("  运行: python src/main.py --daily  (完整每日周期)")
    print("  运行: python src/main.py --init   (初始化系统)")
    print("  运行: python src/main.py --report (生成日报)")

if __name__ == "__main__":
    import random
    random.seed(42)  # 确保演示结果可重复
    run_demo()