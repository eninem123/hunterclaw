#!/usr/bin/env python3
"""
全市场扫描脚本
从主力资金流入TOP数据中筛选候选标的
用法：python3 market_scanner.py
输出：JSON格式的候选池列表
"""

import json
from datetime import datetime

# ============ 扫描配置 ============

# 排除规则
EXCLUDE_PREFIXES = ["300", "688"]  # 不碰创业板/科创板
EXCLUDE_ST = True  # 排除ST股

# 资金流入门槛（亿元）
MIN_FLOW = 3.0

# 单价上限（元）- 超过的太贵1手买不起
MAX_PRICE = 150.0

# 仓位限制：1手金额不超过可用资金的1/10
AVAILABLE_CASH = 37000  # 每日更新
MAX_LOT_RATIO = 0.10  # 1手不超过可用资金10%

# ============ 持仓去重 ============
HELD_CODES = ["600377", "600795", "600089", "601728"]  # 已持仓不再推荐

# ============ 数据输入区 ============
# 每日从search_web获取主力资金流入TOP数据后填入
# 格式：[{"code":"600584","name":"长电科技","price":66.22,"flow":12.88,"sector":"半导体封测"}, ...]
MARKET_DATA = [
    # ===== 在这里粘贴当日扫描数据 =====
    # 示例（5/20数据）：
    # {"code": "600584", "name": "长电科技", "price": 66.22, "flow": 12.88, "sector": "半导体封测"},
]

def scan(data=None):
    """执行扫描，返回候选池"""
    if data is None:
        data = MARKET_DATA
    
    candidates = []
    rejected = []
    
    for item in data:
        code = item["code"]
        name = item["name"]
        price = item.get("price", 0)
        flow = item.get("flow", 0)
        sector = item.get("sector", "未知")
        
        reject_reasons = []
        
        # 1. 排除创业板/科创板
        if any(code.startswith(p) for p in EXCLUDE_PREFIXES):
            reject_reasons.append(f"代码{code}为创业板/科创板，排除")
        
        # 2. 排除ST
        if EXCLUDE_ST and ("ST" in name or "st" in name):
            reject_reasons.append("ST股，排除")
        
        # 3. 排除已持仓
        if code in HELD_CODES:
            reject_reasons.append("已持仓，排除")
        
        # 4. 资金流入门槛
        if flow < MIN_FLOW:
            reject_reasons.append(f"流入{flow}亿<{MIN_FLOW}亿，排除")
        
        # 5. 价格上限
        if price > MAX_PRICE:
            reject_reasons.append(f"价格{price}>{MAX_PRICE}，排除")
        
        # 6. 1手金额不超过可用资金10%
        lot_amount = price * 100
        if lot_amount > AVAILABLE_CASH * MAX_LOT_RATIO:
            reject_reasons.append(f"1手{lot_amount:.0f}元>可用资金{AVAILABLE_CASH*MAX_LOT_RATIO:.0f}，排除")
        
        if reject_reasons:
            rejected.append({"code": code, "name": name, "reasons": reject_reasons})
        else:
            # 计算评分
            score = 0
            # 资金流入权重
            if flow >= 10:
                score += 30
            elif flow >= 5:
                score += 20
            elif flow >= 3:
                score += 10
            
            # 价格合理性（越便宜1手越灵活）
            if lot_amount <= 2000:
                score += 15
            elif lot_amount <= 5000:
                score += 10
            elif lot_amount <= 10000:
                score += 5
            
            candidates.append({
                "code": code,
                "name": name,
                "price": price,
                "flow": flow,
                "sector": sector,
                "lot_amount": lot_amount,
                "score": score,
                "status": "🔍待验证三位一体+FM≥80"
            })
    
    # 按评分排序
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    return candidates, rejected


def main():
    print("=" * 60)
    print(f"🔍 全市场扫描 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    print(f"\n📋 扫描参数：")
    print(f"  资金流入门槛：≥{MIN_FLOW}亿")
    print(f"  价格上限：≤{MAX_PRICE}元")
    print(f"  可用资金：{AVAILABLE_CASH}元")
    print(f"  1手上限：{AVAILABLE_CASH * MAX_LOT_RATIO:.0f}元(10%)")
    print(f"  已持仓排除：{HELD_CODES}")
    
    candidates, rejected = scan()
    
    if not MARKET_DATA:
        print("\n⚠️ 未填入当日数据！请先通过search_web获取主力资金流入TOP数据，")
        print("   填入MARKET_DATA变量后重新运行。")
        print("\n📌 数据获取方式：")
        print("   搜索关键词：'A股今日主力资金流入排名' 或 '今日资金净流入排行'")
        print("   重点关注：流入>3亿 + 非创业板科创板 + 非ST + 1手可买")
        return
    
    print(f"\n📊 扫描结果：输入{len(MARKET_DATA)}只 → 通过{len(candidates)}只 → 排除{len(rejected)}只")
    
    if candidates:
        print(f"\n✅ 候选池（按评分排序）：")
        print("-" * 60)
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c['name']}({c['code']}) | {c['price']}元 | 流入{c['flow']}亿 | {c['sector']}")
            print(f"     1手={c['lot_amount']:.0f}元 | 评分{c['score']} | {c['status']}")
    
    if rejected:
        print(f"\n❌ 排除列表：")
        print("-" * 60)
        for r in rejected:
            print(f"  {r['name']}({r['code']})：{'；'.join(r['reasons'])}")
    
    # 输出JSON供程序读取
    print(f"\n📄 JSON输出：")
    print(json.dumps(candidates, ensure_ascii=False, indent=2))
    
    print(f"\n{'='*60}")
    print(f"📌 下一步：候选标的需通过三位一体验证+FM≥80才能行动")
    print(f"⚠️ 候选池≠买入建议！只是待验证标的列表")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
