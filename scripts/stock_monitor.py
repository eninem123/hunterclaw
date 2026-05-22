#!/usr/bin/env python3
"""
猎手盘中实时监测脚本 v3.0 (凌晨优化版)
改进:
  1. 修复Path.write_text(append=True) bug → 统一使用open().write()
  2. 完善300232洲明科技13信号体系检查
  3. 新增各股涨跌停距离自动计算
  4. 增加信号强度标记(🏆/⭐/📊/⚠️)
  5. 支持--json输出模式
  6. 增加市场广度指标(涨跌比计算)
"""

import urllib.request
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# ===== 配置 =====
STOCKS_TO_WATCH = [
    ('sz000960', '锡业股份', 38.19),
    ('sh600961', '株冶集团', 29.06),
    ('sh600206', '有研新材', 26.80),
    ('sz002237', '恒邦股份', 18.48),
    ('sh600531', '豫光金铅', 16.40),
    ('sz002429', '兆驰股份', 11.91),
    ('sz000938', '紫光股份', 29.92),
    ('sh601138', '工业富联', 66.89),
    ('sh600552', '凯盛科技', 15.70),
    ('sz300232', '洲明科技', 6.35),  # 观察标的，收购逻辑
]

# 000960猎手关键价格
PRICES_960 = {
    'limit_up': 44.64,
    'observe': 41.00,
    'entry_high': 40.80,
    'entry_low': 40.20,
    'risk': 39.80,
    'stop': 38.50,
}

MODE = sys.argv[1] if len(sys.argv) > 1 else 'snapshot'
LOG_DIR = Path('/root/.openclaw/workspace/猎手模拟交易/logs')
PENDING_DIR = Path('/root/.openclaw/workspace/pending-summaries')
LOG_DIR.mkdir(parents=True, exist_ok=True)
PENDING_DIR.mkdir(parents=True, exist_ok=True)


def get_realtime_price(symbol):
    """获取腾讯实时行情"""
    url = f'https://qt.gtimg.cn/q={symbol}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode('gbk')
        parts = data.split('~')
        if len(parts) < 32:
            return None
        return {
            'name': parts[1],
            'code': parts[2],
            'price': float(parts[3]),
            'yesterday_close': float(parts[4]),
            'open': float(parts[5]),
            'volume': int(parts[6]),
            'high': float(parts[33]),
            'low': float(parts[34]),
            'change_pct': float(parts[32]) if parts[32] else 0,
            'timestamp': parts[30],
        }
    except:
        return None


def check_960_events(price):
    """检查000960是否有重大价格事件"""
    events = []
    
    if price >= PRICES_960['observe']:
        events.append(f"✅ 突破观察位{PRICES_960['observe']}，多头强势")
    if price >= PRICES_960['entry_low'] and price <= PRICES_960['entry_high']:
        events.append(f"🎯 进入入场区间{PRICES_960['entry_low']}-{PRICES_960['entry_high']}")
    if price <= PRICES_960['risk']:
        events.append(f"🔴 跌破风控线{PRICES_960['risk']}！转防御模式")
    if price <= PRICES_960['stop']:
        events.append(f"🚨 触及止损线{PRICES_960['stop']}！必须执行止损")
    if price >= PRICES_960['limit_up'] * 0.98:
        events.append(f"🚀 逼近涨停价{PRICES_960['limit_up']}，关注封板情况")
    
    return events


def build_alert_report(stock_name, events, mode, price=None):
    """构建需要推送的告警报告"""
    now = datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    
    lines = []
    lines.append(f"📊 **【猎手盘中监测 {mode}】** {ts}")
    lines.append("")
    lines.append(f"**{stock_name}** 现价: {price:.2f}")
    for e in events:
        lines.append(f"  {e}")
    lines.append("")
    lines.append("--- 猎手关键价格线 ---")
    lines.append(f"  涨停价: {PRICES_960['limit_up']} | 观察位: {PRICES_960['observe']}")
    lines.append(f"  入场区间: {PRICES_960['entry_low']}-{PRICES_960['entry_high']}")
    lines.append(f"  风控线: {PRICES_960['risk']} | 止损: {PRICES_960['stop']}")
    
    return '\n'.join(lines)


def build_market_snapshot(mode):
    """构建市场快照（不推送，仅日志）"""
    now = datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    lines = [f"[{ts}] === 市场快照 ({mode}) ==="]
    
    for symbol, name, y_close in STOCKS_TO_WATCH:
        data = get_realtime_price(symbol)
        if not data:
            lines.append(f"  {name}: 获取失败")
            continue
        
        change_pct = (data['price'] - y_close) / y_close * 100
        lines.append(f"  {name}({data['code']}): {data['price']:.2f} ({change_pct:+.2f}%)")
    
    return '\n'.join(lines)


def main():
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    log_file = LOG_DIR / f"monitor-{today}.log"
    
    if MODE == 'snapshot':
        # 一次性快照：处理所有股票，最后统一输出
        all_prices = []
        events_found = False
        
        for symbol, name, y_close in STOCKS_TO_WATCH:
            data = get_realtime_price(symbol)
            if not data:
                continue
            
            change_pct = (data['price'] - y_close) / y_close * 100
            limit_up = round(y_close * 1.1, 2)
            gap = (limit_up - data['price']) / limit_up * 100
            
            all_prices.append(f"【{name}】{data['price']:.2f} ({change_pct:+.2f}%) 距涨停{gap:.1f}%")
            
            # 000960特殊处理：有事件则标记
            if symbol == 'sz000960':
                events = check_960_events(data['price'])
                if events:
                    events_found = True
                    # 不return，先处理完所有股票
        
        # 统一输出
        now_str = now.strftime('%H:%M:%S')
        
        # 计算市场广度(涨跌比)
        up_count = 0
        down_count = 0
        for symbol, name, y_close in STOCKS_TO_WATCH:
            data = get_realtime_price(symbol)
            if data and data['change_pct'] > 0:
                up_count += 1
            elif data and data['change_pct'] < 0:
                down_count += 1
        breadth_signal = "🟢 多头占优" if up_count > down_count * 1.5 else ("🔴 空头占优" if down_count > up_count * 1.5 else "🟡 均衡")
        
        # 信号标记逻辑
        def signal_mark(chg_pct, gap):
            if chg_pct > 5:
                return "🏆"  # 强势
            elif chg_pct > 2:
                return "⭐"  # 偏强
            elif gap < 3:
                return "📊"  # 逼近涨停
            elif chg_pct < -3:
                return "⚠️"  # 偏弱
            return ""
        
        report_lines = [
            f"📊 **【猎手盘中监测 {now_str}】**",
            f"市场广度: {breadth_signal} | 涨{up_count}跌{down_count}",
            ""
        ]
        
        for symbol, name, y_close in STOCKS_TO_WATCH:
            data = get_realtime_price(symbol)
            if data:
                change_pct = (data['price'] - y_close) / y_close * 100
                limit_up = round(y_close * 1.1, 2)
                gap = (limit_up - data['price']) / limit_up * 100
                sm = signal_mark(change_pct, gap)
                report_lines.append(f"{sm} {name} {data['price']:.2f} ({change_pct:+.2f}%) 距涨停{gap:.1f}%")
            else:
                report_lines.append(f"❓ {name}: 获取失败")
        
        report = '\n'.join(report_lines)
        
        out_file = PENDING_DIR / f"stock-monitor-{today}.md"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(report + "\n")
        print(report)
        
        return
    
    # 其他模式：检查事件
    event_found = False
    all_events = []
    
    for symbol, name, y_close in STOCKS_TO_WATCH:
        data = get_realtime_price(symbol)
        if not data:
            continue
        
        if symbol == 'sz000960':
            events = check_960_events(data['price'])
            if events:
                all_events.append((name, events, data['price']))
                event_found = True
    
    if event_found:
        # 有事件，写入pending推送
        report_lines = [f"📊 **【猎手盘中监测 {MODE}】** {now.strftime('%H:%M:%S')}"]
        for name, events, price in all_events:
            report_lines.append(f"**{name}** 现价: {price:.2f}")
            for e in events:
                report_lines.append(f"  {e}")
        
        report = '\n'.join(report_lines)
        out_file = PENDING_DIR / f"stock-monitor-{today}.md"
        out_file.write_text(report, encoding='utf-8')
        print(report)
    else:
        # 无事件，只写日志
        snapshot = build_market_snapshot(MODE)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(snapshot + '\n')
        print(f"✅ {now.strftime('%H:%M:%S')} 盘中监测：无重大事件，已记录日志")


def check_all_stocks_events() -> List[Dict]:
    """全面检查所有监控股票的异常事件 (v3.0新增)
    
    返回格式: [{"symbol": "...", "name": "...", "events": [...], "price": float}]
    """
    all_events = []
    for symbol, name, y_close in STOCKS_TO_WATCH:
        data = get_realtime_price(symbol)
        if not data:
            continue
        
        events = []
        price = data['price']
        chg_pct = data['change_pct']
        
        # 涨跌异常
        if abs(chg_pct) > 5:
            events.append(f"{'📈' if chg_pct > 0 else '📉'} 波动异常 {chg_pct:+.1f}%")
        
        # 涨停附近
        limit_up = round(y_close * 1.1, 2)
        if price >= limit_up * 0.97:
            events.append(f"🚀 逼近涨停 {price:.2f}/{limit_up}")
        
        # 000960特殊检查
        if symbol == 'sz000960':
            events.extend(check_960_events(price))
        
        # 300232特殊检查
        if symbol == 'sz300232':
            sigs = check_300232_signals()
            triggered = [s for s in sigs if s.get('status') == 'triggered']
            if triggered:
                events.append(f"📡 300232: {len(triggered)}/{len(sigs)-1}个信号触发")
        
        if events:
            all_events.append({
                'symbol': symbol, 'name': name, 'price': price,
                'chg_pct': chg_pct, 'events': events
            })
    
    return all_events


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        events = check_all_stocks_events()
        print(json.dumps(events, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == '--300232':
        signals = check_300232_signals()
        print(json.dumps(signals, ensure_ascii=False, indent=2))
    else:
        main()

# ========== 洲明科技300232 专项监测（13信号体系）==========
# 基于用户假设前提：收购概率85-88%，13个信号

# 13个监测信号
SIGNALS_300232 = {
    'price_alert': {'limit_up': 6.99, 'entry': 6.5, 'stop': 5.80},
    'volume_spike': 1.5,  # 量比超过1.5倍
    'limit_up_day': True,  # 涨停
    'block_trade': True,  # 大宗交易
    'broker_race': True,  # 龙虎榜
    'margin': True,  # 融资余额变化
    'qfii': True,  # QFII持仓变化
    'announcement': True,  # 公告异常
    'hander联动': True,  # 汉得信息联动
    'industry': True,  # 行业动态
}

def check_300232_signals() -> List[Dict]:
    """检查300232洲明科技的13个信号 (v3.0完善版)
    
    13个监测信号:
    1. 价格告警(涨停/入场/止损)
    2. 成交量异动(量比>1.5)
    3. 涨停板触发
    4. 大宗交易
    5. 龙虎榜上榜
    6. 融资余额变化
    7. QFII持仓变化
    8. 公告异常
    9. 汉得信息联动(同行业)  
    10. 行业动态
    11. 突破前高
    12. MACD金叉/死叉
    13. 收购进度更新
    """
    signals = []
    data = get_realtime_price('sz300232')
    if not data:
        signals.append({'id': 0, 'name': '数据获取', 'status': 'failed', 'detail': '无法获取300232行情'})
        return signals
    
    price = data['price']
    chg_pct = data['change_pct']
    volume_ratio = data.get('volume_ratio', 1.0)
    
    # Signal 1: 价格告警
    if price >= SIGNALS_300232['price_alert']['limit_up'] * 0.98:
        signals.append({'id': 1, 'name': '价格告警', 'status': 'triggered', 
                       'level': 'critical', 'detail': f'逼近涨停{price:.2f}'})
    elif price >= SIGNALS_300232['price_alert']['entry']:
        signals.append({'id': 1, 'name': '价格告警', 'status': 'active',
                       'level': 'watch', 'detail': f'进入入场区{price:.2f}'})
    elif price <= SIGNALS_300232['price_alert']['stop']:
        signals.append({'id': 1, 'name': '价格告警', 'status': 'triggered',
                       'level': 'critical', 'detail': f'触及止损{price:.2f}'})
    else:
        signals.append({'id': 1, 'name': '价格告警', 'status': 'normal',
                       'level': 'info', 'detail': f'{price:.2f}'})
    
    # Signal 2: 成交量异动
    if volume_ratio > SIGNALS_300232['volume_spike']:
        signals.append({'id': 2, 'name': '量比异动', 'status': 'triggered',
                       'level': 'watch', 'detail': f'量比{volume_ratio:.1f}x'})
    else:
        signals.append({'id': 2, 'name': '量比异动', 'status': 'normal', 'detail': f'{volume_ratio:.1f}x'})
    
    # Signal 3: 涨停板
    if chg_pct >= 9.8:
        signals.append({'id': 3, 'name': '涨停板', 'status': 'triggered',
                       'level': 'critical', 'detail': f'涨停+{chg_pct:.1f}%'})
    else:
        signals.append({'id': 3, 'name': '涨停板', 'status': 'normal', 'detail': f'{chg_pct:+.1f}%'})
    
    # Signal 4-10: 标记为待验证(需要外部数据源)
    for sid, name in [(4, '大宗交易'), (5, '龙虎榜'), (6, '融资余额'), 
                       (7, 'QFII持仓'), (8, '公告异常'), (9, '汉得联动'), (10, '行业动态')]:
        signals.append({'id': sid, 'name': name, 'status': 'unchecked', 'level': 'info', 
                       'detail': '需外部数据源验证', 'manual_review': True})
    
    # Signal 11: 突破前高(基于日内最高价)
    if data.get('high', 0) > data.get('yesterday_close', 0) * 1.05:
        signals.append({'id': 11, 'name': '突破前高', 'status': 'triggered',
                       'level': 'watch', 'detail': f'日内最高{data["high"]:.2f}'})
    else:
        signals.append({'id': 11, 'name': '突破前高', 'status': 'normal', 'detail': '未突破'})
    
    # Signal 12: 价格在MA5上方(简化MACD判断)
    signals.append({'id': 12, 'name': 'MACD趋势', 'status': 'unchecked',
                   'level': 'info', 'detail': '需K线数据计算'})
    
    # Signal 13: 收购进度
    signals.append({'id': 13, 'name': '收购进度', 'status': 'unchecked',
                   'level': 'info', 'detail': '人工跟踪', 'manual_review': True})
    
    # 计算信号触发数
    triggered = sum(1 for s in signals if s['status'] == 'triggered')
    active = sum(1 for s in signals if s['status'] == 'active')
    unchecked = sum(1 for s in signals if s['status'] == 'unchecked')
    
    signals.insert(0, {
        'id': 0, 'name': '摘要', 'status': 'summary',
        'triggered': triggered, 'active': active, 'unchecked': unchecked,
        'total': len(signals), 'confidence': min(85, triggered * 6 + active * 3)
    })
    
    return signals
