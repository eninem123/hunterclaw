#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

PORTFOLIO_FILE = '/root/.openclaw/workspace/猎手模拟交易/持仓.json'
REPORT_FILE = '/root/.openclaw/workspace/猎手模拟交易/持仓报告.md'

with open(PORTFOLIO_FILE) as f:
    portfolio = json.load(f)

# 获取现价
import akshare as ak
try:
    df = ak.stock_zh_a_daily(symbol='sz002230', adjust='qfq')
    cur = float(df['close'].iloc[-1])
    date = df['date'].iloc[-1]
except Exception as e:
    cur = 47.64
    date = '2026-04-10'

prices = {'002230': cur}
total_pnl = 0

for pos in portfolio['positions']:
    if pos['status'] == 'holding' and pos['code'] in prices:
        c = prices[pos['code']]
        pos['current_price'] = c
        pnl = (c - pos['entry_price']) * pos['shares']
        pos['pnl_value'] = round(pnl, 2)
        pos['pnl_pct'] = round((c/pos['entry_price']-1)*100, 2)
        total_pnl += pnl

total_value = portfolio['cash'] + sum(p['cost'] for p in portfolio['positions'])

lines = []
lines.append("# 猎手模拟交易持仓报告")
lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | **数据日期**: {date} | **模拟总资产**: ¥{total_value:,.2f}")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 账户概览")
lines.append("")
lines.append("| 项目 | 数值 |")
lines.append("|------|------|")
lines.append(f"| 模拟总资产 | ¥{total_value:,.2f} |")
lines.append(f"| 现金余额 | ¥{portfolio['cash']:,.2f} |")
lines.append(f"| 持仓市值 | ¥{sum(p['cost'] for p in portfolio['positions']):,.2f} |")
pnl_pct = total_pnl/total_value*100 if total_value > 0 else 0
lines.append(f"| 当前总盈亏 | ¥{total_pnl:,.2f} ({pnl_pct:+.2f}%) |")
lines.append(f"| 持仓数量 | {len(portfolio['positions'])}只 |")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 持仓明细")
lines.append("")

for pos in portfolio['positions']:
    if pos['status'] != 'holding':
        continue
    c = pos.get('current_price', pos['entry_price'])
    pnl_val = pos.get('pnl_value', 0)
    pnl_pct = pos.get('pnl_pct', 0)
    emoji = '🟢' if pnl_val >= 0 else '🔴'
    dist_sl = (c/pos['stop_loss']-1)*100
    dist_tp = (pos['take_profit']/c-1)*100

    lines.append(f"### {emoji} {pos['name']}({pos['code']})")
    lines.append("")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 持仓成本 | ¥{pos['entry_price']} |")
    lines.append(f"| 当前价 | ¥{c} |")
    lines.append(f"| 持仓数量 | {pos['shares']}股 |")
    lines.append(f"| 买入日期 | {pos['buy_date']} |")
    lines.append(f"| **浮盈亏** | ¥{pnl_val:,.2f} ({pnl_pct:+.2f}%) |")
    lines.append(f"| 止损价 | ¥{pos['stop_loss']} ({pos['stop_loss_pct']}%) |")
    lines.append(f"| 止盈价 | ¥{pos['take_profit']} ({pos['take_profit_pct']}%) |")
    lines.append(f"| 距止损 | {dist_sl:+.1f}% |")
    lines.append(f"| 距止盈 | {dist_tp:+.1f}% |")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("## 信号检查")
lines.append("")

has_signal = False
for pos in portfolio['positions']:
    if cur <= pos['stop_loss']:
        lines.append(f"🔴 【止损信号】{pos['name']} 现价¥{cur} <= 止损价¥{pos['stop_loss']}，亏损{pos.get('pnl_pct',0):.2f}%！")
        has_signal = True
    elif cur >= pos['take_profit']:
        lines.append(f"🟢 【止盈信号】{pos['name']} 现价¥{cur} >= 止盈价¥{pos['take_profit']}，盈利{pos.get('pnl_pct',0):.2f}%！")
        has_signal = True

if not has_signal:
    lines.append("✅ 暂无触发止损止盈信号，继续持有")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 交易历史")
lines.append("")
for h in reversed(portfolio['history'][-10:]):
    if h['action'] == 'BUY':
        lines.append(f"- [{h['date']}] 🟢 买入 **{h['name']}** {h['shares']}股 @{h['price']}")
    else:
        reason = h.get('reason', '')
        lines.append(f"- [{h['date']}] 🔴 卖出 **{h['name']}** 原因: {reason}")

lines.append("")
lines.append("---")
lines.append("*本报告仅供参考，不构成投资建议。*")

report_text = '\n'.join(lines)
print(report_text)

with open(REPORT_FILE, 'w') as f:
    f.write(report_text)
