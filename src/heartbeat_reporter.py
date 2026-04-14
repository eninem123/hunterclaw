#!/usr/bin/env python3
"""持仓汇报生成器 - 腾讯实时行情（快）"""
import sys, json, os, urllib.request
from datetime import datetime

PORTFOLIO_FILE = '/root/.openclaw/workspace/猎手模拟交易/持仓.json'
REPORT_FILE = '/root/.openclaw/workspace/猎手模拟交易/持仓报告.md'

def get_realtime_price(code):
    """腾讯行情接口，秒级响应"""
    prefix = 'sz' if code.startswith(('00', '30')) else 'sh'
    url = f'https://qt.gtimg.cn/q={prefix}{code}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            text = r.read().decode('gbk')
            parts = text.split('~')
            if len(parts) > 32:
                return {
                    'price': float(parts[3]),
                    'prev_close': float(parts[4]),
                    'open': float(parts[5]),
                    'high': float(parts[33]) if parts[33] else float(parts[3]),
                    'low': float(parts[34]) if parts[34] else float(parts[3]),
                    'volume': int(parts[6]) if parts[6] else 0,
                    'time': parts[30] + ' ' + parts[31] if len(parts) > 31 else '',
                }
    except:
        pass
    return None

with open(PORTFOLIO_FILE) as f:
    portfolio = json.load(f)

# 获取现价
price_map = {}
info_map = {}
for pos in portfolio['positions']:
    if pos['status'] != 'holding':
        continue
    info = get_realtime_price(pos['code'])
    if info:
        price_map[pos['code']] = info['price']
        info_map[pos['code']] = info
    else:
        price_map[pos['code']] = pos['entry_price']

# 计算盈亏
total_pnl = 0
for pos in portfolio['positions']:
    if pos['status'] == 'holding' and pos['code'] in price_map:
        c = price_map[pos['code']]
        pnl = (c - pos['entry_price']) * pos['shares']
        pos['current_price'] = c
        pos['pnl_value'] = round(pnl, 2)
        pos['pnl_pct'] = round((c/pos['entry_price']-1)*100, 2)
        total_pnl += pnl

total_value = portfolio['cash'] + sum(p['cost'] for p in portfolio['positions'])

# 时段标题
slot = sys.argv[1] if len(sys.argv) > 1 else '持仓'
update_time = datetime.now().strftime('%Y-%m-%d %H:%M')
data_time = list(info_map.values())[0]['time'] if info_map else update_time

lines = []
lines.append(f"# 【{slot}】猎手模拟交易持仓汇报")
lines.append(f"**更新时间**: {update_time} | **行情时间**: {data_time} | **模拟总资产**: ¥{total_value:,.2f}")
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
pnl_pct_all = total_pnl/total_value*100 if total_value > 0 else 0
lines.append(f"| 当前总盈亏 | ¥{total_pnl:,.2f} ({pnl_pct_all:+.2f}%) |")
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
    info = info_map.get(pos['code'], {})

    lines.append(f"### {emoji} {pos['name']}({pos['code']})")
    if info:
        chg = info['price'] - info['prev_close']
        chg_pct = (info['price']/info['prev_close']-1)*100 if info['prev_close'] else 0
        lines.append(f"**实时价**: ¥{info['price']} ({chg:+.2f} {chg_pct:+.2f}%) | 今开: ¥{info['open']} | 最高: ¥{info['high']} | 最低: ¥{info['low']}")
    lines.append("")
    lines.append("| 项目 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 持仓成本 | ¥{pos['entry_price']} |")
    lines.append(f"| 当前价 | ¥{c} |")
    lines.append(f"| 持仓数量 | {pos['shares']}股 |")
    lines.append(f"| 买入日期 | {pos['buy_date']} |")
    lines.append(f"| **浮盈亏** | ¥{pnl_val:,.2f} ({pnl_pct:+.2f}%) |")
    lines.append(f"| 止损价 | ¥{pos['stop_loss']} (-{pos['stop_loss_pct']}%) |")
    lines.append(f"| 止盈价 | ¥{pos['take_profit']} (+{pos['take_profit_pct']}%) |")
    lines.append(f"| 距止损 | {dist_sl:+.1f}% |")
    lines.append(f"| 距止盈 | {dist_tp:+.1f}% |")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("## 信号检测")
lines.append("")

has_signal = False
for pos in portfolio['positions']:
    if pos['status'] != 'holding':
        continue
    c = pos.get('current_price', pos['entry_price'])
    pnl_pct = pos.get('pnl_pct', 0)
    if c <= pos['stop_loss']:
        lines.append(f"🔴 【止损信号】{pos['name']} 现价¥{c} ≤ 止损价¥{pos['stop_loss']}！浮亏{pnl_pct:.2f}%，建议止损！")
        has_signal = True
    elif c >= pos['take_profit']:
        lines.append(f"🟢 【止盈信号】{pos['name']} 现价¥{c} ≥ 止盈价¥{pos['take_profit']}！浮盈{pnl_pct:.2f}%，建议止盈！")
        has_signal = True

if not has_signal:
    lines.append("✅ 暂无触发止损止盈信号，继续持有。")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 交易历史")
lines.append("")
if not portfolio['history']:
    lines.append("*（暂无交易记录）*")
else:
    for h in reversed(portfolio['history'][-10:]):
        if h['action'] == 'BUY':
            lines.append(f"- [{h['date']}] 🟢 买入 **{h['name']}** {h['shares']}股 @{h['price']}")
        else:
            reason = h.get('reason', '')
            lines.append(f"- [{h['date']}] 🔴 卖出 **{h['name']}** 原因: {reason}")

lines.append("")
lines.append("---")
lines.append("*本报告仅供参考，不构成投资建议。*")

report = '\n'.join(lines)
print(report)

with open(REPORT_FILE, 'w') as f:
    f.write(report)
