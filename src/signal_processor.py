#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动执行层 (Signal Processor)
读取信号队列 → 自动执行 → 写入paper_trader
取代手动确认模式
"""
import sys, json, os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paper_trader import (
    paper_buy, paper_sell, check_stop_loss, check_take_profit,
    get_portfolio, get_state, get_positions, get_cash, print_portfolio
)

SIGNAL_FILE = "/root/.hermes/猎手模拟交易/信号队列"
PENDING_DIR = "/root/.hermes/猎手模拟交易/pending_confirm"
EXECUTION_LOG = "/root/.openclaw/workspace/猎手模拟交易/execution_log.json"

AUTO_MODE = True  # True = 自动执行，False = 需确认

def log_execution(action, detail):
    """记录执行日志"""
    log_file = EXECUTION_LOG
    logs = []
    if os.path.exists(log_file):
        with open(log_file) as f:
            logs = json.load(f)
    logs.append({"time": datetime.now().isoformat(), "action": action, "detail": detail})
    # 保留最近100条
    logs = logs[-100:]
    with open(log_file, 'w') as f:
        json.dump(logs, f, ensure_ascii=False)

def get_current_price(code):
    """获取实时价格"""
    try:
        prefix = 'sh' if code.startswith(('6', '5')) else 'sz'
        import urllib.request
        url = f"https://qt.gtimg.cn/q={prefix}{code}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            raw = r.read().decode("gbk")
        import re
        m = re.search(r'v_[\w]+="([^"]+)"', raw)
        if m:
            parts = m.group(1).split("~")
            return float(parts[3])
    except:
        pass
    return None

def process_signal(signal):
    """
    处理单个信号
    signal格式: {"stock","name","action","price","shares","stop_loss","take_profit","note","status":"pending"}
    """
    code = signal.get("stock", "")
    name = signal.get("name", "")
    action = signal.get("action", "")
    price = float(signal.get("price", 0))
    shares = int(signal.get("shares", 0))
    stop_loss = float(signal.get("stop_loss", 0))
    take_profit = float(signal.get("take_profit", 0))
    note = signal.get("note", "")
    signal_status = signal.get("status", "")

    if signal_status != "pending":
        return None, f"跳过非pending信号({signal_status})"

    if action == "buy":
        ok, msg = paper_buy(
            code=code, name=name,
            price=price, shares=shares,
            stop_loss=stop_loss, take_profit=take_profit,
            signal=note or "signal_queue"
        )
        return ok, msg

    elif action == "sell":
        current_price = get_current_price(code)
        ok, msg = paper_sell(code, reason=note or "signal_sell", current_price=current_price)
        return ok, msg

    return None, f"未知action: {action}"

def scan_and_execute():
    """
    扫描信号队列 + 执行所有pending信号
    """
    results = []
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(SIGNAL_FILE):
        return results

    with open(SIGNAL_FILE) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    if not lines:
        return results

    # 读取所有pending信号
    pending = []
    for line in lines:
        try:
            sig = json.loads(line)
            if sig.get("status") == "pending":
                pending.append((line, sig))
        except:
            continue

    if not pending:
        return results

    for raw_line, sig in pending:
        code = sig.get("stock", "")
        name = sig.get("name", "")
        action = sig.get("action", "")
        price = sig.get("price", 0)
        shares = sig.get("shares", 0)

        ok, msg = process_signal(sig)
        results.append({"code": code, "name": name, "action": action, "ok": ok, "msg": msg})
        log_execution(f"{action.upper()}_AUTO", f"{name}({code}) {action} {shares}@{price} -> {msg}")

        # 标记为已处理
        for i, line in enumerate(lines):
            if line == raw_line:
                lines[i] = json.dumps({**sig, "status": "processed"}, ensure_ascii=False)
                break

    # 写回
    with open(SIGNAL_FILE, 'w') as f:
        for line in lines:
            f.write(line + "\n")

    return results

def check_portfolio_stops():
    """
    检查持仓止损/止盈，发现触发立即执行
    """
    results = []
    positions = get_positions()
    if not positions:
        return results

    for pos in positions:
        code = pos["code"]
        name = pos["name"]
        current_price = get_current_price(code)
        if current_price is None:
            continue

        # 止损检查
        triggered, p = check_stop_loss(code, current_price)
        if triggered:
            ok, msg = paper_sell(code, reason=f"止损(现价{current_price}<{p['stop_loss']})", current_price=current_price)
            results.append({"code": code, "name": name, "action": "STOP_LOSS", "ok": ok, "msg": msg})
            log_execution("STOP_LOSS_AUTO", f"{name}({code}) @{current_price} -> {msg}")

        # 止盈检查
        triggered, p = check_take_profit(code, current_price)
        if triggered:
            ok, msg = paper_sell(code, reason=f"止盈(现价{current_price}>={p['take_profit']})", current_price=current_price)
            results.append({"code": code, "name": name, "action": "TAKE_PROFIT", "ok": ok, "msg": msg})
            log_execution("TAKE_PROFIT_AUTO", f"{name}({code}) @{current_price} -> {msg}")

    return results

def run_all():
    """完整运行：止损检查 → 信号执行 → 持仓快照"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 自动执行层启动")

    stop_results = check_portfolio_stops()
    for r in stop_results:
        print(f"  {'🔴' if r['action']=='STOP_LOSS' else '🟢'} {r['action']}: {r['msg']}")

    signal_results = scan_and_execute()
    for r in signal_results:
        print(f"  📋 信号执行: {r['msg']}")

    if not stop_results and not signal_results:
        print("  无触发事件")

    print_portfolio()
    return stop_results + signal_results

if __name__ == "__main__":
    run_all()
