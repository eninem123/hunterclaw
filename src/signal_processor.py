#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动执行层 (Signal Processor) v3.9
读取信号队列 → 自动执行 → 写入paper_trader
取代手动确认模式

v3.9 改进:
  R01: 涨停过滤（涨幅>=9.8%禁止买）
  R03: 量比门槛（量比>=1.3）
  时间硬校验（仅交易时段执行）
  熔断保护（读取trade_state.json）
  价格偏离校验（偏离>5%拒绝追高）
  异常保护（try-except + error标记）
  详细执行日志
"""
import sys, json, os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paper_trader import (
    paper_buy, paper_sell, check_stop_loss, check_take_profit,
    get_portfolio, get_state, get_positions, get_cash, print_portfolio
)
import sys
sys.path.insert(0, '/root/.openclaw/workspace/猎手模拟交易/scripts')
from debias_rules import HunterDebiasSystem

SIGNAL_FILE = "/root/.hermes/猎手模拟交易/信号队列"  # 目录路径，扫描所有.jsonl文件
PENDING_DIR = "/root/.hermes/猎手模拟交易/pending_confirm"
EXECUTION_LOG = "/root/.openclaw/workspace/猎手模拟交易/execution_log.json"
STATE_FILE = "/root/.openclaw/workspace/猎手模拟交易/trade_state.json"

AUTO_MODE = True  # True = 自动执行，False = 需确认

# ── 辅助校验函数 ──────────────────────────────────────

def is_trading_hours():
    """判断当前是否在A股交易时段（9:30-11:30 / 13:00-15:00）"""
    now = datetime.now()
    h, m = now.hour, now.minute
    morning = (h == 9 and m >= 30) or (10 <= h <= 11) or (h == 11 and m <= 30)
    afternoon = 13 <= h < 15
    return morning or afternoon

def is_near_limit_up(chg_pct):
    """R01: 涨停股禁止买入（涨幅>=9.8%风险过高）"""
    return chg_pct >= 9.8

def meets_volume_ratio_threshold(vol_ratio, threshold=1.3):
    """R03: 量比门槛（需>=1.3）"""
    return vol_ratio >= threshold

# ── 日志记录 ──────────────────────────────────────────

def log_execution(action, detail):
    """记录执行日志（保留最近200条）"""
    log_file = EXECUTION_LOG
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append({"time": datetime.now().isoformat(), "action": action, "detail": detail})
    logs = logs[-200:]
    try:
        with open(log_file, 'w') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── 价格获取 ──────────────────────────────────────────

def get_current_price(code):
    """获取实时价格（腾讯接口）"""
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
    except Exception:
        pass
    return None

# ── 熔断状态检查 ───────────────────────────────────────

def is_circuit_broken():
    """检查是否触发熔断"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                state = json.load(f)
            return state.get("circuit_breaker", False), state.get("circuit_reason", "未知")
    except Exception:
        pass
    return False, ""

# ── 信号处理核心 ──────────────────────────────────────

def process_signal(signal):
    """
    处理单个信号（v3.9强化版）
    signal格式: {"stock","name","action","price","shares","stop_loss","take_profit",
                 "note","status":"pending","chg_pct":float,"vol_ratio":float}
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
    chg_pct = float(signal.get("chg_pct", 0))
    vol_ratio = float(signal.get("vol_ratio", 0))

    if signal_status != "pending":
        return None, f"跳过非pending信号({signal_status})"

    # ── 时间硬校验：仅交易时段执行 ──
    if not is_trading_hours():
        log_execution("TIME_REJECT", f"非交易时段，跳过 {name}({code}) {action}")
        return None, f"非交易时段(9:30-11:30/13:00-15:00)"

    # ── 熔断检查 ──
    broken, reason = is_circuit_broken()
    if broken:
        log_execution("CIRCUIT_REJECT", f"熔断中({reason})，跳过 {name}({code})")
        return False, f"🚨 系统熔断中（{reason}），禁止操作"

    # ── 认知偏差自检（v3.96+） ──
    debias_system = HunterDebiasSystem()
    bias_check_result = debias_system.check_all({
        'decision_type': action,
        'code': code, 'name': name, 'price': price,
        'shares': shares, 'stop_loss': stop_loss, 'take_profit': take_profit,
        'note': note,
        'user_assumption': bool('收购' in note or '概率' in note),
        'confidence': 0.85 if '85%' in note else 1.0,
        'system_confidence': 1.0
    })
    if bias_check_result.warnings:
        msgs = [w['message'] for w in bias_check_result.warnings]
        log_execution("DEBIAS_CHECK", f"{len(msgs)}个偏差: {msgs}")

    if action == "buy":
        # R01: 涨停过滤（涨幅>=9.8%）
        if is_near_limit_up(chg_pct):
            log_execution("LIMIT_UP_REJECT", f"{name}({code}) 涨幅{chg_pct:.2f}% >= 9.8%")
            return False, f"⚠️ {name} 涨幅{chg_pct:.2f}%，近涨停禁止买入"

        # R03: 量比门槛（>=1.3）
        if not meets_volume_ratio_threshold(vol_ratio):
            log_execution("VOL_RATIO_REJECT", f"{name}({code}) 量比{vol_ratio:.1f} < 1.3")
            return False, f"⚠️ {name} 量比{vol_ratio:.1f} < 1.3，不满足量比门槛"

        # 高风险认知偏差：要求确认
        if bias_check_result.warnings and any(w['severity'] == 'high' for w in bias_check_result.warnings):
            high_msgs = [w['message'] for w in bias_check_result.warnings if w['severity'] == 'high']
            return False, f"⚠️ 高风险认知偏差: {high_msgs}"

        # 价格合理性：偏离信号价>5%拒绝追高
        current_price = get_current_price(code)
        if current_price and price > 0 and abs(current_price - price) / price > 0.05:
            log_execution("PRICE_REJECT", f"{name}({code}) 信号{price} vs 现价{current_price} 偏离>5%")
            return False, f"⚠️ {name} 现价{current_price} vs 信号{price} 偏离>5%，拒绝追高"

        ok, msg = paper_buy(
            code=code, name=name,
            price=price, shares=shares,
            stop_loss=stop_loss, take_profit=take_profit,
            signal=note or "signal_queue"
        )
        return ok, msg

    if action == "sell":
        # 高风险偏差检查
        if bias_check_result.warnings and any(w['severity'] == 'high' for w in bias_check_result.warnings):
            high_msgs = [w['message'] for w in bias_check_result.warnings if w['severity'] == 'high']
            return False, f"⚠️ 高风险认知偏差: {high_msgs}"
        ok, msg = paper_sell(code, reason=note or "signal_sell", current_price=current_price)
        return ok, msg

    return None, f"未知action: {action}"

# ── 信号队列扫描执行 ──────────────────────────────────

def scan_and_execute():
    """
    扫描信号队列 + 执行所有pending信号（v3.9强化版）
    """
    results = []
    today = datetime.now().strftime("%Y-%m-%d")
    today_signal_file = f"{SIGNAL_FILE}/{today}_signals.jsonl"
    
    if not os.path.exists(today_signal_file):
        log_execution("SCAN", f"[{today}] 今日信号文件不存在")
        return results

    try:
        with open(today_signal_file) as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except Exception as e:
        log_execution("FILE_READ_ERROR", str(e))
        return results

    if not lines:
        return results

    # 读取所有pending信号
    pending = []
    for line in lines:
        try:
            sig = json.loads(line)
            if sig.get("status") == "pending":
                pending.append((line, sig))
        except Exception:
            continue

    if not pending:
        log_execution("SCAN", f"[{today}] 无pending信号")
        return results

    log_execution("SCAN_START", f"[{today}] 扫描到{len(pending)}个pending信号")

    for raw_line, sig in pending:
        code = sig.get("stock", "")
        name = sig.get("name", "")
        action = sig.get("action", "")
        price = sig.get("price", 0)
        shares = sig.get("shares", 0)

        try:
            ok, msg = process_signal(sig)
            results.append({"code": code, "name": name, "action": action, "ok": ok, "msg": msg})
            log_execution(f"{action.upper()}_AUTO", f"{name}({code}) {action} {shares}@{price} -> {msg}")

            # 标记状态：执行成功processed，失败原因决定skipped/error
            if ok is True:
                new_status = "processed"
            elif ok is False:
                new_status = "skipped"  # 安全原因拒绝（熔断/涨停/量比等）
            else:
                new_status = "processed"
            for i, line in enumerate(lines):
                if line == raw_line:
                    lines[i] = json.dumps({**sig, "status": new_status}, ensure_ascii=False)
                    break
        except Exception as e:
            err_msg = f"执行异常: {str(e)}"
            log_execution("EXEC_ERROR", f"{name}({code}) 异常: {e}")
            results.append({"code": code, "name": name, "action": action, "ok": False, "msg": err_msg})
            for i, line in enumerate(lines):
                if line == raw_line:
                    lines[i] = json.dumps({**sig, "status": "error", "error": str(e)}, ensure_ascii=False)
                    break

    # 写回
    try:
        with open(SIGNAL_FILE, 'w') as f:
            for line in lines:
                f.write(line + "\n")
    except Exception as e:
        log_execution("FILE_WRITE_ERROR", str(e))

    log_execution("SCAN_DONE", f"处理{len(results)}个，成功{sum(1 for r in results if r.get('ok'))}个")
    return results

# ── 持仓止损止盈检查 ─────────────────────────────────

def check_portfolio_stops():
    """检查持仓止损/止盈，发现触发立即执行"""
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

        # 止盈检查（分批止盈 R04：+4%卖1/3，+8%卖1/3，+12%清仓）
        triggered, p = check_take_profit(code, current_price)
        if triggered:
            ok, msg = paper_sell(code, reason=f"止盈(现价{current_price}>={p['take_profit']})", current_price=current_price)
            results.append({"code": code, "name": name, "action": "TAKE_PROFIT", "ok": ok, "msg": msg})
            log_execution("TAKE_PROFIT_AUTO", f"{name}({code}) @{current_price} -> {msg}")

    return results

# ── 完整执行循环 ──────────────────────────────────────

def run_all():
    """完整运行（v3.9）：止损检查 → 信号执行 → 持仓快照"""
    from datetime import datetime as dt
    ts = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    trading = is_trading_hours()
    broken, reason = is_circuit_broken()
    print(f"\n[{'='*55}]")
    print(f"[{ts}] 自动执行层 v3.9")
    print(f"  交易时段: {'✅' if trading else '❌'} | 熔断: {'🚨 '+reason if broken else '✅正常'} | AUTO: {'ON' if AUTO_MODE else 'OFF'}")
    print(f"[{'='*55}]")

    # 1. 止损检查（任何时候都可能触发）
    stop_results = check_portfolio_stops()
    for r in stop_results:
        print(f"  {'🔴' if r['action']=='STOP_LOSS' else '🟢'} {r['action']}: {r['msg']}")

    # 2. 信号执行
    if AUTO_MODE:
        signal_results = scan_and_execute()
        for r in signal_results:
            emoji = "✅" if r.get("ok") else "⏭️"
            print(f"  {emoji} {r['name']}({r['code']}) {r['action']} -> {r['msg']}")
    else:
        print("  ⏸️ AUTO_MODE=OFF，跳过信号执行")
        signal_results = []

    # 3. 持仓快照
    if not stop_results and not signal_results:
        print("  ✅ 无触发事件")
    print(f"\n[{dt.now().strftime('%H:%M:%S')}] 持仓快照:")
    print_portfolio()
    log_execution("CYCLE_DONE", f"stop={len(stop_results)} signal={len(signal_results)}")
    return stop_results + signal_results

if __name__ == "__main__":
    run_all()