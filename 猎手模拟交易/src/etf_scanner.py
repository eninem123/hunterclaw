#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF & 黄金扫描模块 v1.0 (2026-05-18)
"""

import json
import re
import urllib.parse

# ── ETF代码库 ─────────────────────────────────────────────────────────────
ETF_CATEGORIES = {
    "科技": [
        ("513310", "中韩半导体ETF"),
        ("159509", "纳指科技ETF景顺"),
        ("513290", "纳指生物科技ETF汇添富"),
    ],
    "互联网": [
        ("159688", "恒生互联网ETF华安"),
        ("513220", "中概互联ETF招商"),
        ("513050", "中概互联网ETF易方达"),
    ],
    "医药": [
        ("159502", "标普生物科技ETF嘉实"),
        ("513120", "港股创新药ETF广发"),
    ],
    "消费": [],
    "油气": [
        ("513350", "标普油气ETF富国"),
    ],
    "黄金ETF": [
        ("518880", "黄金ETF华安"),
        ("517520", "黄金股ETF永赢"),
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
def http_get_gbk(url, timeout=8):
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("gbk", errors="replace")
    except:
        return None

def http_get_utf8(url, timeout=8):
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except:
        return None

# ── ETF实时行情获取 ───────────────────────────────────────────────────────
def get_etf_realtime_data(codes_list):
    """
    获取ETF/股票实时行情
    参数: codes_list - 字符串列表 ['513310', '518880', ...]
    """
    if not codes_list:
        return {}
    result = {}
    try:
        # codes_list 应该是字符串列表，直接构建URL
        codes_str = ",".join(["sh" + str(code) for code in codes_list])
        url = "https://qt.gtimg.cn/q=" + codes_str
        raw = http_get_gbk(url)
        if not raw:
            return result
        for line in raw.strip().split("\n"):
            if "=" not in line or '"' not in line:
                continue
            try:
                # 格式: v_sh513310="1~中韩半导体ETF华泰柏瑞~513310~6.134~..."
                code_match = re.search(r'v_sh(\w+)=', line)
                if not code_match:
                    continue
                code = code_match.group(1)
                
                data_match = re.search(r'"([^"]+)"', line)
                if not data_match:
                    continue
                parts = data_match.group(1).split("~")
                
                # 索引3=当前价, 4=昨收, 32=涨跌幅%
                price = float(parts[3]) if len(parts) > 3 and parts[3] not in ["-", ""] else 0
                prev_close = float(parts[4]) if len(parts) > 4 and parts[4] not in ["-", ""] else price
                chg_pct = float(parts[32]) if len(parts) > 32 and parts[32] not in ["-", ""] else 0
                amount = float(parts[37]) if len(parts) > 37 and parts[37] not in ["-", ""] else 0
                
                result[code] = {
                    "price": price,
                    "prev_close": prev_close,
                    "chg_pct": chg_pct,
                    "amount": amount,
                }
            except (ValueError, IndexError, AttributeError):
                continue
    except Exception as e:
        print(f"  Warning: ETF行情获取异常 {e}")
    return result

# ── 获取近3日主力资金净流入 ────────────────────────────────────────────────
def get_money_flow_3day(code, timeout=3):
    """获取近3日主力资金净流入（备用方案：使用涨跌估算）"""
    # 由于资金流接口可能不可用，使用备用方案
    # 通过价格变化估算资金流向（简化版）
    prefix = "sz" if code.startswith(("00", "30", "002", "003", "301")) else "sh"
    secid = prefix + code
    try:
        # 尝试获取资金流
        url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        params = {
            "lmt": "3",
            "klt": "101",
            "secid": secid,
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63"
        }
        raw = http_get_utf8(url + "?" + urllib.parse.urlencode(params), timeout=timeout)
        if raw and len(raw) > 50:
            data = json.loads(raw)
            klines = data.get("data", {}).get("klines", [])
            total_inflow = 0
            for kline in klines:
                parts = kline.split(",")
                if len(parts) >= 7:
                    try:
                        total_inflow += float(parts[6])
                    except:
                        pass
            if total_inflow > 0:
                trend = "净流入"
            elif total_inflow < 0:
                trend = "净流出"
            else:
                trend = "持平"
            return {"inflow_3d": total_inflow, "trend": trend}
    except:
        pass
    # 备用：返回未知，让后续逻辑处理
    return {"inflow_3d": 0, "trend": "unknown"}

# ── 获取国际/国内金价 ─────────────────────────────────────────────────────
def get_gold_price():
    """获取国际金价和国内金价"""
    result = {
        "intl_price": 0,
        "intl_chg": 0,
        "domestic_price": 0,
        "domestic_chg": 0,
        "source": "未知"
    }
    
    # 方法1: 尝试腾讯伦敦金接口
    try:
        url = "https://qt.gtimg.cn/q=hf_GC,hf_XAU"
        raw = http_get_gbk(url)
        if raw:
            for line in raw.strip().split("\n"):
                if '"' not in line:
                    continue
                try:
                    data_match = re.search(r'"([^"]+)"', line)
                    if not data_match:
                        continue
                    parts = data_match.group(1).split("~")
                    if len(parts) > 4:
                        price_str = parts[1].replace(",", "")
                        chg_str = parts[4].replace(",", "")
                        if price_str not in ["-", ""]:
                            result["intl_price"] = float(price_str)
                        if chg_str not in ["-", ""]:
                            result["intl_chg"] = float(chg_str)
                        result["source"] = "伦敦金"
                        break
                except:
                    pass
    except:
        pass
    
    # 方法2: 尝试东方财富国际商品接口
    if result["intl_price"] == 0:
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": "1", "pz": "5", "po": "1", "np": "1",
                "fltt": "2", "invt": "2", "fid": "f3",
                "fs": "b:MK1004",  # 国际商品
                "fields": "f2,f3,f4,f12,f14"
            }
            raw = http_get_utf8(url + "?" + urllib.parse.urlencode(params))
            if raw:
                data = json.loads(raw)
                stocks = data.get("data", {}).get("diff", [])
                for s in stocks:
                    name = s.get("f14", "").lower()
                    if "黄金" in name or "gold" in name or "gc" in name:
                        result["intl_price"] = float(s.get("f2", 0))
                        result["intl_chg"] = float(s.get("f3", 0))
                        result["source"] = "国际金"
                        break
        except:
            pass
    
    # 方法3: 获取国内金价（上金所Au99.99）
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "5", "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fid": "f3",
            "fs": "m:223+r:1",
            "fields": "f2,f3,f4,f5,f6,f12,f14"
        }
        raw = http_get_utf8(url + "?" + urllib.parse.urlencode(params))
        if raw:
            stocks = json.loads(raw).get("data", {}).get("diff", [])
            if stocks:
                result["domestic_price"] = float(stocks[0].get("f2", 0))
                result["domestic_chg"] = float(stocks[0].get("f3", 0))
    except:
        pass
    
    return result

# ── 动态获取消费ETF ───────────────────────────────────────────────────────
def get_consume_etf_list():
    """从东方财富动态获取消费类ETF"""
    consume_etfs = []
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1", "pz": "10", "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fid": "f3",
            "fs": "b:MK0021,b:MK0022,b:MK0023",
            "fields": "f2,f3,f6,f12,f14"
        }
        raw = http_get_utf8(url + "?" + urllib.parse.urlencode(params))
        if raw:
            stocks = json.loads(raw).get("data", {}).get("diff", [])
            for s in stocks[:5]:
                code = str(s.get("f12", ""))
                name = s.get("f14", "")
                if code.startswith("51") or code.startswith("15"):
                    consume_etfs.append((code, name))
    except:
        pass
    return consume_etfs

# ── ETF主扫描函数 ─────────────────────────────────────────────────────────
def scan_etf():
    """ETF综合扫描"""
    print("\n" + "━" * 50)
    print("【ETF & 黄金扫描】开始...")
    result = {"signals": [], "warnings": []}
    ETF_CATEGORIES["消费"] = get_consume_etf_list()
    
    HIGH_GAIN = 5.0
    MIN_AMOUNT = 5000  # 万元
    
    for category, etf_list in ETF_CATEGORIES.items():
        if not etf_list:
            continue
        print(f"\n  📊 [{category}]扫描中...")
        realtime_data = get_etf_realtime_data([code for code, _ in etf_list])
        
        for code, name in etf_list:
            info = realtime_data.get(code, {})
            if not info or info.get("price", 0) == 0:
                print(f"    ⚠️ {name}({code}) 无行情数据")
                continue
            
            price = info.get("price", 0)
            chg_pct = info.get("chg_pct", 0)
            amount = info.get("amount", 0) / 10000  # 转换为亿元
            
            # 跳过资金流获取（接口不稳定），使用默认值
            inflow_3d = 0
            flow_trend = "unknown"
            
            # 三位一体铁律检查
            trinity_pass = True
            trinity_reasons = []
            
            if chg_pct > HIGH_GAIN:
                trinity_pass = False
                trinity_reasons.append(f"涨幅{chg_pct:.2f}%>5%")
            
            if amount < MIN_AMOUNT:
                trinity_pass = False
                trinity_reasons.append(f"成交额{amount:.0f}万<5000万")
            
            # 注意：主力资金检查已暂时禁用（接口不稳定）
            
            signal = {
                "category": category,
                "code": code,
                "name": name,
                "price": price,
                "chg_pct": chg_pct,
                "amount": amount,
                "inflow_3d": inflow_3d,
                "trinity_pass": trinity_pass,
                "trinity_reasons": trinity_reasons,
                "is_gold": category == "黄金ETF",
            }
            
            if trinity_pass:
                result["signals"].append(signal)
                inflow_str = f"3日主力{inflow_3d/10000:+.2f}亿" if inflow_3d != 0 else "资金数据缺失"
                print(f"    ✅ {name}({code}) 现价{price:.3f} 涨{chg_pct:+.2f}% 成交{amount:.2f}亿 {inflow_str} ✅")
            else:
                result["warnings"].append(signal)
                reasons_str = ",".join(trinity_reasons)
                print(f"    ⚠️ {name}({code}) 现价{price:.3f} 涨{chg_pct:+.2f}% [{reasons_str}]")
    
    return result

# ── 黄金专项扫描 ──────────────────────────────────────────────────────────
def scan_gold():
    """黄金专项扫描"""
    print("\n" + "━" * 50)
    print("【黄金专项扫描】开始...")
    
    result = {
        "intl_gold": {},
        "gold_stocks": [],
        "recommendation": ""
    }
    
    gold_price = get_gold_price()
    result["intl_gold"] = gold_price
    
    if gold_price["intl_price"] > 0:
        trend_icon = "📈" if gold_price["intl_chg"] > 0 else "📉"
        print(f"  {trend_icon} 国际金价: ${gold_price['intl_price']:.2f} ({gold_price['intl_chg']:+.2f}%) [{gold_price['source']}]")
    else:
        print("  ⚠️ 国际金价获取失败")
    
    if gold_price["domestic_price"] > 0:
        print(f"  🏛️ 国内金价(Au99.99): {gold_price['domestic_price']:.2f} ({gold_price['domestic_chg']:+.2f}%)")
    
    print("\n  📊 [黄金股]扫描中...")
    gold_stocks_data = get_etf_realtime_data([code for code, _ in GOLD_STOCKS])
    
    for code, name in GOLD_STOCKS:
        info = gold_stocks_data.get(code, {})
        if not info or info.get("price", 0) == 0:
            continue
        
        price = info.get("price", 0)
        chg_pct = info.get("chg_pct", 0)
        
        # 跳过资金流获取（接口不稳定）
        inflow_3d = 0
        
        stock_signal = {
            "code": code,
            "name": name,
            "price": price,
            "chg_pct": chg_pct,
            "inflow_3d": inflow_3d,
            "recommend": chg_pct < 5,  # 简化为：只要涨幅<5%就推荐
        }
        result["gold_stocks"].append(stock_signal)
        
        rec_icon = "✅" if stock_signal["recommend"] else "⚠️"
        inflow_str = f"主力{inflow_3d/10000:+.2f}亿" if inflow_3d != 0 else "资金数据缺失"
        print(f"    {rec_icon} {name}({code}) 现价{price:.2f} 涨{chg_pct:+.2f}% {inflow_str}")
    
    # 综合判断
    if gold_price["intl_price"] > 0:
        if gold_price["intl_chg"] > 2:
            result["recommendation"] = "国际金价大涨，注意回调风险"
        elif gold_price["intl_chg"] > 0:
            result["recommendation"] = "金价偏强，可持有黄金ETF"
        elif gold_price["intl_chg"] < -2:
            result["recommendation"] = "金价回调，等待企稳信号"
        else:
            result["recommendation"] = "金价震荡，观望为主"
    
    return result

# ── 报告生成 ───────────────────────────────────────────────────────────────
def generate_report(etf_result, gold_result):
    """生成ETF和黄金扫描报告"""
    lines = []
    icons = {"科技": "💻", "互联网": "🌐", "医药": "💊", "消费": "🛒", "油气": "⛽", "黄金ETF": "🥇", "黄金股": "🥇"}
    
    lines.append("")
    lines.append("━" * 52)
    lines.append("【ETF & 黄金扫描报告】")
    lines.append("━" * 52)
    
    # 金价信息
    if gold_result.get("intl_gold", {}).get("intl_price", 0) > 0:
        gold = gold_result["intl_gold"]
        trend = "📈" if gold["intl_chg"] > 0 else "📉"
        lines.append(f"{trend} 国际金价: ${gold['intl_price']:.2f} ({gold['intl_chg']:+.2f}%)")
    if gold_result.get("domestic_price", 0) > 0:
        lines.append(f"🏛️ 国内金价: {gold_result['domestic_price']:.2f} ({gold_result['domestic_chg']:+.2f}%)")
    if gold_result.get("recommendation"):
        lines.append(f"💡 {gold_result['recommendation']}")
    
    # ETF推荐信号
    if etf_result["signals"]:
        lines.append("")
        lines.append("✅ 【ETF推荐信号】")
        for sig in etf_result["signals"]:
            cat = sig["category"]
            icon = icons.get(cat, "📊")
            inf = f"主力净流入{sig['inflow_3d']/10000:.2f}亿" if sig["inflow_3d"] > 0 else f"主力净流出{abs(sig['inflow_3d'])/10000:.2f}亿"
            lines.append(f"  {icon}[{cat}] {sig['name']}({sig['code']}) 现价{sig['price']:.3f} 涨{sig['chg_pct']:+.2f}% {inf} ✅")
    
    # ETF观望信号
    if etf_result["warnings"]:
        lines.append("")
        lines.append("⚠️ 【ETF观望信号】(涨幅>5%或流动性不足)")
        shown = set()
        for sig in etf_result["warnings"]:
            cat = sig["category"]
            if cat in shown:
                continue
            shown.add(cat)
            icon = icons.get(cat, "📊")
            lines.append(f"  {icon}[{cat}] {sig['name']}({sig['code']}) 涨{sig['chg_pct']:+.2f}% {', '.join(sig['trinity_reasons'])}")
    
    # 黄金股
    if gold_result.get("gold_stocks"):
        lines.append("")
        lines.append("🥇 【黄金股】")
        for gs in gold_result["gold_stocks"][:4]:
            rec = "✅" if gs["recommend"] else "⚠️"
            inf = f"主力{gs['inflow_3d']/10000:+.2f}亿" if gs["inflow_3d"] != 0 else "资金数据缺失"
            lines.append(f"  {rec} {gs['name']}({gs['code']}) 现价{gs['price']:.2f} 涨{gs['chg_pct']:+.2f}% {inf}")
    
    lines.append("━" * 52)
    return "\n".join(lines)

# ── 主入口函数 ────────────────────────────────────────────────────────────
def pick_best_etf_gold(max_count=3):
    """ETF和黄金综合扫描主入口"""
    etf_result = scan_etf()
    gold_result = scan_gold()
    
    all_signals = etf_result["signals"].copy()
    
    # 添加黄金股推荐
    for gs in gold_result.get("gold_stocks", []):
        if gs["recommend"]:
            gs_copy = gs.copy()
            gs_copy["category"] = "黄金股"
            gs_copy["is_gold_stock"] = True
            all_signals.append(gs_copy)
    
    # 按主力资金排序
    all_signals.sort(key=lambda x: x.get("inflow_3d", 0), reverse=True)
    top_signals = all_signals[:max_count]
    
    # 生成并打印报告
    report = generate_report(etf_result, gold_result)
    print(report)
    
    return {
        "signals": top_signals,
        "all_signals": all_signals,
        "etf_result": etf_result,
        "gold_result": gold_result,
        "report": report,
    }

# ── CLI测试入口 ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 52)
    result = pick_best_etf_gold(max_count=3)
    print(f"\n最终入选({len(result['signals'])}只):")
    for s in result["signals"]:
        print(f"  {s['category']} {s['name']}({s['code']}) 涨{s['chg_pct']:+.2f}%")
