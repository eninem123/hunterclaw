#!/usr/bin/env python3
"""进化交易系统 - 每日进化周期（网络离线兼容版）"""
import sys, os, json, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_fetcher import DataFetcher
from strategy_gene import StrategyGene, StrategyPool
from backtest import BacktestRunner
import pandas as pd

def main():
    print('=' * 60)
    print('  # 进化交易系统 | 每日进化引擎')
    print(f'  # {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)

    data_dir = Path('data')
    fetcher = DataFetcher(str(data_dir))
    pool = StrategyPool(pool_size=20)
    runner = BacktestRunner(fetcher, 100000)
    state_file = data_dir / 'evolution_state.json'

    # 1. 初始化
    print('\n## 1. 初始化系统')
    fetcher.update_all_data()

    if state_file.exists():
        pool.load_from_file(state_file)
        print(f'  策略池加载: {len(pool.strategies)} 个策略')
    else:
        pool.initialize_random()
        print(f'  生成随机策略池: {len(pool.strategies)} 个')

    stock_pool = [s['code'] for s in fetcher.stock_pool[:15]]
    print(f'  测试股票池: {len(stock_pool)} 只')
    for c in stock_pool:
        csv_120 = data_dir / 'quotes' / f'{c}_day_120.csv'
        print(f'    {c} 缓存: {"OK" if csv_120.exists() else "MISSING"}')
    print('  [初始化完成]')

    # 2. 评估
    print('\n## 2. 策略评估')
    t0 = time.time()
    # Force cache load to avoid network calls
    for sym in stock_pool[:5]:
        fetcher.get_daily_data(sym, 60)
    genes = [s['gene'] for s in pool.strategies]
    results = runner.batch_test_strategies(stock_pool, genes)
    for i, r in enumerate(results):
        if i < len(pool.strategies):
            pool.update_fitness(
                pool.strategies[i]['id'],
                r['fitness'], r['returns'], r['sharpe'],
                r['max_drawdown'], r['win_rate'], r['trade_count']
            )
    pool.save_to_file(state_file)
    elapsed = time.time() - t0
    print(f'  评估完成: {len(results)} 策略 x {len(stock_pool)} 股票, 耗时 {elapsed:.1f}s')

    # 3. 进化
    print('\n## 3. 策略进化')
    pool.strategies.sort(key=lambda x: x['fitness'], reverse=True)
    best = pool.get_best_strategy()
    if best:
        print(f'  当前最优: fitness={best["fitness"]:.4f}, '
              f'return={best["returns"]:.2%}, sharpe={best["sharpe"]:.2f}, '
              f'mdd={best["max_drawdown"]:.2%}, win_rate={best["win_rate"]:.2%}, '
              f'trades={best["trade_count"]}')

    pool.evolve(elite_count=3, mutation_rate=0.15)
    pool.save_to_file(state_file)
    print('  进化完成 [保留精英3 -> 变异生成17]')

    # 4. 市场参考
    market_return = 0.0
    try:
        mkt_csv = data_dir / 'quotes' / '600519_day_120.csv'
        if mkt_csv.exists():
            mkt_df = pd.read_csv(mkt_csv)
            if len(mkt_df) >= 5:
                mkt_df = mkt_df.tail(5)
                market_return = (mkt_df['close'].iloc[-1] - mkt_df['close'].iloc[0]) / mkt_df['close'].iloc[0]
    except Exception:
        pass

    # 5. 日报
    print('\n## 4. 生成日报')
    pool.strategies.sort(key=lambda x: x['fitness'], reverse=True)
    best = pool.get_best_strategy()

    results_dir = data_dir / 'results'
    results_dir.mkdir(exist_ok=True)

    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'market_return': market_return,
        'total_strategies': len(pool.strategies),
        'tested_stocks': len(stock_pool),
        'evolution_cycles': getattr(pool, 'generation', 1),
        'best_strategy': None,
        'top_strategies': [],
        'evolution_stats': {'elite_kept': 3, 'new_generated': len(pool.strategies) - 3},
    }

    if best:
        report['best_strategy'] = {
            'fitness': float(best['fitness']),
            'returns': float(best['returns']),
            'sharpe': float(best['sharpe']),
            'max_drawdown': float(best['max_drawdown']),
            'win_rate': float(best['win_rate']),
            'trade_count': int(best['trade_count']),
            'gene_params': {k: float(v) if isinstance(v, (int, float)) else str(v)
                           for k, v in best['gene'].to_dict().items()}
        }

    for i, s in enumerate(pool.strategies[:5]):
        report['top_strategies'].append({
            'rank': i + 1,
            'fitness': float(s['fitness']),
            'returns': float(s['returns']),
            'sharpe': float(s['sharpe']),
            'max_drawdown': float(s['max_drawdown'])
        })

    rep_file = results_dir / f'report_{datetime.now().strftime("%Y%m%d")}.json'
    with open(rep_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'  报告保存: {rep_file}')

    # ==================== 输出完整日报 ====================
    print()
    print('#' * 62)
    print('#  ' + '进化交易系统 | 每日进化日报'.center(50) + ' #')
    print('#  ' + f'日期: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'.center(52) + ' #')
    print('#' * 62)
    print()

    print(f'  [市场基准] 近5日参考收益: {market_return:+.2%}')
    print(f'  [策略池]   规模: {report["total_strategies"]} 个策略 | '
          f'测试股票: {report["tested_stocks"]} 只 | '
          f'进化代数: {report["evolution_cycles"]}')
    print()

    if report['best_strategy']:
        b = report['best_strategy']
        print('  ' + '-' * 56)
        print('  |  <<最优策略>>')
        print('  ' + '-' * 56)
        print(f'  |  适应度(Fitness)     {b["fitness"]:>15.4f}')
        print(f'  |  累计收益率(Return)  {b["returns"]:>15.2%}')
        print(f'  |  夏普比率(Sharpe)   {b["sharpe"]:>15.2f}')
        print(f'  |  最大回撤(MDD)      {b["max_drawdown"]:>15.2%}')
        print(f'  |  胜率(Win Rate)     {b["win_rate"]:>15.2%}')
        print(f'  |  交易次数(Trades)    {b["trade_count"]:>15}')
        print('  ' + '-' * 56)
        print()

        if 'gene_params' in b and b['gene_params']:
            print('  |  <<基因参数>>')
            print('  ' + '-' * 56)
            gp = b['gene_params']
            # 按类别分组
            # 均线参数
            ma_keys = [k for k in gp if k.startswith('ma_')]
            print('  |  均线系统:')
            for k in ma_keys:
                print(f'  |    {k:>20} = {gp[k]:>10}')

            rsi_keys = [k for k in gp if k.startswith('rsi_')]
            if rsi_keys:
                print('  |  RSI参数:')
                for k in rsi_keys:
                    print(f'  |    {k:>20} = {gp[k]:>10}')

            w_keys = [k for k in gp if k.startswith('weight_')]
            if w_keys:
                print('  |  信号权重:')
                for k in w_keys:
                    print(f'  |    {k:>20} = {float(gp[k]):>10.4f}')

            misc_keys = [k for k in gp if not k.startswith('ma_') and not k.startswith('rsi_') and not k.startswith('weight_')]
            if misc_keys:
                print('  |  其他参数:')
                for k in misc_keys:
                    print(f'  |    {k:>20} = {float(gp[k]):>10.4f}')
            print('  ' + '-' * 56)
            print()

    # 排名表
    print('  [策略排名 TOP5]')
    print('  ' + '-' * 54)
    print('  | 排名 |  适应度   |  收益率  |  夏普  |  最大回撤 |')
    print('  ' + '-' * 54)
    for s in report['top_strategies']:
        print(f'  |  {s["rank"]:>2}  '
              f'| {s["fitness"]:>8.3f} '
              f'| {s["returns"]:>7.2%} '
              f'| {s["sharpe"]:>5.2f}  '
              f'| {s["max_drawdown"]:>7.2%}  |')
    print('  ' + '-' * 54)
    print()

    # 进化统计
    print('  [进化动力学统计]')
    print('  ' + '-' * 56)
    print(f'  |  保留精英策略(Elite)          {report["evolution_stats"]["elite_kept"]}')
    print(f'  |  新生变异策略(Offspring)      {report["evolution_stats"]["new_generated"]}')
    print(f'  |  策略池更新率                {report["evolution_stats"]["new_generated"]}/{report["total_strategies"]} '
          f'({report["evolution_stats"]["new_generated"]/report["total_strategies"]*100:.0f}%)')
    print(f'  |  进化代数                    {report["evolution_cycles"]}')
    print(f'  |  评估股票数                  {report["tested_stocks"]}')
    print('  ' + '-' * 56)
    print()

    # 明日计划
    print('  [明日进化议程]')
    print('  ' + '-' * 56)
    print('  |  1. 部署最优策略参数 -> 生成模拟交易信号')
    print('  |  2. 监控TOP5策略盘中信号分叉情况')
    print('  |  3. 收盘后触发自动进化迭代')
    print('  |  4. 追踪适应度收敛曲线与策略多样性')
    print('  |  5. 分析策略参数分布漂移趋势')
    print('  ' + '-' * 56)
    print()

    print('#' * 62)
    print('#  ' + '进化周期完成'.center(52) + ' #')
    print('#  ' + f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'.center(52) + ' #')
    print('#' * 62)

if __name__ == '__main__':
    main()
