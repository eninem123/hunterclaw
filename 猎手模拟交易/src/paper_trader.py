#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易层 (Paper Trader)
单一持仓数据源，所有模块读这个
"""
import json, os, sys
from datetime import datetime
from pathlib import Path

# 单一持仓文件路径
PAPER_PORTFOLIO_FILE = "/root/.openclaw/workspace/猎手模拟交易/paper_positions.json"
STATE_FILE = "/root/.openclaw/workspace/猎手模拟交易/paper_state.json"

def _load():
    p = PAPER_PORTFOLIO_FILE
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {
        "cash": 100000.0,
        "positions": [],
        "total_value": 100000.0,
        "history": [],
        "trade_log": []
    }

def _save(d):
    with open(PAPER_PORTFOLIO_FILE, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _load_state():
    s = STATE_FILE
    if os.path.exists(s):
        with open(s) as f:
            return json.load(f)
    return {
        "today_buys": 0,
        "last_trade_date": "",
        "circuit_breaker": False
    }

def _save_state(d):
    with open(STATE_FILE, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ── 核心接口 ──

def get_portfolio():
    """读取当前模拟持仓（单一数据源）"""
    return _load()

def get_state():
    return _load_state()

def paper_buy(code, name, price, shares, stop_loss, take_profit, signal="manual"):
    """
    模拟买入
    Returns: (success: bool, msg: str)
    """
    d = _load()
    s = _load_state()
    today = datetime.now().strftime("%Y-%m-%d")

    if s.get("circuit_breaker"):
        return False, "熔断中，禁止买入"

    cost = price * shares
    if cost > d["cash"]:
        return False, f"资金不足 ¥{cost:,.2f} > ¥{d['cash']:,.2f}"

    # 清除当日买卖计数
    if s.get("last_trade_date") != today:
        s["today_buys"] = 0
        s["last_trade_date"] = today

    if s["today_buys"] >= 3:
        return False, f"今日买入次数已达上限({s['today_buys']}/3)"

    # 撮合模拟：随机滑点 ±0.5%
    import random
    fill_price = round(price * (1 + random.uniform(-0.005, 0.005)), 2)
    fill_cost = round(fill_price * shares, 2)

    # 扣除资金
    d["cash"] -= fill_cost

    # 追加持仓
    d["positions"].append({
        "code": code,
        "name": name,
        "entry_price": fill_price,
        "shares": shares,
        "cost": fill_cost,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "buy_date": today,
        "buy_time": datetime.now().strftime("%H:%M"),
        "status": "holding",
        "signal": signal
    })

    # 更新总市值
    d["total_value"] = d["cash"] + sum(p["cost"] for p in d["positions"])

    # 记录
    d["history"].append({
        "date": today,
        "action": "BUY",
        "code": code,
        "name": name,
        "price": fill_price,
        "shares": shares,
        "cost": fill_cost,
        "signal": signal
    })
    d.setdefault("trade_log", []).append({
        "time": datetime.now().isoformat(),
        "action": "BUY",
        "code": code,
        "name": name,
        "price": fill_price,
        "shares": shares,
        "note": f"模拟买入 | 信号:{signal}"
    })

    s["today_buys"] += 1
    _save(d)
    _save_state(s)
    return True, f"✅ 模拟买入 {name}({code}) {shares}股 @{fill_price} | 花费¥{fill_cost:,.2f} | 剩余¥{d['cash']:,.2f}"

def paper_sell(code, reason, current_price=None):
    """
    模拟卖出
    Returns: (success: bool, msg: str)
    """
    d = _load()
    today = datetime.now().strftime("%Y-%m-%d")

    for i, pos in enumerate(d["positions"]):
        if pos["code"] == code and pos["status"] == "holding":
            sell_price = current_price or pos["entry_price"]
            sell_value = round(sell_price * pos["shares"], 2)
            pnl = round((sell_price / pos["entry_price"] - 1) * 100, 2)
            pnl_val = round((sell_price - pos["entry_price"]) * pos["shares"], 2)

            # 撮合模拟
            import random
            fill_price = round(sell_price * (1 + random.uniform(-0.003, 0.003)), 2)
            fill_value = round(fill_price * pos["shares"], 2)

            d["cash"] += fill_value
            d["positions"].pop(i)
            d["total_value"] = d["cash"]

            d["history"].append({
                "date": today,
                "action": "SELL",
                "code": code,
                "name": pos["name"],
                "price": fill_price,
                "shares": pos["shares"],
                "cost": pos["cost"],
                "pnl_pct": pnl,
                "pnl_val": pnl_val,
                "reason": reason
            })
            d.setdefault("trade_log", []).append({
                "time": datetime.now().isoformat(),
                "action": "SELL",
                "code": code,
                "name": pos["name"],
                "price": fill_price,
                "shares": pos["shares"],
                "pnl_pct": pnl,
                "note": f"模拟卖出 | 原因:{reason}"
            })

            _save(d)
            return True, f"✅ 模拟卖出 {pos['name']}({code}) {pos['shares']}股 @{fill_price} | {pnl:+.2f}%({pnl_val:+,.0f}元) | 原因:{reason}"

    return False, f"未找到持仓 {code}"

def check_stop_loss(code, current_price):
    """检查止损，返回触发则自动执行"""
    d = _load()
    for pos in d["positions"]:
        if pos["code"] == code and pos["status"] == "holding":
            if current_price <= pos["stop_loss"]:
                return True, pos
    return False, None

def check_take_profit(code, current_price):
    """检查止盈，返回触发则执行"""
    d = _load()
    for pos in d["positions"]:
        if pos["code"] == code and pos["status"] == "holding":
            if current_price >= pos["take_profit"]:
                return True, pos
    return False, None

def get_positions():
    """获取当前持仓列表"""
    return [p for p in _load().get("positions", []) if p.get("status") == "holding"]

def get_cash():
    return _load()["cash"]

def get_total_value():
    d = _load()
    return d["cash"] + sum(p["cost"] for p in d.get("positions", []) if p.get("status") == "holding")

def print_portfolio():
    """打印当前模拟持仓状态"""
    d = _load()
    print(f"\n{'='*50}")
    print(f"模拟账户 | 总市值: ¥{d['total_value']:,.2f} | 现金: ¥{d['cash']:,.2f}")
    positions = [p for p in d.get("positions", []) if p.get("status") == "holding"]
    if positions:
        for p in positions:
            print(f"  {p['code']} {p['name']} {p['shares']}股 @ ¥{p['entry_price']} | 止损:{p['stop_loss']} 止盈:{p['take_profit']}")
    else:
        print("  空仓")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    print_portfolio()
