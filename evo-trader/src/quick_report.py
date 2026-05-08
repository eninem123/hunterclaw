#!/usr/bin/env python3
"""快速生成进化日报（从现有状态）"""
import json
import sys
from datetime import datetime
from pathlib import Path

data_dir = Path("/root/.openclaw/workspace/猎手模拟交易/evo-trader/data")
state_file = data_dir / "evolution_state.json"
results_dir = data_dir / "results"

# 读取状态
with open(state_file, 'r', encoding='utf-8') as f:
    state = json.load(f)

strategies = state.get('strategies', [])
strategies.sort(key=lambda x: x.get('fitness', 0), reverse=True)

# 读取市场数据
market_return = 0.0
try:
    index_cache = data_dir / "quotes" / "000300.parquet"
    if index_cache.exists():
        import pandas as pd
        mkt_df = pd.read_parquet(index_cache)
        if len(mkt_df) >= 5:
            mkt_df = mkt_df.tail(5)
            market_return = (mkt_df['close'].iloc[-1] - mkt_df['close'].iloc[0]) / mkt_df['close'].iloc[0]
except Exception as e:
    pass

report = {
    'date': datetime.now().strftime('%Y-%m-%d'),
    'time': datetime.now().strftime('%H:%M:%S'),
    'market_return': market_return,
    'total_strategies': len(strategies),
    'best_strategy': None,
    'top_strategies': [],
    'evolution_stats': {
        'elite_kept': 3,
        'new_generated': len(strategies) - 3
    }
}

# 最优策略
if strategies:
    best = strategies[0]
    report['best_strategy'] = {
        'fitness': best.get('fitness', 0),
        'returns': best.get('returns', 0),
        'sharpe': best.get('sharpe', 0),
        'max_drawdown': best.get('max_drawdown', 0),
        'win_rate': best.get('win_rate', 0),
        'trade_count': best.get('trade_count', 0),
        'gene_params': best.get('gene', {})
    }

# 前5名
for i, s in enumerate(strategies[:5]):
    report['top_strategies'].append({
        'rank': i + 1,
        'fitness': s.get('fitness', 0),
        'returns': s.get('returns', 0),
        'sharpe': s.get('sharpe', 0),
        'max_drawdown': s.get('max_drawdown', 0)
    })

# 保存JSON报告
report_file = results_dir / f"report_{datetime.now().strftime('%Y%m%d')}.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

# 打印文本报告
print("=" * 50)
print("🔬 进化交易系统日报")
print("=" * 50)
print(f"📅 日期: {report['date']} {report['time']}")
print(f"📈 市场表现(沪深300): {report['market_return']:.2%}")
print(f"🧬 策略池: {report['total_strategies']} 个策略")
print()

if report['best_strategy']:
    best = report['best_strategy']
    print("🏆 今日最优策略:")
    print(f"   适应度: {best['fitness']:.4f}")
    print(f"   收益率: {best['returns']:.2%}")
    print(f"   夏普比率: {best['sharpe']:.2f}")
    print(f"   最大回撤: {best['max_drawdown']:.2%}")
    print(f"   胜率: {best['win_rate']:.2%}")
    print(f"   交易次数: {best['trade_count']:.0f}")
    print()
    print("📐 最优策略参数:")
    gene = best['gene_params']
    print(f"   MA快线周期: {gene.get('ma_fast', 0)}")
    print(f"   MA慢线周期: {gene.get('ma_slow', 0)}")
    print(f"   RSI周期: {gene.get('rsi_period', 0)}")
    print(f"   RSI超买: {gene.get('rsi_overbought', 0)}")
    print(f"   RSI超卖: {gene.get('rsi_oversold', 0)}")
    print(f"   仓位比例: {gene.get('position_size', 0):.2%}")
    print(f"   止损比例: {gene.get('stop_loss_pct', 0):.2%}")
    print(f"   止盈比例: {gene.get('take_profit_pct', 0):.2%}")
    print()

print("📊 策略排名（前5）:")
print("-" * 50)
for s in report['top_strategies']:
    print(f"  #{s['rank']}  适应度:{s['fitness']:>8.3f}  收益:{s['returns']:>8.2%}  夏普:{s['sharpe']:>6.2f}  回撤:{s['max_drawdown']:>7.2%}")
print()

print("🔄 进化统计:")
print(f"   保留精英策略: {report['evolution_stats']['elite_kept']}")
print(f"   新生策略: {report['evolution_stats']['new_generated']}")
print()

print("📅 明日计划:")
print("   - 启用最优策略进行模拟交易")
print("   - 继续监控策略表现")
print("   - 收盘后进行下一轮进化")
print()
print(f"✅ 日报已保存至: {report_file}")