#!/usr/bin/env python3
"""
猎手系统 - Cron 入口脚本
负责：调用扫描 → 格式化 → 打印输出（供cron捕获推送）
然后调用 auto_trade 执行买卖
"""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, date

# 确保hunter目录在python路径
sys.path.insert(0, str(Path(__file__).parent))

from market_scanner import full_scan, format_report

AUTO_TRADE_SCRIPT = "/root/.openclaw/workspace/猎手模拟交易/src/auto_trade.py"

# ── A股交易时间校验 ──
def is_trading_day():
    """检查今天是否是A股交易日（周一~周五，非节假日简版）"""
    today = date.today()
    # 周六周日休市
    if today.weekday() >= 5:
        return False
    return True

def is_trading_hours():
    """检查当前是否在A股交易时段（9:30-11:30 / 13:00-15:00）"""
    now = datetime.now()
    h, m = now.hour, now.minute
    
    # 上午: 9:30 - 11:30
    if (h == 9 and m >= 30) or (9 < h < 11):
        return True
    if h == 11 and m <= 30:
        return True
    
    # 下午: 13:00 - 15:00
    if 13 <= h < 15:
        return True
    
    return False

if __name__ == "__main__":
    mode = "normal"
    if "--morning" in sys.argv:
        mode = "morning"
    elif "--afternoon" in sys.argv:
        mode = "afternoon"
    elif "--closing" in sys.argv:
        mode = "closing"

    # ── 非交易时段：只做持仓状态推送，不做买卖 ──
    is_trading = is_trading_day() and is_trading_hours()
    
    if not is_trading:
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        today_label = weekday_names[date.today().weekday()]
        now_str = datetime.now().strftime("%H:%M")
        print(f"📴 [{today_label} {now_str}] 非交易时段，跳过交易扫描")
        print("  A股交易时间：周一~周五 9:30-11:30 / 13:00-15:00")
        print("  如需查看持仓，请手动运行 auto_trade.py")
        
        # 非交易时段只执行持仓状态推送
        if is_trading_day():
            print("\n[run_scan] 非交易时段，持仓推送...")
            try:
                r = subprocess.run(
                    ["python3", AUTO_TRADE_SCRIPT, "--status-only"],
                    capture_output=True, text=True, timeout=60
                )
                print(r.stdout)
            except Exception as e:
                print(f"[auto_trade 调用失败] {e}")
        sys.exit(0)

    closing_mode = (mode == "closing")

    report = full_scan(closing_mode=closing_mode)

    # 如果是开盘/尾盘模式，注入阶段标识
    if mode == "morning":
        report["section"] = "开盘提醒"
    elif mode == "afternoon":
        report["section"] = "下午开盘"
    elif mode == "closing":
        report["section"] = "撤退检查"

    # 输出供推送
    output = format_report(report)
    print(output)

    # ── 调用自动交易（买/卖/持仓推送）──
    print("\n" + "=" * 40)
    print("[run_scan] 调用 auto_trade 执行交易...")
    try:
        r = subprocess.run(
            ["python3", AUTO_TRADE_SCRIPT],
            capture_output=True,
            text=True,
            timeout=120
        )
        print(r.stdout)
        if r.stderr:
            print("STDERR:", r.stderr[:500])
    except Exception as e:
        print(f"[auto_trade 调用失败] {e}")

    # exit code = 0 正常，1 有高危预警
    if report["verdict"] == "RISK_HIGH":
        sys.exit(1)
    sys.exit(0)
