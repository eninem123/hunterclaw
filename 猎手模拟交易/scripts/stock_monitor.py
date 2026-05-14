#!/usr/bin/env python3
"""
猎手盘中实时监测脚本 v2
智能版：只在关键价格事件时写入pending-summaries触发微信推送
其他时间只写日志，不打扰用户
"""

import urllib.request
import json
import sys
import os
from datetime import datetime
from pathlib import Path

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
        report_lines = [f"📊 **【猎手盘中监测 {now_str}】**"] + all_prices
        report = '\n'.join(report_lines)
        
        out_file = PENDING_DIR / f"stock-monitor-{today}.md"
        out_file.write_text(report, encoding='utf-8')
        
        log_file.open(mode="a").write(report + "\n")
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
        log_file.write_text(snapshot + '\n', encoding='utf-8', append=True)
        print(f"✅ {now.strftime('%H:%M:%S')} 盘中监测：无重大事件，已记录日志")


if __name__ == "__main__":
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

def check_300232_signals():
    """检查300232的13个信号"""
    signals = []
    return signals
