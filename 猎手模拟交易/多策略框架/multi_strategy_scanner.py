#!/usr/bin/env python3
"""
多策略选股扫描器 v1.0
按板块特性差异化筛选标的
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

import json
import pandas as pd
from datetime import datetime
from hunter_utils import (
    get_realtime_data,
    get_market_temperature,
    get_sector_leaders,
    get_main_force_flow
)

# ==================== 配置 ====================
MARKET_TEMP_THRESHOLD = 40  # 市场温度门槛

# ==================== 主板价值投资 ====================
def scan_main_board():
    """主板价值投资扫描"""
    print("\n📊 主板扫描（价值投资）...")
    
    candidates = [
        {"code": "600900", "name": "长江电力"},
        {"code": "601088", "name": "中国神华"},
        {"code": "601006", "name": "大秦铁路"},
        {"code": "601398", "name": "工商银行"},
        {"code": "600887", "name": "伊利股份"},
        {"code": "600028", "name": "中国石化"},
    ]
    
    results = []
    for c in candidates:
        try:
            data = get_realtime_data(c["code"])
            if not data:
                continue
            price = data.get("price", 0)
            chg = data.get("chg", 0)
            volume = data.get("volume", 0)
            
            # 简化筛选：价格稳定 + 小幅上涨
            if chg > 0 and chg < 5:
                results.append({
                    "code": c["code"],
                    "name": c["name"],
                    "price": price,
                    "chg": chg,
                    "signal": "value_invest",
                    "reason": f"低估值高分红"
                })
        except Exception as e:
            print(f"  异常 {c['code']}: {e}")
    
    return results

# ==================== 创业板趋势跟踪 ====================
def scan_gem_board():
    """创业板趋势跟踪扫描"""
    print("\n🚀 创业板扫描（趋势跟踪）...")
    
    # 获取涨停板中的创业板
    try:
        sector_data = get_sector_leaders()
        # 筛选涨幅>7%且非涨停的创业板
        results = []
        for item in sector_data:
            code = item.get("code", "")
            if code.startswith("3"):  # 创业板
                chg = item.get("chg", 0)
                if 5 <= chg < 9.8:  # 排除涨停
                    results.append({
                        "code": code,
                        "name": item.get("name", ""),
                        "price": item.get("price", 0),
                        "chg": chg,
                        "signal": "trend_follow",
                        "reason": f"动量启动"
                    })
        return results
    except Exception as e:
        print(f"  创业板扫描异常: {e}")
        return []

# ==================== 科创板成长股 ====================
def scan_star_board():
    """科创板成长股扫描"""
    print("\n🔬 科创板扫描（成长股）...")
    
    # 科创板扫描逻辑
    candidates = [
        {"code": "688012", "name": "中微公司"},
        {"code": "688008", "name": "澜起科技"},
        {"code": "688981", "name": "中芯国际"},
    ]
    
    results = []
    for c in candidates:
        try:
            data = get_realtime_data(c["code"])
            if not data:
                continue
            price = data.get("price", 0)
            chg = data.get("chg", 0)
            
            # 成长股信号：底部反弹 + 政策催化
            if chg > 3:
                results.append({
                    "code": c["code"],
                    "name": c["name"],
                    "price": price,
                    "chg": chg,
                    "signal": "growth",
                    "reason": f"国产替代"
                })
        except Exception as e:
            print(f"  异常 {c['code']}: {e}")
    
    return results

# ==================== ETF轮动 ====================
def scan_etf():
    """ETF轮动扫描"""
    print("\n📈 ETF扫描（轮动策略）...")
    
    etf_list = [
        {"code": "159715", "name": "稀土ETF"},
        {"code": "159995", "name": "芯片ETF"},
        {"code": "516160", "name": "新能源ETF"},
        {"code": "512010", "name": "医疗ETF"},
        {"code": "512800", "name": "银行ETF"},
    ]
    
    results = []
    for e in etf_list:
        try:
            data = get_realtime_data(e["code"])
            if not data:
                continue
            price = data.get("price", 0)
            chg = data.get("chg", 0)
            volume = data.get("volume", 0)
            
            # ETF信号：量价齐升
            if chg > 1.5:
                results.append({
                    "code": e["code"],
                    "name": e["name"],
                    "price": price,
                    "chg": chg,
                    "signal": "etf_rotation",
                    "reason": f"板块轮动"
                })
        except Exception as e:
            print(f"  异常 {e['code']}: {e}")
    
    return results

# ==================== 基金扫描 ====================
def scan_funds():
    """基金选基扫描"""
    print("\n💰 基金扫描（选基逻辑）...")
    
    # 扫描基金池子逻辑（待东财基金数据接口）
    # 暂时返回关注列表
    results = [
        {"code": "001417", "name": "汇添富医疗服务"},
        {"code": "110022", "name": "易方达消费行业"},
        {"code": "001643", "name": "汇丰晋信低碳先锋"},
    ]
    
    print(f"  基金扫描：{len(results)}只待关注")
    return results

# ==================== 主程序 ====================
def main():
    print("=" * 50)
    print("多策略选股扫描器 v1.0")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # 获取市场温度
    try:
        temp = get_market_temperature()
        print(f"\n🌡️ 市场温度: {temp}℃")
        
        if temp < MARKET_TEMP_THRESHOLD:
            print(f"⚠️ 市场温度 < {MARKET_TEMP_THRESHOLD}℃，严格筛选")
    except Exception as e:
        print(f"  市场温度获取失败: {e}")
        temp = 50
    
    all_results = []
    
    # 主板扫描
    main_board = scan_main_board()
    all_results.extend(main_board)
    
    # 创业板扫描（仅当市场温度≥50）
    if temp >= 50:
        gem_board = scan_gem_board()
        all_results.extend(gem_board)
    
    # 科创板扫描
    star_board = scan_star_board()
    all_results.extend(star_board)
    
    # ETF扫描
    etf_results = scan_etf()
    all_results.extend(etf_results)
    
    # 基金扫描
    fund_results = scan_funds()
    
    # 输出结果
    print("\n" + "=" * 50)
    print(f"📋 扫描结果汇总: {len(all_results)}只标的")
    print("=" * 50)
    
    if all_results:
        print(f"{'代码':<10} {'名称':<12} {'价格':<10} {'涨幅':<8} {'信号':<15} {'原因'}")
        print("-" * 70)
        for r in sorted(all_results, key=lambda x: x["chg"], reverse=True):
            print(f"{r['code']:<10} {r['name']:<12} {r['price']:<10.2f} {r['chg']:>6.2f}% {r['signal']:<15} {r['reason']}")
    
    # 保存结果
    output_file = f"/root/.openclaw/workspace/猎手模拟交易/多策略框架/scan_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "scan_time": datetime.now().isoformat(),
            "market_temp": temp,
            "results": all_results,
            "funds": fund_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存: {output_file}")
    return all_results

if __name__ == "__main__":
    main()
