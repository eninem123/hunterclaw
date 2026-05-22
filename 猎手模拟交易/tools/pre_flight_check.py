#!/usr/bin/env python3
"""
Pre-flight 检查脚本
交易操作前必须执行，返回PASS/FAIL
用法：python3 pre_flight_check.py <操作类型> <股票代码> <数量>
操作类型：buy/sell/hold
"""

import sys
import json
from datetime import datetime, timedelta

# ============ 当前持仓配置（手动更新区域）============
POSITIONS = {
    "600377": {"name": "宁沪高速", "shares": 1000, "cost": 12.345, "type": "🟣防御", "stop_loss": 11.00, "stop_profit": [14.20], "buyable_today": 0},
    "600795": {"name": "国电电力", "shares": 2000, "cost": 4.903, "type": "🟢长线", "stop_loss": 4.51, "stop_profit": [5.40, 5.70, 5.90, 6.50], "buyable_today": 0},
    "600089": {"name": "特变电工", "shares": 100, "cost": 27.550, "type": "🔴短线", "stop_loss": 24.80, "stop_profit": [28.50], "buyable_today": 0},
    "601728": {"name": "中国电信", "shares": 400, "cost": 6.783, "type": "🟣防御", "stop_loss": 6.50, "stop_profit": [7.35, 8.00], "buyable_today": 0},
}

# 灯色评分（每日更新）
LIGHT_SCORE = 51  # 5/20灯色
LIGHT_COLOR = "🟡"  # 🟢≥75 / 🟡45-74 / 🔴<45

# 交易限制
MAX_DAILY_BUY = 3        # 单日买入≤3次
MAX_SINGLE_RATIO = 0.30  # 单只≤30%仓位
MIN_LOT = 100            # 最小1手=100股

# 今日已买入次数（每日重置）
TODAY_BUYS = 0

# 总资产（每日更新）
TOTAL_ASSET = 65138

# ============ T+1 计算 ============
# 记录今日买入的股票和数量（每日更新）
# 格式：{"代码": 今日买入股数}
TODAY_PURCHASES = {}

def get_sellable_shares(code):
    """计算今天可卖股数 = 总持仓 - 今日买入"""
    pos = POSITIONS.get(code)
    if not pos:
        return 0
    total = pos["shares"]
    bought_today = TODAY_PURCHASES.get(code, 0)
    return total - bought_today

def check_buy(code, quantity, current_price=None):
    """买入前检查"""
    errors = []
    warnings = []
    
    # 1. 灯色检查
    if LIGHT_SCORE < 45:
        errors.append(f"🔴灯色{LIGHT_SCORE}分<45，禁止新开仓！")
    elif LIGHT_SCORE < 60:
        # 黄灯区：禁止补仓（已有持仓加仓），只允许新开主线仓
        if code in POSITIONS:
            errors.append(f"🟡灯色{LIGHT_SCORE}分<60，禁止补仓！只允许新开主线仓")
        else:
            warnings.append(f"🟡灯色{LIGHT_SCORE}分，仅允许轻仓新开主线标的")
    elif LIGHT_SCORE < 75:
        warnings.append(f"🟡灯色{LIGHT_SCORE}分，谨慎轻仓")
    
    # 2. 整手检查
    if quantity % MIN_LOT != 0:
        errors.append(f"❌数量{quantity}不是{MIN_LOT}的整数倍！A股最小1手=100股")
    
    # 3. 单日买入次数
    if TODAY_BUYS >= MAX_DAILY_BUY:
        errors.append(f"❌今日已买入{TODAY_BUYS}次，达上限{MAX_DAILY_BUY}次")
    
    # 4. 单只仓位限制
    if current_price:
        buy_amount = current_price * quantity
        ratio = buy_amount / TOTAL_ASSET
        if ratio > MAX_SINGLE_RATIO:
            errors.append(f"❌买入金额{buy_amount:.0f}占总资产{ratio:.1%}，超过{MAX_SINGLE_RATIO:.0%}限制")
    
    # 5. 不碰300/688
    if code.startswith("300") or code.startswith("688"):
        errors.append(f"❌{code}是创业板/科创板，铁律不碰！")
    
    # 6. 不追涨停
    if current_price:
        pos = POSITIONS.get(code)
        # 如果是新买（非补仓），检查是否追高
        # 这里简单提示，具体需要外部数据判断是否涨停
    
    # 7. 补仓条件检查（如果是已有持仓加仓）
    if code in POSITIONS and current_price:
        pos = POSITIONS[code]
        loss_pct = (current_price - pos["cost"]) / pos["cost"]
        stop_dist = (current_price - pos["stop_loss"]) / current_price
        
        if loss_pct < -0.05:
            errors.append(f"❌浮亏{loss_pct:.1%}超-5%，禁止补仓！")
        
        if stop_dist < 0.01:
            errors.append(f"❌距止损仅{stop_dist:.1%}(<1%)，禁止补仓！")
        elif stop_dist < 0.03:
            errors.append(f"❌距止损仅{stop_dist:.1%}(<3%)，禁止补仓！太危险！")
        
        # 补仓条件：止跌缩量+价低于买入3-4%+距止损≥1%+未触止损
        if loss_pct > -0.03:
            warnings.append(f"⚠️浮亏仅{loss_pct:.1%}，补仓需浮亏3-4%以上")
    
    return errors, warnings

def check_sell(code, quantity, current_price=None):
    """卖出前检查"""
    errors = []
    warnings = []
    
    pos = POSITIONS.get(code)
    if not pos:
        errors.append(f"❌未找到{code}的持仓记录")
        return errors, warnings
    
    # 1. T+1检查
    sellable = get_sellable_shares(code)
    if quantity > sellable:
        bought_today = TODAY_PURCHASES.get(code, 0)
        errors.append(f"❌T+1限制！总持仓{pos['shares']}股，今日买入{bought_today}股，可卖{sellable}股，欲卖{quantity}股")
    
    # 2. 整手检查
    if quantity % MIN_LOT != 0:
        # 100股持仓全卖例外
        if not (pos["shares"] == quantity == MIN_LOT):
            errors.append(f"❌数量{quantity}不是{MIN_LOT}的整数倍")
    
    # 3. 止损距离
    if current_price:
        stop_dist = (current_price - pos["stop_loss"]) / current_price
        if stop_dist < 0.03:
            warnings.append(f"🚨距止损{pos['stop_loss']}仅{stop_dist:.1%}！<3%红色预警！")
    
    return errors, warnings

def main():
    if len(sys.argv) < 4:
        print("用法: python3 pre_flight_check.py <buy|sell> <股票代码> <数量> [当前价格]")
        print("示例: python3 pre_flight_check.py buy 601728 300 6.60")
        print("示例: python3 pre_flight_check.py sell 601728 300 6.50")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    code = sys.argv[2]
    quantity = int(sys.argv[3])
    current_price = float(sys.argv[4]) if len(sys.argv) >= 5 else None
    
    print("=" * 50)
    print(f"📋 Pre-flight 检查 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"操作：{action.upper()} {code} {quantity}股" + (f" @ {current_price}" if current_price else ""))
    print("=" * 50)
    
    # 基础信息
    if code in POSITIONS:
        pos = POSITIONS[code]
        print(f"\n📊 持仓信息：{pos['name']} | {pos['shares']}股@{pos['cost']} | {pos['type']}")
        print(f"   止损：{pos['stop_loss']} | 止盈：{pos['stop_profit']}")
        sellable = get_sellable_shares(code)
        print(f"   T+1可卖：{sellable}股")
        if current_price:
            stop_dist = (current_price - pos["stop_loss"]) / current_price * 100
            pnl = (current_price - pos["cost"]) * pos["shares"]
            pnl_pct = (current_price - pos["cost"]) / pos["cost"] * 100
            print(f"   距止损：{stop_dist:.1f}% | 浮盈亏：{pnl:+.0f}元({pnl_pct:+.1f}%)")
    
    print(f"\n💡 灯色：{LIGHT_COLOR}{LIGHT_SCORE}分", end="")
    if LIGHT_SCORE < 45:
        print(" → 禁止新开仓！")
    elif LIGHT_SCORE < 75:
        print(" → 谨慎轻仓")
    else:
        print(" → 可积极布局")
    
    # 执行检查
    if action == "buy":
        errors, warnings = check_buy(code, quantity, current_price)
    elif action == "sell":
        errors, warnings = check_sell(code, quantity, current_price)
    else:
        print(f"\n❌未知操作类型：{action}，只支持 buy/sell")
        sys.exit(1)
    
    # 输出结果
    if warnings:
        print("\n⚠️ 警告：")
        for w in warnings:
            print(f"  {w}")
    
    if errors:
        print("\n❌ 不通过：")
        for e in errors:
            print(f"  {e}")
        print("\n" + "=" * 50)
        print("🔴 结论：FAIL — 禁止执行此操作！")
        print("=" * 50)
        sys.exit(1)
    else:
        print("\n" + "=" * 50)
        print("🟢 结论：PASS — 可以执行")
        print("=" * 50)
        sys.exit(0)

if __name__ == "__main__":
    main()
