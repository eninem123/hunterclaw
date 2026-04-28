#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速回测脚本
对指定股票运行策略回测
用法: python3 run_backtest.py --stock 000960 --days 60
"""
import sys, json, argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import urllib.request
import numpy as np
import pandas as pd

def fetch_kline(code, days=60):
    """获取K线数据"""
    try:
        prefix = 'sh' if code.startswith(('6', '5')) else 'sz'
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={prefix}{code},day,,,{days},qfq&r=0.1"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8")
        raw = raw.replace("kline_dayqfq=", "", 1).strip()
        data = json.loads(raw)
        qfqday = data.get("data", {}).get(prefix+code, {}).get("qfqday", [])
        if not qfqday:
            qfqday = data.get("data", {}).get(prefix+code, {}).get("day", [])
        qfqday = [r for r in qfqday if isinstance(r, list) and len(r) == 6]
        df = pd.DataFrame(qfqday, columns=["date", "open", "close", "high", "low", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        for col in ["open", "close", "high", "low", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna()
        return df
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

def run_backtest(df, initial_capital=100000, stop_loss_pct=0.05, take_profit_pct=0.08):
    """
    简单回测：MA+RSI策略
    - 买入：MA5上穿MA20 且 RSI<70
    - 止损：-5%
    - 止盈：+8%
    """
    df = df.dropna().copy()
    if len(df) < 30:
        return None, "数据不足"

    # 计算指标
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["rsi"] = calculate_rsi(df["close"])
    df["volume_ma5"] = df["volume"].rolling(5).mean()

    capital = initial_capital
    cash = capital
    position = None
    trades = []

    for i in range(30, len(df)):
        date = df.index[i]
        row = df.iloc[i]
        close = row["close"]

        if position:
            # 持仓中：检查止损止盈
            pnl_pct = (close - position["entry_price"]) / position["entry_price"]

            sold = False
            reason = ""
            if pnl_pct <= -stop_loss_pct:
                reason = "止损"
                sold = True
            elif pnl_pct >= take_profit_pct:
                reason = "止盈"
                sold = True

            if sold:
                proceeds = close * position["shares"]
                commission = proceeds * 0.0003 + proceeds * 0.001
                net_proceeds = proceeds - commission
                pnl = net_proceeds - position["cost"]
                capital = capital + pnl
                trades.append({
                    "date": str(date.date()),
                    "code": position["code"],
                    "action": "SELL",
                    "price": close,
                    "shares": position["shares"],
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct * 100, 2),
                    "reason": reason
                })
                position = None

        if not position and i < len(df) - 1:
            # 无持仓：检查买入信号
            prev = df.iloc[i-1]
            ma5_cross = prev["ma5"] <= prev["ma20"] and row["ma5"] > row["ma20"]
            rsi_ok = 40 < row["rsi"] < 70
            vol_ok = row["volume"] > row["volume_ma5"] * 1.2

            if ma5_cross and rsi_ok and vol_ok and cash > close * 100:
                shares = int(cash / close / 100) * 100
                cost = close * shares
                commission = cost * 0.0003
                position = {
                    "code": df.iloc[i].name,
                    "entry_price": close,
                    "shares": shares,
                    "cost": cost + commission,
                    "entry_date": date
                }

    # 平仓最后持仓
    if position:
        close = df.iloc[-1]["close"]
        proceeds = close * position["shares"]
        commission = proceeds * 0.0003 + proceeds * 0.001
        net = proceeds - commission
        pnl = net - position["cost"]
        capital = capital + pnl
        trades.append({
            "date": str(df.index[-1].date()),
            "code": "LAST",
            "action": "SELL",
            "price": close,
            "shares": position["shares"],
            "pnl": round(pnl, 2),
            "pnl_pct": round((close / position["entry_price"] - 1) * 100, 2),
            "reason": "回测结束"
        })

    # 计算统计
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    total_return = (capital - initial_capital) / initial_capital * 100
    win_trades = [t for t in sell_trades if t.get("pnl", 0) > 0]
    loss_trades = [t for t in sell_trades if t.get("pnl", 0) <= 0]

    avg_win_val = sum(t["pnl"] for t in win_trades) / max(len(win_trades), 1) if win_trades else 0
    avg_loss_val = sum(t["pnl"] for t in loss_trades) / max(len(loss_trades), 1) if loss_trades else 0

    metrics = {
        "initial_capital": initial_capital,
        "final_capital": round(capital, 2),
        "total_return_pct": round(total_return, 2),
        "total_trades": len(sell_trades),
        "win_trades": len(win_trades),
        "loss_trades": len(loss_trades),
        "win_rate": round(len(win_trades) / max(len(sell_trades), 1) * 100, 1),
        "avg_win": round(avg_win_val, 2),
        "avg_loss": round(avg_loss_val, 2),
        "max_win_pct": round(max((t["pnl_pct"] for t in sell_trades), default=0), 2),
        "max_loss_pct": round(min((t["pnl_pct"] for t in sell_trades), default=0), 2),
    }

    return metrics, trades

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="快速回测")
    parser.add_argument("--stock", default="000960", help="股票代码")
    parser.add_argument("--days", type=int, default=120, help="回测天数")
    parser.add_argument("--name", default="锡业股份", help="股票名称")
    args = parser.parse_args()

    print(f"\n📊 回测: {args.name}({args.stock}) 近{args.days}天")
    print("=" * 50)

    df = fetch_kline(args.stock, args.days)
    if df is None:
        print("获取数据失败")
        sys.exit(1)

    print(f"数据范围: {df.index[0].date()} ~ {df.index[-1].date()}, 共{len(df)}个交易日")
    print("-" * 50)

    metrics, trades = run_backtest(df)

    if metrics is None:
        print(f"错误: {trades}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  总收益率: {metrics['total_return_pct']:+.2f}%")
    print(f"  总交易次数: {metrics['total_trades']}次")
    print(f"  胜率: {metrics['win_rate']:.1f}%")
    print(f"  盈利次数: {metrics['win_trades']} | 亏损次数: {metrics['loss_trades']}")
    print(f"  平均盈利: ¥{metrics['avg_win']:,.2f} | 平均亏损: ¥{metrics['avg_loss']:,.2f}")
    print(f"  最大单笔盈利: {metrics['max_win_pct']:+.2f}%")
    print(f"  最大单笔亏损: {metrics['max_loss_pct']:+.2f}%")
    print(f"{'='*50}")

    if trades:
        print(f"\n📋 交易明细:")
        for t in trades[-10:]:
            emoji = "🟢" if t["pnl"] >= 0 else "🔴"
            print(f"  {t['date']} {emoji} {t['action']} @ ¥{t['price']:.2f} x{t['shares']} | {t['pnl']:+.2f}元({t['pnl_pct']:+.2f}%) | {t['reason']}")

    # 保存报告
    report = {
        "stock": args.stock,
        "name": args.name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "period_days": args.days,
        "metrics": metrics,
        "trades": trades[-50:]
    }
    out_file = Path(__file__).parent / "data" / "results" / f"backtest_{args.stock}_{datetime.now().strftime('%Y%m%d')}.json"
    out_file.parent.mkdir(exist_ok=True)
    with open(out_file, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 报告已保存: {out_file.name}")
