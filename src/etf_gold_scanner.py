#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF & 黄金扫描器 v3.0 (2026-05-18)
【简化版】去掉不稳定的主力资金接口，专注行情扫描
"""

import re
import urllib.request
from datetime import datetime

# ── ETF代码库 ─────────────────────────────────────────────────────────────
ETF_CATEGORIES = {
    "科技": [
        ("513310", "中韩半导体ETF"),
        ("159509", "纳指科技ETF景顺"),
        ("513290", "纳指生物科技ETF"),
    ],
    "互联网": [
        ("159688", "恒生互联网ETF"),
        ("513220", "中概互联ETF"),
        ("513050", "中概互联网ETF"),
    ],
    "医药": [
        ("159502", "标普生物科技ETF"),
        ("513120", "港股创新药ETF"),
    ],
    "油气": [
        ("513350", "标普油气ETF"),
    ],
    "黄金ETF": [
        ("518880", "黄金ETF华安"),
        ("517520", "黄金股ETF"),
        ("159830", "金ETF天弘"),
    ],
}

GOLD_STOCKS = [
    ("600547", "山东黄金"),
    ("601899", "紫金矿业"),
    ("600988", "赤峰黄金"),
    ("000975", "银泰黄金"),
]

# ── HTTP工具 ──────────────────────────────────────────────────────────────
def http_get_gbk(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("gbk", errors="replace")
    except:
        return None

# ── 实时行情获取 ──────────────────────────────────────────────────────────
def get_realtime_data(codes_list, market_prefix="sh"):
    if not codes_list:
        return {}
    result = {}
    try:
        codes_str = ",".join([f"{market_prefix}{str(code)}" for code in codes_list])
        url = f"https://qt.gtimg.cn/q={codes_str}"
        raw = http_get_gbk(url)
        if not raw:
            return result
        for line in raw.strip().split("\n"):
            if "=" not in line or '"' not in line:
                continue
            try:
                code_match = re.search(rf'v_{market_prefix}(\w+)=', line)
                if not code_match:
                    continue
                code = code_match.group(1)
                data_match = re.search(r'"([^"]+)"', line)
                if not data_match:
                    continue
                parts = data_match.group(1).split("~")
                price = float(parts[3]) if len(parts) > 3 and parts[3] not in ["-", ""] else 0
                chg_pct = float(parts[32]) if len(parts) > 32 and parts[32] not in ["-", ""] else 0
                amount = float(parts[37]) if len(parts) > 37 and parts[37] not in ["-", ""] else 0
                result[code] = {"price": price, "chg_pct": chg_pct, "amount": amount}
            except:
                continue
    except:
        pass
    return result

# ── 国际金价 ──────────────────────────────────────────────────────────────
def get_gold_price():
    result = {"intl_price": 0, "intl_chg": 0}
    try:
        url = "https://qt.gtimg.cn/q=hf_GC,hf_XAU"
        raw = http_get_gbk(url)
        if raw:
            for line in raw.strip().split("\n"):
                if '"' not in line:
                    continue
                try:
                    m = re.search(r'"([^"]+)"', line)
                    if m:
                        p = m.group(1).split("~")
                        if len(p) > 4 and p[1] not in ["-", ""]:
                            result["intl_price"] = float(p[1].replace(",", ""))
                            result["intl_chg"] = float(p[4].replace(",", ""))
                            break
                except:
                    pass
    except:
        pass
    return result

# ── 主扫描 ────────────────────────────────────────────────────────────────
def scan_all():
    print(f"\n{'='*52}")
    print(f"━━━ ETF & 黄金扫描 ━━━ [{datetime.now().strftime('%H:%M:%S')}]")
    print(f"{'='*52}")
    
    HIGH_GAIN = 5.0       # 涨幅>5%不推荐
    MIN_AMOUNT_WAN = 5000  # 成交额下限5000万（万元）
    
    signals = []
    warnings = []
    
    gold_price = get_gold_price()
    if gold_price["intl_price"] > 0:
        trend = "📈" if gold_price["intl_chg"] > 0 else "📉"
        print(f"\n{trend}[国际金价] ${gold_price['intl_price']:.2f} ({gold_price['intl_chg']:+.2f}%)")
    
    for category, etf_list in ETF_CATEGORIES.items():
        if not etf_list:
            continue
        print(f"\n【{category}ETF】扫描中...")
        data = get_realtime_data([code for code, _ in etf_list])
        
        for code, name in etf_list:
            info = data.get(code, {})
            if not info or info.get("price", 0) == 0:
                print(f"  ⚠️ {name}({code}) 无行情")
                continue
            
            price = info["price"]
            chg_pct = info["chg_pct"]
            amount_wan = info["amount"]  # 成交额（万元）
            amount_yi = amount_wan / 10000  # 转为亿元
            
            reasons = []
            if chg_pct > HIGH_GAIN:
                reasons.append(f"涨{chg_pct:.1f}%>5%")
            if amount_wan < MIN_AMOUNT_WAN:
                reasons.append(f"额{amount_yi:.2f}亿<0.5亿")
            
            sig = {"category": category, "code": code, "name": name,
                   "price": price, "chg_pct": chg_pct, "amount_yi": amount_yi, "reasons": reasons}
            
            if not reasons:
                signals.append(sig)
                print(f"  ✅ {name}({code}) 现价{price:.3f} 涨{chg_pct:+.2f}% 成交{amount_yi:.2f}亿")
            else:
                warnings.append(sig)
                reasons_str = ",".join(reasons)
                print(f"  ⚠️ {name}({code}) 涨{chg_pct:+.2f}% 成交{amount_yi:.2f}亿 [{reasons_str}]")
    
    print(f"\n【黄金股】扫描中...")
    gold_data = get_realtime_data([code for code, _ in GOLD_STOCKS])
    
    for code, name in GOLD_STOCKS:
        info = gold_data.get(code, {})
        if not info or info.get("price", 0) == 0:
            continue
        
        price = info["price"]
        chg_pct = info["chg_pct"]
        
        reasons = []
        if chg_pct > HIGH_GAIN:
            reasons.append(f"涨{chg_pct:.1f}%>5%")
        
        sig = {"category": "黄金股", "code": code, "name": name,
               "price": price, "chg_pct": chg_pct, "reasons": reasons}
        
        if not reasons:
            signals.append(sig)
            print(f"  ✅ {name}({code}) 现价{price:.2f} 涨{chg_pct:+.2f}%")
        else:
            warnings.append(sig)
            reasons_str = ",".join(reasons)
            print(f"  ⚠️ {name}({code}) 涨{chg_pct:+.2f}% [{reasons_str}]")
    
    print(f"\n{'='*52}")
    print("━━━ ETF & 黄金推荐 ━━━")
    print(f"{'='*52}")
    
    if signals:
        for s in signals[:8]:
            print(f"【{s['category']}】{s['name']}({s['code']}) 现价{s['price']:.3f} 涨{s['chg_pct']:+.2f}% ✅")
    else:
        print("当前无推荐信号（涨幅>5%或成交额<0.5亿）")
    
    return {"signals": signals[:8], "warnings": warnings}

if __name__ == "__main__":
    result = scan_all()
    print(f"\n推荐信号: {len(result['signals'])}只")
