#!/usr/bin/env python3
"""
猎手自动交易执行模块 v2.0
- 新策略：市场温度回暖 + 资金流入 → 试探建仓
- 自动执行：买入/卖出信号触发 → 自动模拟成交
- 交易限制：单日≤3次 / 单只≤30% / 熔断禁止买入
"""

import json
import os
from datetime import datetime, date
from pathlib import Path

PORTFOLIO_FILE = "/root/.openclaw/workspace/猎手模拟交易/持仓.json"
STATE_FILE = "/root/.openclaw/workspace/猎手模拟交易/trade_state.json"

# ============ 交易限制常量 ============
MAX_BUYS_PER_DAY = 3      # 单日买入≤3次
MAX_POSITION_PCT = 30     # 单只持仓≤30%
STOP_LOSS_PCT = 5          # 止损-5%（绝对红线）
TAKE_PROFIT_PCT = 10      # 止盈+10%

# ============ 市场温度阈值 ============
TEMPICY_THRESHOLD = 30     # 冰点线（成交额低于此视为冰点）
WARM_THRESHOLD = 50       # 暖意线（高于此可建仓）
VOLUME_GROWTH_MIN = 0.05  # 最小放量幅度（5%）

# ============ 持仓状态管理 ============

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {"cash": 100000, "positions": [], "total_value": 100000, "history": []}

def load_state():
    """加载交易状态（含熔断、日内计数）"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "circuit_breaker": False,   # 熔断标志
        "circuit_reason": "",
        "today_buys": 0,            # 今日买入次数
        "last_trade_date": "",       # 上次交易日期
        "market_temperature": 0,     # 市场温度（0-100）
        "volume_growth": 0,          # 成交量增幅
    }

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def reset_daily_limits(state):
    """新交易日重置日内计数"""
    today = date.today().strftime("%Y-%m-%d")
    if state.get("last_trade_date") != today:
        state["today_buys"] = 0
        state["last_trade_date"] = today
        state["circuit_breaker"] = False
        state["circuit_reason"] = ""
    return state

def get_position_pct(portfolio):
    """计算持仓占比"""
    if portfolio["total_value"] <= 0:
        return {}
    pos_pcts = {}
    for p in portfolio["positions"]:
        if p["status"] == "holding":
            pos_pcts[p["code"]] = p["cost"] / portfolio["total_value"] * 100
    return pos_pcts

# ============ 信号检测 ============

def check_stop_loss(portfolio, current_prices):
    """检查止损信号（-5%绝对红线）"""
    signals = []
    for pos in portfolio["positions"]:
        if pos["status"] != "holding" or pos["code"] not in current_prices:
            continue
        cur = current_prices[pos["code"]]
        entry = pos["entry_price"]
        pnl_pct = (cur / entry - 1) * 100
        if pnl_pct <= -STOP_LOSS_PCT:
            signals.append({
                "type": "STOP_LOSS",
                "code": pos["code"],
                "name": pos["name"],
                "current": cur,
                "entry": entry,
                "pnl_pct": round(pnl_pct, 2),
                "action": f"🔴 止损！{pos['name']} 浮亏{pnl_pct:.2f}%，执行止损"
            })
    return signals

def check_take_profit(portfolio, current_prices):
    """检查止盈信号（+10%）"""
    signals = []
    for pos in portfolio["positions"]:
        if pos["status"] != "holding" or pos["code"] not in current_prices:
            continue
        cur = current_prices[pos["code"]]
        entry = pos["entry_price"]
        pnl_pct = (cur / entry - 1) * 100
        if pnl_pct >= TAKE_PROFIT_PCT:
            signals.append({
                "type": "TAKE_PROFIT",
                "code": pos["code"],
                "name": pos["name"],
                "current": cur,
                "entry": entry,
                "pnl_pct": round(pnl_pct, 2),
                "action": f"🟢 止盈！{pos['name']} 浮盈{pnl_pct:.2f}%，执行止盈"
            })
    return signals

def check_risk_control(portfolio, current_prices):
    """风控强制信号（总资产回撤≥3%时）"""
    total_value = portfolio["cash"] + sum(
        current_prices.get(p["code"], p["entry_price"]) * p["shares"]
        for p in portfolio["positions"] if p["status"] == "holding"
    )
    cost_basis = sum(p["cost"] for p in portfolio["positions"])
    if cost_basis > 0:
        drawdown = (total_value - cost_basis) / cost_basis * 100
        if drawdown <= -3:
            return [{
                "type": "RISK_CONTROL",
                "action": f"🚨 风控熔断！总回撤{drawdown:.2f}%，强制清仓观望"
            }]
    return []

# ============ 自动买入逻辑 ============

def can_buy(state, portfolio, code, cost):
    """检查是否可以买入"""
    state = reset_daily_limits(state)
    
    # 1. 熔断检查
    if state.get("circuit_breaker"):
        print(f"❌ 熔断中，禁止买入: {state.get('circuit_reason', '')}")
        return False
    
    # 2. 日内次数检查
    if state["today_buys"] >= MAX_BUYS_PER_DAY:
        print(f"❌ 今日买入次数已用完（{state['today_buys']}/{MAX_BUYS_PER_DAY}）")
        return False
    
    # 3. 仓位检查
    total_value = portfolio["cash"] + sum(p["cost"] for p in portfolio["positions"])
    if cost > total_value * MAX_POSITION_PCT / 100:
        print(f"❌ 单只仓位超限: 需{cost}元，占比{cost/total_value*100:.1f}% > {MAX_POSITION_PCT}%")
        return False
    
    # 4. 现金检查
    if cost > portfolio["cash"]:
        print(f"❌ 现金不足: 需要{cost}元，现金{portfolio['cash']}元")
        return False
    
    return True

def auto_buy(state, portfolio, code, name, price, shares):
    """自动买入执行"""
    cost = price * shares
    if not can_buy(state, portfolio, code, cost):
        return False
    
    # 更新持仓
    stop_loss = round(price * (1 - STOP_LOSS_PCT / 100), 2)
    take_profit = round(price * (1 + TAKE_PROFIT_PCT / 100), 2)
    
    position = {
        "code": code,
        "name": name,
        "entry_price": price,
        "shares": shares,
        "cost": cost,
        "stop_loss": stop_loss,
        "stop_loss_pct": STOP_LOSS_PCT,
        "take_profit": take_profit,
        "take_profit_pct": TAKE_PROFIT_PCT,
        "buy_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "holding"
    }
    portfolio["positions"].append(position)
    portfolio["cash"] -= cost
    
    # 记录历史
    portfolio["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": "BUY_AUTO",
        "code": code,
        "name": name,
        "price": price,
        "shares": shares,
        "cost": cost,
        "signal": "市场回暖自动建仓"
    })
    
    # 更新日内计数
    state["today_buys"] += 1
    
    save_portfolio(portfolio)
    save_state(state)
    
    print(f"✅ 【自动买入】{name}({code}) {shares}股 @{price}元")
    print(f"   成本: ¥{cost:,.2f} | 止损: ¥{stop_loss} | 止盈: ¥{take_profit}")
    print(f"   今日买入: {state['today_buys']}/{MAX_BUYS_PER_DAY} | 剩余现金: ¥{portfolio['cash']:,.2f}")
    return True

# ============ 自动卖出逻辑 ============

def auto_sell(state, portfolio, code, reason):
    """自动卖出执行"""
    for i, pos in enumerate(portfolio["positions"]):
        if pos["code"] == code and pos["status"] == "holding":
            portfolio["positions"].pop(i)
            portfolio["cash"] += pos["cost"]
            
            portfolio["history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "SELL_AUTO",
                "code": code,
                "name": pos["name"],
                "reason": reason,
                "entry_price": pos["entry_price"],
                "cost": pos["cost"]
            })
            
            save_portfolio(portfolio)
            save_state(state)
            
            print(f"✅ 【自动卖出】{pos['name']}({code}) 原因: {reason}")
            return True
    return False

def trigger_circuit_breaker(state, reason):
    """触发熔断"""
    state["circuit_breaker"] = True
    state["circuit_reason"] = reason
    save_state(state)
    print(f"🚨 【熔断触发】{reason}")

# ============ 市场温度计算 ============

def calc_market_temperature(volume_yesterday, volume_today):
    """
    计算市场温度（0-100）
    基于成交量变化判断市场情绪
    """
    if volume_yesterday <= 0:
        return 50  # 默认中立
    
    growth = (volume_today - volume_yesterday) / volume_yesterday
    
    # 成交额增速 → 温度映射
    if growth < -0.2:
        temp = 20   # 缩量严重，冰点
    elif growth < -0.05:
        temp = 35   # 缩量，偏冷
    elif growth < 0.05:
        temp = 50   # 持平，中立
    elif growth < 0.15:
        temp = 65   # 温和放量，暖意
    elif growth < 0.30:
        temp = 80   # 明显放量，热情
    else:
        temp = 95   # 爆量，极度热情
    
    return temp, growth

# ============ 新策略：判断是否建议建仓 ============

def should_buy(state, market_temperature, volume_growth):
    """
    新策略判断：市场温度回暖 + 资金流入 → 建议建仓
    - market_temperature: 市场温度（0-100）
    - volume_growth: 成交量增速（>0表示放量）
    """
    state = reset_daily_limits(state)
    
    if state.get("circuit_breaker"):
        return False, "熔断中"
    
    if state["today_buys"] >= MAX_BUYS_PER_DAY:
        return False, f"今日买入{state['today_buys']}次已达上限"
    
    # 新策略核心：温度>暖意线 且 放量
    if market_temperature >= WARM_THRESHOLD and volume_growth >= VOLUME_GROWTH_MIN:
        return True, f"市场回暖(温度{market_temperature}℃ + 放量{volume_growth*100:+.1f}%)"
    
    return False, f"市场偏冷(温度{market_temperature}℃)或放量不足"

# ============ 主流水判断 ============

def check_main_money_flow():
    """
    通过涨幅判断主力资金流向
    返回: (market_temp, volume_growth, is_main_inflow)
    """
    try:
        import urllib.request
        
        # 指数行情（东方财富）
        urls = {
            "sh": "https://qt.gtimg.cn/q=sh000001",
            "sz": "https://qt.gtimg.cn/q=sz399001", 
            "cy": "https://qt.gtimg.cn/q=sz399006",
        }
        
        data = {}
        for name, url in urls.items():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    text = r.read().decode("gbk")
                    parts = text.split("~")
                    if len(parts) > 10:
                        price = float(parts[3])
                        prev = float(parts[4])
                        vol = int(parts[6]) if parts[6] else 0
                        data[name] = {"price": price, "prev": prev, "vol": vol}
            except:
                pass
        
        if len(data) < 2:
            return 50, 0, False
        
        # 简单判断：用涨幅代替成交量变化
        avg_chg = sum((d["price"]/d["prev"]-1)*100 for d in data.values()) / len(data)
        
        if avg_chg > 1.0:
            temp = 80  # 强势
        elif avg_chg > 0.3:
            temp = 65  # 暖意
        elif avg_chg > -0.3:
            temp = 50  # 中立
        elif avg_chg > -1.0:
            temp = 35  # 偏冷
        else:
            temp = 20  # 冰点
        
        growth = avg_chg / 5  # 粗略估算
        
        return temp, growth, avg_chg > 0.3
    except Exception as e:
        print(f"获取行情失败: {e}")
        return 50, 0, False

# ============ 主执行流程 ============

def run_auto_trade_cycle():
    """
    每次推演时自动运行的核心逻辑
    1. 获取市场温度
    2. 检查持仓信号（止损/止盈/风控）
    3. 判断是否可建仓
    4. 执行自动操作
    """
    portfolio = load_portfolio()
    state = load_state()
    state = reset_daily_limits(state)
    
    current_prices = {}
    for pos in portfolio["positions"]:
        if pos["status"] == "holding":
            try:
                import urllib.request
                prefix = "sz" if pos["code"].startswith(("00", "30")) else "sh"
                url = f"https://qt.gtimg.cn/q={prefix}{pos['code']}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    text = r.read().decode("gbk")
                    parts = text.split("~")
                    if len(parts) > 3:
                        current_prices[pos["code"]] = float(parts[3])
            except:
                current_prices[pos["code"]] = pos["entry_price"]
    
    results = []
    
    # 1. 检查止损（-5%红线，优先执行）
    for sig in check_stop_loss(portfolio, current_prices):
        results.append(sig["action"])
        auto_sell(state, portfolio, sig["code"], f"止损({sig['pnl_pct']}%)")
    
    # 2. 检查止盈
    for sig in check_take_profit(portfolio, current_prices):
        results.append(sig["action"])
        auto_sell(state, portfolio, sig["code"], f"止盈({sig['pnl_pct']}%)")
    
    # 3. 检查风控
    for sig in check_risk_control(portfolio, current_prices):
        results.append(sig["action"])
        trigger_circuit_breaker(state, sig["action"])
        # 强制清仓
        for pos in list(portfolio["positions"]):
            if pos["status"] == "holding":
                auto_sell(state, portfolio, pos["code"], "风控熔断")
    
    # 4. 判断市场温度
    market_temp, vol_growth, is_main_in = check_main_money_flow()
    state["market_temperature"] = market_temp
    state["volume_growth"] = vol_growth
    
    should, reason = should_buy(state, market_temp, vol_growth)
    
    save_state(state)
    
    return {
        "market_temperature": market_temp,
        "volume_growth": vol_growth,
        "is_main_inflow": is_main_in,
        "can_buy": should,
        "buy_reason": reason,
        "circuit_breaker": state.get("circuit_breaker", False),
        "today_buys": state["today_buys"],
        "signals": results,
        "cash": portfolio["cash"],
        "positions_count": len(portfolio["positions"]),
    }

if __name__ == "__main__":
    result = run_auto_trade_cycle()
    print("\n========== 自动交易检测结果 ==========")
    print(f"市场温度: {result['market_temperature']}℃ (放量{result['volume_growth']*100:+.1f}%)")
    print(f"主力流入: {'是' if result['is_main_inflow'] else '否'}")
    print(f"熔断状态: {'熔断中' if result['circuit_breaker'] else '正常'}")
    print(f"今日买入: {result['today_buys']}/{MAX_BUYS_PER_DAY}次")
    print(f"可建仓: {'是' if result['can_buy'] else '否'} - {result['buy_reason']}")
    print(f"信号: {' '.join(result['signals']) if result['signals'] else '无'}")
    print(f"现金: ¥{result['cash']:,.2f} | 持仓: {result['positions_count']}只")
    print("=========================================")
