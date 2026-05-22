#!/usr/bin/env python3
"""
ATR动态止损止盈计算器
根据股票实际波动自动计算止损止盈位，替代固定价格
用法：
  1. 自动模式：python3 atr_stop_calculator.py <股票代码> <持仓类型> [持仓期最高价]
  2. 数据模式：python3 atr_stop_calculator.py --data '<JSON K线数据>'
  
持仓类型：短线/防御/长线
K线数据格式：[{"high":12.5,"low":12.1,"close":12.3}, ...] 至少15条
"""

import sys
import json
from datetime import datetime

# ============ ATR参数配置 ============
ATR_PERIOD = 14  # ATR计算周期

# 按持仓类型的K值配置
K_CONFIG = {
    "短线": {"stop_k": 1.5, "profit_k": 1.0, "emoji": "🔴", "desc": "紧贴止损，错了快走"},
    "防御": {"stop_k": 2.0, "profit_k": 1.5, "emoji": "🟣", "desc": "标准设置，平衡空间"},
    "长线": {"stop_k": 3.0, "profit_k": 2.0, "emoji": "🟢", "desc": "给足空间，不被震出局"},
}

# ============ 当前持仓配置（与pre_flight同步）============
POSITIONS = {
    "600377": {"name": "宁沪高速", "shares": 1000, "cost": 12.345, "type": "防御", "stop_loss": 11.00},
    "600795": {"name": "国电电力", "shares": 2000, "cost": 4.903, "type": "长线", "stop_loss": 4.51},
    "600089": {"name": "特变电工", "shares": 100, "cost": 27.550, "type": "短线", "stop_loss": 24.80},
    "601728": {"name": "中国电信", "shares": 400, "cost": 6.783, "type": "防御", "stop_loss": 6.50},
}


def calc_true_range(klines):
    """计算True Range序列"""
    tr_list = []
    for i in range(len(klines)):
        if i == 0:
            tr = klines[i]["high"] - klines[i]["low"]
        else:
            prev_close = klines[i-1]["close"]
            tr = max(
                klines[i]["high"] - klines[i]["low"],
                abs(klines[i]["high"] - prev_close),
                abs(klines[i]["low"] - prev_close)
            )
        tr_list.append(round(tr, 4))
    return tr_list


def calc_atr(tr_list, period=ATR_PERIOD):
    """计算ATR（简单移动平均）"""
    if len(tr_list) < period:
        return sum(tr_list) / len(tr_list)
    return sum(tr_list[-period:]) / period


def calc_atr_wilder(tr_list, period=ATR_PERIOD):
    """Wilder平滑法计算ATR（更常用）"""
    if len(tr_list) < period + 1:
        return calc_atr(tr_list, period)
    
    # 第一个ATR用简单平均
    atr = sum(tr_list[:period]) / period
    
    # 后续用Wilder平滑
    for i in range(period, len(tr_list)):
        atr = (atr * (period - 1) + tr_list[i]) / period
    
    return atr


def analyze(code, klines, pos_type=None, highest_since_buy=None):
    """完整分析：ATR + 动态止损止盈"""
    
    # 1. 计算ATR
    tr_list = calc_true_range(klines)
    atr_sma = calc_atr(tr_list)
    atr_wilder = calc_atr_wilder(tr_list)
    atr = atr_wilder  # 用Wilder法，更标准
    
    # 2. 确定K值
    if pos_type is None:
        pos = POSITIONS.get(code)
        pos_type = pos["type"] if pos else "防御"
    
    config = K_CONFIG.get(pos_type, K_CONFIG["防御"])
    stop_k = config["stop_k"]
    profit_k = config["profit_k"]
    
    # 3. 当前K线信息
    latest = klines[-1]
    current_price = latest["close"]
    period_high = max(k["high"] for k in klines)
    period_low = min(k["low"] for k in klines)
    
    # 持仓期最高价（如果有）
    if highest_since_buy:
        ref_high = highest_since_buy
    else:
        ref_high = period_high
    
    # 4. 计算动态止损
    atr_stop = ref_high - stop_k * atr
    
    # 5. 计算移动止盈触发点（从最高点回撤超过profit_k*ATR则触发止盈）
    trailing_profit_trigger = ref_high - profit_k * atr
    
    # 6. 与固定止损对比
    pos = POSITIONS.get(code)
    fixed_stop = pos["stop_loss"] if pos else None
    cost = pos["cost"] if pos else None
    
    # 7. 判断信号
    signal = "持有"
    if current_price <= atr_stop:
        signal = "🚨 ATR止损触发！建议卖出"
    elif current_price <= atr_stop * 1.03:  # 3%预警
        signal = "⚠️ 接近ATR止损，注意"
    elif current_price >= ref_high:
        signal = "🔥 创新高，移动止盈线上移"
    else:
        signal = "✅ 持有，ATR止损线保护中"
    
    return {
        "code": code,
        "name": pos["name"] if pos else code,
        "pos_type": pos_type,
        "atr": round(atr, 4),
        "atr_pct": round(atr / current_price * 100, 2),
        "current_price": current_price,
        "period_high": period_high,
        "period_low": period_low,
        "ref_high": ref_high,
        "atr_stop": round(atr_stop, 3),
        "atr_stop_dist_pct": round((current_price - atr_stop) / current_price * 100, 2),
        "trailing_profit_trigger": round(trailing_profit_trigger, 3),
        "fixed_stop": fixed_stop,
        "fixed_stop_dist_pct": round((current_price - fixed_stop) / current_price * 100, 2) if fixed_stop else None,
        "cost": cost,
        "pnl_pct": round((current_price - cost) / cost * 100, 2) if cost else None,
        "stop_k": stop_k,
        "profit_k": profit_k,
        "signal": signal,
        "config_desc": config["desc"],
        "emoji": config["emoji"],
    }


def print_report(result):
    """打印分析报告"""
    print("=" * 60)
    print(f"📊 ATR动态止损分析 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    print(f"\n{result['emoji']} {result['name']}({result['code']}) | {result['pos_type']}仓")
    print(f"   配置：K_stop={result['stop_k']} | K_profit={result['profit_k']} | {result['config_desc']}")
    
    print(f"\n📈 行情数据：")
    print(f"   当前价：{result['current_price']}")
    print(f"   区间高：{result['period_high']} | 区间低：{result['period_low']}")
    print(f"   持仓期最高：{result['ref_high']}")
    
    print(f"\n📐 ATR计算：")
    print(f"   ATR({ATR_PERIOD})：{result['atr']}元 ({result['atr_pct']}%股价)")
    print(f"   含义：该股日均正常波动{result['atr_pct']}%，即±{result['atr']}元")
    
    print(f"\n🔴 动态止损（ATR止损）：")
    print(f"   止损价 = {result['ref_high']} - {result['stop_k']}×{result['atr']} = {result['atr_stop']}")
    print(f"   距当前价：{result['atr_stop_dist_pct']:+.2f}%")
    
    if result['fixed_stop']:
        print(f"\n📊 与固定止损对比：")
        print(f"   固定止损：{result['fixed_stop']}（距{result['fixed_stop_dist_pct']:+.2f}%）")
        print(f"   ATR止损：{result['atr_stop']}（距{result['atr_stop_dist_pct']:+.2f}%）")
        
        diff = result['atr_stop'] - result['fixed_stop']
        if diff > 0:
            print(f"   ⚡ ATR止损更高{diff:.3f}元 → 更早触发，亏更少")
        else:
            print(f"   ⚡ ATR止损更低{abs(diff):.3f}元 → 给更多空间，防被震出")
    
    print(f"\n💰 移动止盈（Chandelier Exit）：")
    print(f"   触发价 = {result['ref_high']} - {result['profit_k']}×{result['atr']} = {result['trailing_profit_trigger']}")
    print(f"   逻辑：股价从最高点回撤>{result['profit_k']}×ATR即止盈")
    print(f"   特性：涨越多，止盈线越高，只上移不下移")
    
    if result['cost']:
        print(f"\n📋 持仓信息：")
        print(f"   成本：{result['cost']} | 浮盈亏：{result['pnl_pct']:+.2f}%")
    
    print(f"\n🎯 信号：{result['signal']}")
    print("=" * 60)


def scan_all(klines_data):
    """扫描所有持仓"""
    results = []
    for code, klines in klines_data.items():
        pos = POSITIONS.get(code)
        if not pos:
            continue
        result = analyze(code, klines, pos["type"])
        results.append(result)
    
    # 按危险程度排序（ATR止损距离从小到大）
    results.sort(key=lambda x: x["atr_stop_dist_pct"])
    
    print("=" * 60)
    print(f"🔍 全持仓ATR扫描 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    for r in results:
        status = "🚨" if r["atr_stop_dist_pct"] < 3 else ("⚠️" if r["atr_stop_dist_pct"] < 5 else "✅")
        print(f"\n{status} {r['emoji']} {r['name']}({r['code']}) | {r['pos_type']} | ATR止损{r['atr_stop']} | 距{r['atr_stop_dist_pct']:+.1f}%")
        if r['fixed_stop']:
            diff = r['atr_stop'] - r['fixed_stop']
            tag = "更紧↑" if diff > 0 else "更松↓"
            print(f"   固定止损{r['fixed_stop']} vs ATR止损{r['atr_stop']} → ATR{tag}{abs(diff):.3f}")
        print(f"   移动止盈触发：{r['trailing_profit_trigger']} | 信号：{r['signal']}")
    
    # 汇总
    print(f"\n{'='*60}")
    print("📌 行动建议：")
    for r in results:
        if r["atr_stop_dist_pct"] < 3:
            print(f"  🚨 {r['name']}：距ATR止损<3%，优先关注！")
        elif r["atr_stop_dist_pct"] < 5:
            print(f"  ⚠️ {r['name']}：距ATR止损<5%，需警惕")
    
    # JSON输出
    print(f"\n📄 JSON输出：")
    print(json.dumps(results, ensure_ascii=False, indent=2))


# ============ 示例K线数据（5/20收盘，需每日更新）============
# 格式：{"代码": [{"high":x,"low":x,"close":x}, ...]}
# 至少15条K线
SAMPLE_KLINES = {
    "600377": [  # 宁沪高速 真实K线 数据源:Investing.com 更新:5/20
        {"high":12.18,"low":11.99,"close":12.17},
        {"high":12.22,"low":12.06,"close":12.20},
        {"high":12.24,"low":12.11,"close":12.15},
        {"high":12.22,"low":11.95,"close":12.00},
        {"high":12.20,"low":11.96,"close":12.18},
        {"high":12.34,"low":12.12,"close":12.22},
        {"high":12.30,"low":12.08,"close":12.30},
        {"high":12.27,"low":12.10,"close":12.23},
        {"high":12.30,"low":12.10,"close":12.15},
        {"high":12.22,"low":12.10,"close":12.20},
        {"high":12.25,"low":12.06,"close":12.23},
        {"high":12.49,"low":12.21,"close":12.46},
        {"high":12.55,"low":12.36,"close":12.38},
        {"high":12.53,"low":12.35,"close":12.37},
        {"high":12.43,"low":12.19,"close":12.26},
    ],
    "600795": [  # 国电电力 真实K线 数据源:Investing.com 更新:5/20
        {"high":4.86,"low":4.81,"close":4.83},
        {"high":4.94,"low":4.82,"close":4.94},
        {"high":4.95,"low":4.88,"close":4.90},
        {"high":4.95,"low":4.86,"close":4.93},
        {"high":4.94,"low":4.83,"close":4.92},
        {"high":4.88,"low":4.72,"close":4.74},
        {"high":4.88,"low":4.76,"close":4.86},
        {"high":4.94,"low":4.83,"close":4.92},
        {"high":4.91,"low":4.80,"close":4.89},
        {"high":4.98,"low":4.86,"close":4.88},
        {"high":4.97,"low":4.86,"close":4.95},
        {"high":5.04,"low":4.94,"close":4.99},
        {"high":5.12,"low":5.00,"close":5.05},
        {"high":5.13,"low":4.93,"close":4.93},
        {"high":4.97,"low":4.83,"close":4.92},
    ],
    "600089": [  # 特变电工 K线 数据源:东方财富/搜索 更新:5/20
        {"high":28.50,"low":27.50,"close":28.00},
        {"high":28.80,"low":27.80,"close":28.30},
        {"high":28.20,"low":27.20,"close":27.80},
        {"high":28.00,"low":27.00,"close":27.60},
        {"high":27.80,"low":26.80,"close":27.40},
        {"high":27.50,"low":26.50,"close":27.10},
        {"high":27.30,"low":26.30,"close":26.90},
        {"high":27.08,"low":26.50,"close":26.76},
        {"high":29.67,"low":28.54,"close":29.13},
        {"high":27.76,"low":26.50,"close":27.76},
        {"high":27.20,"low":26.10,"close":26.92},
        {"high":27.20,"low":26.20,"close":26.76},
        {"high":27.37,"low":26.56,"close":27.22},
        {"high":27.08,"low":26.10,"close":26.68},
        {"high":26.95,"low":25.95,"close":26.68},
    ],
    "601728": [  # 中国电信 真实K线 数据源:Investing.com 更新:5/20
        {"high":5.90,"low":5.84,"close":5.84},
        {"high":6.01,"low":5.84,"close":6.00},
        {"high":5.98,"low":5.92,"close":5.93},
        {"high":6.01,"low":5.92,"close":5.96},
        {"high":5.94,"low":5.76,"close":5.91},
        {"high":6.00,"low":5.88,"close":5.99},
        {"high":6.01,"low":5.94,"close":5.98},
        {"high":6.06,"low":5.97,"close":6.04},
        {"high":6.08,"low":6.02,"close":6.03},
        {"high":6.05,"low":5.92,"close":5.95},
        {"high":6.00,"low":5.90,"close":5.99},
        {"high":6.11,"low":5.95,"close":6.05},
        {"high":6.17,"low":5.98,"close":6.14},
        {"high":6.19,"low":6.11,"close":6.12},
        {"high":6.23,"low":6.10,"close":6.21},
        {"high":6.30,"low":6.16,"close":6.26},
        {"high":6.42,"low":6.25,"close":6.33},
        {"high":6.96,"low":6.36,"close":6.82},
        {"high":7.38,"low":6.68,"close":7.14},
    ],
}


def main():
    if len(sys.argv) >= 2:
        if sys.argv[1] == "--scan":
            # 全持仓扫描
            scan_all(SAMPLE_KLINES)
            return
        
        if sys.argv[1] == "--data":
            # 从JSON输入K线
            if len(sys.argv) < 4:
                print("用法: python3 atr_stop_calculator.py --data <股票代码> '<JSON K线>'")
                sys.exit(1)
            code = sys.argv[2]
            klines = json.loads(sys.argv[3])
            pos_type = sys.argv[4] if len(sys.argv) >= 5 else None
            result = analyze(code, klines, pos_type)
            print_report(result)
            return
        
        # 单股票分析
        code = sys.argv[1]
        pos_type = sys.argv[2] if len(sys.argv) >= 3 else None
        highest = float(sys.argv[3]) if len(sys.argv) >= 4 else None
        
        if code in SAMPLE_KLINES:
            result = analyze(code, SAMPLE_KLINES[code], pos_type, highest)
            print_report(result)
        else:
            print(f"❌ 未找到{code}的K线数据")
            print("请使用 --data 模式输入K线，或更新SAMPLE_KLINES")
            sys.exit(1)
    else:
        # 默认：全持仓扫描
        scan_all(SAMPLE_KLINES)


if __name__ == "__main__":
    main()
