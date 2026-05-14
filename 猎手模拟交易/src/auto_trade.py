#!/usr/bin/env python3
"""
猎手自动交易执行模块 v3.0
- 【时间硬校验】非交易日/非交易时段直接跳过
- 新策略：市场温度回暖 + 资金流入 → 试探建仓
- 自动执行：买入/卖出信号触发 → 自动模拟成交
- 交易限制：单日≤3次 / 单只≤30% / 熔断禁止买入
"""

import json
import os
import subprocess
import urllib.request
import urllib.parse
import uuid
from datetime import datetime, date
from pathlib import Path

PORTFOLIO_FILE = "/root/.openclaw/workspace/猎手模拟交易/持仓.json"
STATE_FILE = "/root/.openclaw/workspace/猎手模拟交易/trade_state.json"
DELIVERY_QUEUE = "/root/.openclaw/delivery-queue"
WECHAT_ID = "o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat"
ACCOUNT_ID = "665a0448707a-im-bot"

# ============ 微信通知（直接写delivery-queue） ============
def wechat_notify(msg):
    """通过 OpenClaw delivery-queue 实时推送微信消息"""
    try:
        entry = {
            "id": str(uuid.uuid4()),
            "enqueuedAt": int(datetime.now().timestamp() * 1000),
            "channel": "openclaw-weixin",
            "to": WECHAT_ID,
            "accountId": ACCOUNT_ID,
            "payloads": [{"text": msg, "mediaUrls": [], "replyToTag": False,
                          "replyToCurrent": False, "audioAsVoice": False}],
            "retryCount": 0,
            "lastAttemptAt": None
        }
        path = Path(DELIVERY_QUEUE) / f"{entry['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        print(f"[微信通知已推送] {msg[:200]}{'...' if len(msg) > 200 else ''}")
        return {"ok": True}
    except Exception as e:
        print(f"[通知失败] {e}")
        return {"error": str(e)}

# ============ A股时间硬校验（最优先） ============
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def get_real_date():
    """通过外部API获取真实日期，防止时间幻觉"""
    try:
        req = urllib.request.Request(
            "http://worldtimeapi.org/api/timezone/Asia/Shanghai",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return datetime.strptime(data["datetime"][:10], "%Y-%m-%d").date()
    except Exception:
        pass
    # fallback to system date
    try:
        result = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True)
        return datetime.strptime(result.stdout.strip(), "%Y-%m-%d").date()
    except Exception:
        pass
    return date.today()

def is_trading_day():
    """判断今天是否A股交易日"""
    today = get_real_date()
    weekday = today.weekday()
    if weekday >= 5:  # 周六周日
        return False, today, "周末"
    return True, today, "交易日"

def is_trading_hours():
    """判断当前是否在A股交易时段（9:30-11:30 / 13:00-15:00）"""
    now = datetime.now()
    h, m = now.hour, now.minute
    morning = (h == 9 and m >= 30) or (10 <= h <= 11) or (h == 11 and m <= 30)
    afternoon = 13 <= h < 15
    return morning or afternoon

def send_trading_status():
    """发送非交易时段通知"""
    is_trade, real_date, date_type = is_trading_day()
    weekday = WEEKDAY_NAMES[real_date.weekday()]
    now_str = datetime.now().strftime("%H:%M")
    msg = (f"📴 【交易校验】{real_date} {weekday} {now_str}\n"
           f"今日类型：{date_type}\n"
           f"结论：{'非交易日，跳过交易推演' if not is_trade else '交易时段，可执行买卖'}\n\n"
           f"A股交易时间：\n"
           f"  周一~周五 9:30-11:30\n"
           f"  周一~周五 13:00-15:00")
    wechat_notify(msg)

# ============ 交易限制常量 ============
MAX_BUYS_PER_DAY = 3
MAX_POSITION_PCT = 30
STOP_LOSS_PCT = 5
TAKE_PROFIT_PCT = 8   # 与MEMORY保持一致：8%

# ============ 持仓状态管理 ============
def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {"cash": 100000, "positions": [], "total_value": 100000, "history": []}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "circuit_breaker": False, "circuit_reason": "",
        "today_buys": 0, "last_trade_date": "",
        "market_temperature": 0, "volume_growth": 0,
    }

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def reset_daily_limits(state):
    today = date.today().strftime("%Y-%m-%d")
    if state.get("last_trade_date") != today:
        state["today_buys"] = 0
        state["last_trade_date"] = today
        state["circuit_breaker"] = False
        state["circuit_reason"] = ""
    return state

# ============ 信号检测 ============
def check_stop_loss(portfolio, current_prices):
    signals = []
    for pos in portfolio["positions"]:
        if pos["status"] != "holding" or pos["code"] not in current_prices:
            continue
        cur = current_prices[pos["code"]]
        entry = pos["entry_price"]
        pnl_pct = (cur / entry - 1) * 100
        if pnl_pct <= -STOP_LOSS_PCT:
            signals.append({
                "type": "STOP_LOSS", "code": pos["code"], "name": pos["name"],
                "current": cur, "entry": entry, "pnl_pct": round(pnl_pct, 2),
                "action": f"🔴 止损！{pos['name']} 浮亏{pnl_pct:.2f}%"
            })
    return signals

def check_take_profit(portfolio, current_prices):
    signals = []
    for pos in portfolio["positions"]:
        if pos["status"] != "holding" or pos["code"] not in current_prices:
            continue
        cur = current_prices[pos["code"]]
        entry = pos["entry_price"]
        pnl_pct = (cur / entry - 1) * 100
        if pnl_pct >= TAKE_PROFIT_PCT:
            signals.append({
                "type": "TAKE_PROFIT", "code": pos["code"], "name": pos["name"],
                "current": cur, "entry": entry, "pnl_pct": round(pnl_pct, 2),
                "action": f"🟢 止盈！{pos['name']} 浮盈{pnl_pct:.2f}%"
            })
    return signals

def check_risk_control(portfolio, current_prices):
    total_value = portfolio["cash"] + sum(
        current_prices.get(p["code"], p["entry_price"]) * p["shares"]
        for p in portfolio["positions"] if p["status"] == "holding"
    )
    cost_basis = sum(p["cost"] for p in portfolio["positions"])
    if cost_basis > 0:
        drawdown = (total_value - cost_basis) / cost_basis * 100
        if drawdown <= -3:
            return [{"type": "RISK_CONTROL", "action": f"🚨 风控熔断！总回撤{drawdown:.2f}%"}]
    return []

# ============ 自动买入 ============
def can_buy(state, portfolio, code, cost):
    state = reset_daily_limits(state)
    if state.get("circuit_breaker"):
        return False
    if state["today_buys"] >= MAX_BUYS_PER_DAY:
        return False
    total_value = portfolio["cash"] + sum(p["cost"] for p in portfolio["positions"])
    if cost > total_value * MAX_POSITION_PCT / 100:
        return False
    if cost > portfolio["cash"]:
        return False
    return True

from datetime import datetime, date


def _sync_monitor_list(add_code=None, remove_code=None):
    """买入/卖出后同步stock_monitor.py的STOCKS_TO_WATCH列表"""
    monitor_path = "/root/.openclaw/workspace/猎手模拟交易/scripts/stock_monitor.py"
    try:
        with open(monitor_path, 'r') as f:
            lines = f.readlines()
        in_list = False
        new_lines = []
        for line in lines:
            if 'STOCKS_TO_WATCH = [' in line:
                in_list = True
            if in_list and add_code and ('sh'+add_code in line or 'sz'+add_code in line):
                in_list = False
                continue
            if in_list and remove_code and ('sh'+remove_code in line or 'sz'+remove_code in line):
                continue
            new_lines.append(line)
            if in_list and line.strip().startswith('])'):
                in_list = False
        if add_code:
            prefix = 'sh' if add_code.startswith('6') else 'sz'
            entry = f"    ('{prefix}{add_code}', '{remove_code}', 0),\n"
            inserted = False
            result = []
            for l in new_lines:
                result.append(l)
                if not inserted and "])" in l and l.strip() == "])":
                    indent = len(l) - len(l.lstrip())
                    result.insert(-1, ' ' * indent + entry)
                    inserted = True
            new_lines = result
        with open(monitor_path, 'w') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[同步监控列表失败] {e}")


def auto_buy(state, portfolio, code, name, price, shares):
    cost = price * shares
    if not can_buy(state, portfolio, code, cost):
        return False
    stop_loss = round(price * (1 - STOP_LOSS_PCT / 100), 2)
    take_profit = round(price * (1 + TAKE_PROFIT_PCT / 100), 2)
    position = {
        "code": code, "name": name, "entry_price": price, "shares": shares,
        "cost": cost, "stop_loss": stop_loss, "stop_loss_pct": STOP_LOSS_PCT,
        "take_profit": take_profit, "take_profit_pct": TAKE_PROFIT_PCT,
        "buy_date": datetime.now().strftime("%Y-%m-%d"), "status": "holding"
    }
    portfolio["positions"].append(position)
    portfolio["cash"] -= cost
    portfolio["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": "BUY_AUTO", "code": code, "name": name,
        "price": price, "shares": shares, "cost": cost,
        "signal": "市场回暖自动建仓"
    })
    state["today_buys"] += 1
    save_portfolio(portfolio)
    save_state(state)
    msg = (f"📗 【自动买入】\n股票：{name}({code})\n"
           f"价格：¥{price} × {shares}股\n成本：¥{cost:,.2f}\n"
           f"止损：¥{stop_loss} | 止盈：¥{take_profit}\n"
           f"今日买入：{state['today_buys']}/{MAX_BUYS_PER_DAY}次")
    wechat_notify(msg)
    print(f"✅ 【自动买入】{name}({code}) {shares}股 @{price}元")
    print(f"   成本: ¥{cost:,.2f} | 止损: ¥{stop_loss} | 止盈: ¥{take_profit}")
    print(f"   今日买入: {state['today_buys']}/{MAX_BUYS_PER_DAY} | 剩余现金: ¥{portfolio['cash']:,.2f}")
    _sync_monitor_list(add_code=code, remove_code=name)
    return True

# ============ 自动卖出 ============
def auto_sell(state, portfolio, code, reason, current_prices=None):
    _prices = current_prices if current_prices is not None else globals().get('current_prices', {})
    for i, pos in enumerate(portfolio["positions"]):
        if pos["code"] == code and pos["status"] == "holding":
            entry = pos["entry_price"]
            price = _prices.get(code, entry)
            # 卖出结算：按实际卖出价计算
            sell_value = price * pos["shares"]
            portfolio["positions"].pop(i)
            portfolio["cash"] += sell_value  # 按现价结算，不是成本价
            pnl_pct = (price / entry - 1) * 100
            pnl_val = (price - entry) * pos["shares"]
            portfolio["history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "SELL_AUTO", "code": code, "name": pos["name"],
                "reason": reason, "entry_price": entry, "cost": pos["cost"],
                "sell_price": price, "sell_value": sell_value,
                "pnl_pct": round(pnl_pct, 2), "pnl_val": round(pnl_val, 2)
            })
            save_portfolio(portfolio)
            save_state(state)
            emoji_pnl = "🟢" if pnl_val >= 0 else "🔴"
            msg = (f"📕 【自动卖出】\n股票：{pos['name']}({code})\n"
                   f"卖出价：¥{price} × {pos['shares']}股 = ¥{sell_value:,.2f}\n"
                   f"{emoji_pnl} 盈亏：{pnl_pct:+.2f}% (¥{pnl_val:,.0f})\n"
                   f"原因：{reason}")
            wechat_notify(msg)
            print(f"✅ 【自动卖出】{pos['name']}({code}) 原因: {reason}")
            print(f"   卖出: ¥{price} × {pos['shares']} = ¥{sell_value:,.2f} | PnL: {pnl_pct:+.2f}%")
            _sync_monitor_list(remove_code=code)
            return True
    return False

def trigger_circuit_breaker(state, reason):
    state["circuit_breaker"] = True
    state["circuit_reason"] = reason
    save_state(state)
    print(f"🚨 【熔断触发】{reason}")

# ============ 市场温度 ============
def check_main_money_flow():
    try:
        codes_map = {
            "sh": "https://qt.gtimg.cn/q=sh000001",
            "sz": "https://qt.gtimg.cn/q=sz399001",
            "cy": "https://qt.gtimg.cn/q=sz399006",
        }
        data = {}
        for name, url in codes_map.items():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    text = r.read().decode("gbk")
                    parts = text.split("~")
                    if len(parts) > 10:
                        price = float(parts[3])
                        prev = float(parts[4])
                        data[name] = {"price": price, "prev": prev}
            except:
                pass
        if len(data) < 2:
            return 50, 0, False
        avg_chg = sum((d["price"]/d["prev"]-1)*100 for d in data.values()) / len(data)
        if avg_chg > 1.0: temp = 80
        elif avg_chg > 0.3: temp = 65
        elif avg_chg > -0.3: temp = 50
        elif avg_chg > -1.0: temp = 35
        else: temp = 20
        growth = avg_chg / 5
        return temp, growth, avg_chg > 0.3
    except Exception as e:
        print(f"[行情获取失败] {e}")
        return 50, 0, False

def should_buy(state, market_temperature, volume_growth):
    state = reset_daily_limits(state)
    if state.get("circuit_breaker"):
        return False, "熔断中"
    if state["today_buys"] >= MAX_BUYS_PER_DAY:
        return False, f"今日买入{state['today_buys']}次已达上限"
    WARM_THRESHOLD = 50
    VOLUME_GROWTH_MIN = 0.03
    if market_temperature >= WARM_THRESHOLD and volume_growth >= VOLUME_GROWTH_MIN:
        return True, f"市场回暖(温度{market_temperature}℃ + 放量{volume_growth*100:+.1f}%)"
    return False, f"市场偏冷(温度{market_temperature}℃)或放量不足"

# ============ 获取持仓现价 ============
current_prices = {}

def update_current_prices(portfolio):
    global current_prices
    current_prices = {}
    for pos in portfolio["positions"]:
        if pos["status"] == "holding":
            try:
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

# ============ 持仓状态推送 ============
def push_portfolio_status(portfolio):
    update_current_prices(portfolio)
    total_value = portfolio["cash"] + sum(
        current_prices.get(p["code"], p["entry_price"]) * p["shares"]
        for p in portfolio["positions"] if p["status"] == "holding"
    )
    total_pnl = sum(
        (current_prices.get(p["code"], p["entry_price"]) - p["entry_price"]) * p["shares"]
        for p in portfolio["positions"] if p["status"] == "holding"
    )
    now_str = datetime.now().strftime("%H:%M")
    lines = [f"📊 【猎手持仓】{now_str}"]
    for pos in portfolio["positions"]:
        if pos["status"] != "holding":
            continue
        cur = current_prices.get(pos["code"], pos["entry_price"])
        pnl = (cur / pos["entry_price"] - 1) * 100
        emoji = "🟢" if pnl >= 0 else "🔴"
        lines.append(
            f"{emoji} {pos['name']} @{cur} ({pnl:+.2f}%)\n"
            f"   止损{pos['stop_loss']} | 止盈{pos['take_profit']}"
        )
    lines.append(f"\n现金：¥{portfolio['cash']:,.0f}")
    lines.append(f"总市值：¥{total_value:,.0f}")
    lines.append(f"今日浮盈亏：¥{total_pnl:,.0f}")
    wechat_notify("\n".join(lines))

# ============ 选股建仓 ============
def execute_buy_candidates(state, portfolio):
    """执行选股建仓（仅交易时段）- 写入信号队列待确认，不直接买入"""
    try:
        from stock_picker import pick_best_candidates, calculate_buy_quantity
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        candidates = pick_best_candidates(
            max_count=MAX_BUYS_PER_DAY - state["today_buys"], min_score=5
        )
        signal_file = "/root/.hermes/猎手模拟交易/信号队列"
        for c in candidates:
            code, name, price = c["code"], c["name"], c["price"]
            shares = calculate_buy_quantity(price, portfolio["cash"], MAX_POSITION_PCT)
            if shares < 100:
                print(f"  资金不足买入{name}({code})：计算{shares}股 < 100")
                continue
            stop_loss = round(price * (1 - STOP_LOSS_PCT / 100), 2)
            take_profit = round(price * (1 + TAKE_PROFIT_PCT / 100), 2)
            # 写信号到队列（代替直接买入）
            signal = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "stock": code,
                "name": name,
                "action": "buy",
                "price": price,
                "shares": shares,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "note": c.get("note", "技术面入选 + 市场回暖"),
                "bearish_reasons": c.get("bearish", "高位股注意回调"),
                "status": "pending"
            }
            with open(signal_file, "a") as f:
                f.write(json.dumps(signal, ensure_ascii=False) + "\n")
            print(f"  ✅ 信号写入队列: {name}({code}) @ {price} × {shares}股")
            return True
        return False
    except Exception as e:
        print(f"[选股建仓异常] {e}")
        return False

# ============ 主执行流程 ============
def run_auto_trade_cycle():
    """
    【时间硬校验】→ 获取市场 → 检查持仓 → 选股建仓 → 推送状态
    """
    # ── 第一步：时间硬校验 ──
    is_trade, real_date, date_type = is_trading_day()
    weekday = WEEKDAY_NAMES[real_date.weekday()]
    now_str = datetime.now().strftime("%H:%M")
    trading_hours = is_trading_hours()

    print(f"\n{'='*50}")
    print(f"【时间校验】 {real_date} {weekday} {now_str}")
    print(f"是否交易日：{date_type}")
    print(f"交易时段：{'是' if trading_hours else '否 (9:30-11:30 / 13:00-15:00)'}")
    print(f"{'='*50}")

    # 非交易日：发通知 + 退出
    if not is_trade:
        send_trading_status()
        return {"status": "SKIP", "reason": f"非{date_type}"}

    # 非交易时段：发通知 + 仅推送持仓
    if not trading_hours:
        send_trading_status()
        portfolio = load_portfolio()
        state = load_state()
        push_portfolio_status(portfolio)
        return {"status": "NON_TRADING_HOURS", "reason": "非交易时段，仅推送持仓"}

    # ── 交易时段：执行完整流程 ──
    portfolio = load_portfolio()
    state = load_state()
    state = reset_daily_limits(state)
    update_current_prices(portfolio)
    results = []

    # 1. 止损检查
    for sig in check_stop_loss(portfolio, current_prices):
        results.append(sig["action"])
        auto_sell(state, portfolio, sig["code"], f"止损({sig['pnl_pct']}%)")

    # 2. 止盈检查
    for sig in check_take_profit(portfolio, current_prices):
        results.append(sig["action"])
        auto_sell(state, portfolio, sig["code"], f"止盈({sig['pnl_pct']}%)")

    # 3. 风控检查（熔断时任何时段都清仓）
    risk_signals = check_risk_control(portfolio, current_prices)
    if risk_signals:
        trigger_circuit_breaker(state, risk_signals[0]["action"])
        for pos in list(portfolio["positions"]):
            if pos["status"] == "holding":
                auto_sell(state, portfolio, pos["code"], "风控熔断")
        results.append(risk_signals[0]["action"])

    # 4. 市场温度
    market_temp, vol_growth, is_main_in = check_main_money_flow()
    state["market_temperature"] = market_temp
    state["volume_growth"] = vol_growth
    should, reason = should_buy(state, market_temp, vol_growth)
    save_state(state)

    # 5. 选股建仓
    if should and state["today_buys"] < MAX_BUYS_PER_DAY:
        execute_buy_candidates(state, portfolio)

    # 6. 持仓状态推送
    push_portfolio_status(portfolio)

    return {
        "status": "OK",
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

# ============ CLI入口 ============
if __name__ == "__main__":
    result = run_auto_trade_cycle()

    print("\n========== 自动交易检测结果 ==========")
    if result["status"] == "SKIP":
        print(f"状态：跳过（{result['reason']}）")
        print("非交易日，不执行任何交易操作")
    elif result["status"] == "NON_TRADING_HOURS":
        print(f"状态：非交易时段（已推送持仓）")
        print(f"现金: ¥{result.get('cash', 0):,.2f}")
    else:
        print(f"市场温度: {result['market_temperature']}℃ (放量{result['volume_growth']*100:+.1f}%)")
        print(f"主力流入: {'是' if result['is_main_inflow'] else '否'}")
        print(f"熔断状态: {'熔断中' if result['circuit_breaker'] else '正常'}")
        print(f"今日买入: {result['today_buys']}/{MAX_BUYS_PER_DAY}次")
        print(f"可建仓: {'是' if result['can_buy'] else '否'} - {result['buy_reason']}")
        print(f"信号: {' '.join(result['signals']) if result['signals'] else '无'}")
        print(f"现金: ¥{result['cash']:,.2f} | 持仓: {result['positions_count']}只")
    print("=========================================")
