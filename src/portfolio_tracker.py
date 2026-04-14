#!/usr/bin/env python3
"""
猎手模拟交易持仓追踪系统
- 记录持仓、买入价、止损/止盈线
- 自动计算浮盈浮亏
- 监测止损止盈信号
- 生成每日报告
"""

import json
import os
from datetime import datetime
from pathlib import Path

PORTFOLIO_FILE = "/root/.openclaw/workspace/猎手模拟交易/持仓.json"
REPORT_FILE = "/root/.openclaw/workspace/猎手模拟交易/持仓报告.md"
LOG_FILE = "/root/.openclaw/workspace/猎手模拟交易/log.txt"

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {"cash": 100000, "positions": [], "total_value": 100000, "history": []}

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

def buy(portfolio, code, name, price, shares, stop_loss_pct=7, take_profit_pct=15):
    """买入"""
    cost = price * shares
    if cost > portfolio["cash"]:
        print(f"❌ 现金不足：需要{cost}元，现金{portfolio['cash']}元")
        return False
    
    # 止损止盈价
    stop_loss = round(price * (1 - stop_loss_pct / 100), 2)
    take_profit = round(price * (1 + take_profit_pct / 100), 2)
    
    position = {
        "code": code,
        "name": name,
        "entry_price": price,
        "shares": shares,
        "cost": cost,
        "stop_loss": stop_loss,
        "stop_loss_pct": stop_loss_pct,
        "take_profit": take_profit,
        "take_profit_pct": take_profit_pct,
        "buy_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "holding"
    }
    portfolio["positions"].append(position)
    portfolio["cash"] -= cost
    portfolio["total_value"] = portfolio["cash"] + sum(p["cost"] for p in portfolio["positions"])
    
    # 记录历史
    portfolio["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": "BUY",
        "code": code,
        "name": name,
        "price": price,
        "shares": shares,
        "cost": cost
    })
    
    save_portfolio(portfolio)
    print(f"✅ 买入成功 {name}({code}) {shares}股 @{price}元")
    print(f"   止损: {stop_loss} (-{stop_loss_pct}%) | 止盈: {take_profit} (+{take_profit_pct}%)")
    return True

def sell(portfolio, code, reason=""):
    """卖出"""
    for i, pos in enumerate(portfolio["positions"]):
        if pos["code"] == code and pos["status"] == "holding":
            portfolio["positions"].pop(i)
            portfolio["cash"] += pos["cost"]  # 简化：按成本计算
            portfolio["total_value"] = portfolio["cash"]
            
            portfolio["history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "SELL",
                "code": code,
                "name": pos["name"],
                "reason": reason,
                "entry_price": pos["entry_price"],
                "cost": pos["cost"]
            })
            
            save_portfolio(portfolio)
            print(f"✅ 卖出 {pos['name']}({code}) 原因: {reason}")
            return True
    print(f"❌ 未找到持仓 {code}")
    return False

def check_signals(portfolio, current_prices):
    """检查止损止盈信号"""
    signals = []
    for pos in portfolio["positions"]:
        if pos["status"] != "holding":
            continue
        code = pos["code"]
        if code not in current_prices:
            continue
        
        cur = current_prices[code]
        entry = pos["entry_price"]
        pnl_pct = (cur / entry - 1) * 100
        pnl_val = (cur - entry) * pos["shares"]
        
        # 止损信号
        if cur <= pos["stop_loss"]:
            signals.append({
                "type": "STOP_LOSS",
                "code": code,
                "name": pos["name"],
                "current": cur,
                "entry": entry,
                "stop_loss": pos["stop_loss"],
                "pnl_pct": round(pnl_pct, 2),
                "pnl_val": round(pnl_val, 2),
                "action": f"建议止损卖出 @{cur} (亏{round(pnl_pct,2)}%)"
            })
        # 止盈信号
        elif cur >= pos["take_profit"]:
            signals.append({
                "type": "TAKE_PROFIT",
                "code": code,
                "name": pos["name"],
                "current": cur,
                "entry": entry,
                "take_profit": pos["take_profit"],
                "pnl_pct": round(pnl_pct, 2),
                "pnl_val": round(pnl_val, 2),
                "action": f"建议止盈卖出 @{cur} (盈{round(pnl_pct,2)}%)"
            })
        # 更新浮盈浮亏
        pos["current_price"] = cur
        pos["pnl_pct"] = round(pnl_pct, 2)
        pos["pnl_value"] = round(pnl_val, 2)
    
    save_portfolio(portfolio)
    return signals

def generate_report(portfolio, current_prices):
    """生成持仓报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 更新浮盈浮亏
    total_pnl = 0
    for pos in portfolio["positions"]:
        if pos["status"] == "holding" and pos["code"] in current_prices:
            cur = current_prices[pos["code"]]
            pos["current_price"] = cur
            pnl = (cur - pos["entry_price"]) * pos["shares"]
            pos["pnl_value"] = round(pnl, 2)
            pos["pnl_pct"] = round((cur / pos["entry_price"] - 1) * 100, 2)
            total_pnl += pnl

    total_value = portfolio["cash"] + sum(p["cost"] for p in portfolio["positions"])
    total_pnl += sum(p.get("pnl_value", 0) for p in portfolio["positions"])
    
    report = f"""# 猎手模拟交易持仓报告
**更新时间**: {now} | **模拟总资产**: ¥{total_value:,.2f}

---

## 📊 账户概览

| 项目 | 数值 |
|------|------|
| 模拟总资产 | ¥{total_value:,.2f} |
| 现金余额 | ¥{portfolio['cash']:,.2f} |
| 持仓市值 | ¥{sum(p['cost'] for p in portfolio['positions']):,.2f} |
| 当前总盈亏 | ¥{total_pnl:,.2f} ({total_pnl/total_value*100:.2f}%) |
| 持仓数量 | {len(portfolio['positions'])}只 |

---

## 📋 持仓明细

"""
    if not portfolio["positions"]:
        report += "*（暂无持仓）*\n"
    else:
        for pos in portfolio["positions"]:
            if pos["status"] != "holding":
                continue
            cur = pos.get("current_price", pos["entry_price"])
            pnl = pos.get("pnl_value", 0)
            pnl_pct = pos.get("pnl_pct", 0)
            emoji = "🟢" if pnl >= 0 else "🔴"
            
            report += f"""### {emoji} {pos['name']}({pos['code']})

| 项目 | 数值 |
|------|------|
| 持仓成本 | ¥{pos['entry_price']} |
| 当前价 | ¥{cur} |
| 持仓数量 | {pos['shares']}股 |
| 买入日期 | {pos['buy_date']} |
| **浮盈亏** | ¥{pnl:,.2f} ({pnl_pct:+.2f}%) |
| 止损价 | ¥{pos['stop_loss']} ({pos['stop_loss_pct']}%) |
| 止盈价 | ¥{pos['take_profit']} ({pos['take_profit_pct']}%) |

"""
    
    report += f"""---

## 📈 交易历史

"""
    if not portfolio["history"]:
        report += "*（暂无交易记录）*\n"
    else:
        for h in reversed(portfolio["history"][-10:]):
            action = h["action"]
            if action == "BUY":
                report += f"- [{h['date']}] 🟢 买入 **{h['name']}** {h['shares']}股 @{h['price']}\n"
            else:
                reason = h.get("reason", "")
                report += f"- [{h['date']}] 🔴 卖出 **{h['name']}** 原因: {reason}\n"
    
    report += f"""
---
*本报告仅供参考，不构成投资建议。*"""
    
    with open(REPORT_FILE, "w") as f:
        f.write(report)
    
    return report, total_pnl

def update_prices(portfolio):
    """从 akshare 获取持仓股票现价"""
    import akshare as ak
    import pandas as pd
    
    codes = [p["code"] for p in portfolio["positions"] if p["status"] == "holding"]
    prices = {}
    
    for code in codes:
        try:
            df = ak.stock_zh_a_daily(symbol=f"sz{code}" if code.startswith("00") else f"sh{code}", adjust="qfq")
            prices[code] = float(df["close"].iloc[-1])
        except:
            pass
    
    return prices

if __name__ == "__main__":
    import sys
    
    portfolio = load_portfolio()
    
    if len(sys.argv) < 2:
        print("用法: python3 持仓追踪.py [buy|sell|report|check|status]")
        print("  buy  代码 名称 价格 股数 [止损%] [止盈%]")
        print("  sell 代码")
        print("  report")
        print("  check")
        print("  status")
        print(f"\n当前持仓: {len(portfolio['positions'])}只")
        print(f"现金: ¥{portfolio['cash']:,.2f}")
        for p in portfolio["positions"]:
            print(f"  {p['name']}({p['code']}) {p['shares']}股 @{p['entry_price']}")
        exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "buy" and len(sys.argv) >= 6:
        code, name, price, shares = sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5])
        stop_loss = float(sys.argv[6]) if len(sys.argv) > 6 else 7
        take_profit = float(sys.argv[7]) if len(sys.argv) > 7 else 15
        buy(portfolio, code, name, price, shares, stop_loss, take_profit)
    
    elif cmd == "sell" and len(sys.argv) >= 3:
        sell(portfolio, sys.argv[2])
    
    elif cmd == "report":
        prices = update_prices(portfolio)
        report, _ = generate_report(portfolio, prices)
        print(report)
    
    elif cmd == "check":
        prices = update_prices(portfolio)
        signals = check_signals(portfolio, prices)
        if signals:
            for s in signals:
                print(f"🚨 {s['type']}: {s['action']}")
        else:
            print("✅ 暂无触发止损止盈信号")
    
    elif cmd == "status":
        prices = update_prices(portfolio)
        _, total_pnl = generate_report(portfolio, prices)
        print(f"📊 当前总盈亏: ¥{total_pnl:,.2f}")
