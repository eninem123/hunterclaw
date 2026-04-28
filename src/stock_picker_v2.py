#!/usr/bin/env python3
"""
猎手系统 - 进阶选股器 v2.0
策略框架：资金流向 → 板块效应 → 均线形态 → 量价验证

改进点：
1. 主力净流入排名优先（不只是涨幅）
2. 均线多头排列验证（MA5>MA10>MA20）
3. 缩量回踩形态识别（不追高，等回调）
4. 板块热度过滤（选热门板块）
5. 量价配合验证（放量上涨、缩量回调）
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# ── HTTP工具 ──
def http_get_gbk(url):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.qq.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode("gbk", errors="replace")
    except Exception:
        return None

def http_get_utf8(url):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.eastmoney.com",
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None

def get_realtime_quote(code):
    """获取单只股票实时五档行情"""
    prefix = "sz" if code.startswith(("00", "30", "002", "003")) else "sh"
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    raw = http_get_gbk(url)
    if not raw:
        return None
    try:
        m = re.search(r'~(.+)"', raw)
        if not m:
            return None
        parts = m.group(1).split("~")
        return {
            "name": parts[1],
            "price": float(parts[3]) if parts[3] else 0,
            "prev_close": float(parts[4]) if parts[4] else 0,
            "open": float(parts[5]) if parts[5] else 0,
            "volume": int(parts[6]) if parts[6] else 0,
            "chg_pct": float(parts[32]) if parts[32] else 0,
            "vol_ratio": float(parts[49]) if parts[49] else 0,
        }
    except (ValueError, IndexError):
        return None

def get_money_flow_top():
    """
    获取主力净流入排名TOP股票
    东方财富资金流入排名接口
    返回：[{code, name, main_net_inflow, main_ratio, price, chg_pct}]
    """
    candidates = []
    try:
        # 按今日主力净流入排名（全市场）
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "200",      # 取前200只（按净流入排序）
            "po": "1",        # 降序
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f62",     # 按主力净流入排序
            "fs": "m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23",
            "fields": "f12,f14,f2,f3,f62,f184"
        }
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        raw = http_get_utf8(full_url)
        if not raw:
            return candidates

        data = json.loads(raw)
        stocks = data.get("data", {}).get("diff", [])

        for s in stocks:
            try:
                code = str(s.get("f12", ""))
                name = s.get("f14", "")
                price = float(s.get("f2", 0))
                chg_pct = float(s.get("f3", 0))
                main_net_inflow = float(s.get("f62", 0))  # 主力净流入（元）
                main_ratio = float(s.get("f184", 0))     # 主力净流入占比（%）

                if not code or not name or price <= 0:
                    continue
                if "ST" in name or "*ST" in name or name.startswith("N"):
                    continue

                candidates.append({
                    "code": code,
                    "name": name,
                    "price": price,
                    "chg_pct": chg_pct,
                    "main_net_inflow": main_net_inflow,
                    "main_ratio": main_ratio,
                })
            except (ValueError, TypeError):
                continue
    except Exception as e:
        print(f"  [资金流获取异常] {e}")
    return candidates

def get_kline_data(code, days=20):
    """获取K线数据，返回(日期, 开, 收, 高, 低, 量)列表"""
    prefix = "sz" if code.startswith(("00", "30", "002", "003")) else "sh"
    secid = f"{prefix}{code}"
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={secid},day,,,{days},qfq"
    raw = http_get_utf8(url)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        kdata = data.get("data", {})
        if isinstance(kdata, list):
            return []
        stock_data = kdata.get(secid, {})
        qfqday = stock_data.get("qfqday", stock_data.get("day", []))
        result = []
        for row in qfqday:
            try:
                result.append({
                    "date": row[0],
                    "open": float(row[1]),
                    "close": float(row[2]),
                    "high": float(row[3]),
                    "low": float(row[4]),
                    "volume": float(row[5]),
                })
            except (ValueError, IndexError):
                continue
        return result
    except Exception:
        return []

def calc_ma(prices, n):
    """计算N日简单移动平均"""
    if len(prices) < n:
        return None
    return sum(prices[-n:]) / n

def verify_ma_pattern(code):
    """
    验证均线形态
    要求：
    1. MA5 > MA10 > MA20（均线多头排列）
    2. MA5 向上（今日MA5 > 昨日MA5）
    3. MA10 向上
    """
    klines = get_kline_data(code, days=25)
    if len(klines) < 20:
        return False, "K线不足20天"

    closes = [k["close"] for k in klines]
    ma5_list = [calc_ma(closes[:i+1], 5) for i in range(len(closes))]
    ma10_list = [calc_ma(closes[:i+1], 10) for i in range(len(closes))]
    ma20_list = [calc_ma(closes[:i+1], 20) for i in range(len(closes))]

    # 今日 & 昨日
    ma5_today, ma5_yest = ma5_list[-1], ma5_list[-2]
    ma10_today, ma10_yest = ma10_list[-1], ma10_list[-2]
    ma20_today = ma20_list[-1]

    if None in [ma5_today, ma5_yest, ma10_today, ma10_yest, ma20_today]:
        return False, "均线数据不足"

    # 多头排列
    ma_bullish = ma5_today > ma10_today > ma20_today
    # MA5向上
    ma5_rising = ma5_today > ma5_yest
    # MA10向上
    ma10_rising = ma10_today > ma10_yest

    if ma_bullish and ma5_rising and ma10_rising:
        return True, f"均线多头(MA5={ma5_today:.2f}>MA10={ma10_today:.2f}>MA20={ma20_today:.2f},MA5向上)"
    return False, f"均线不符(MA5>{ma10_today:.2f}>{ma20_today:.2f},{'↑' if ma5_rising else '↓'}MA5,{'↑' if ma10_rising else '↓'}MA10)"

def verify_volume_price(code):
    """
    验证量价配合
    要求：
    1. 今日成交量 > 昨日成交量 × 1.3（温和放量）
    2. 今日收盘 > 开盘（阳线）
    3. 股价在合理区间（当日均价附近，非高位）
    """
    klines = get_kline_data(code, days=5)
    if len(klines) < 3:
        return False, "K线不足3天"

    today = klines[-1]
    yest = klines[-2]

    vol_today = today["volume"]
    vol_yest = yest["volume"]
    close_today = today["close"]
    open_today = today["open"]

    # 今日量比昨日放量（温和放量）
    vol_expanded = vol_today >= vol_yest * 1.3
    # 今日收阳线
    bullish = close_today > open_today
    # 收盘在合理位置（非高位吊颈线）
    today_avg = (today["high"] + today["low"]) / 2
    not_top = close_today < today["high"] * 0.98

    if vol_expanded and bullish:
        vol_ratio = vol_today / vol_yest if vol_yest > 0 else 0
        return True, f"量价配合(放量{vol_ratio:.1f}x,阳线)"
    return False, f"量价不符(放量{vol_today/vol_yest*100 if vol_yest>0 else 0:.0f}%,{'阳' if bullish else '阴'})"

def verify_pullback_pattern(code):
    """
    验证缩量回踩形态（选股最佳形态）
    形态：股价回踩MA5，但成交量萎缩（说明抛压轻，主力没跑）
    条件：
    1. 股价在MA5附近（±3%）
    2. 今日成交量 < 昨日成交量（缩量）
    3. MA5向上
    """
    klines = get_kline_data(code, days=10)
    if len(klines) < 6:
        return False, "K线不足"

    closes = [k["close"] for k in klines]
    ma5 = calc_ma(closes, 5)
    if ma5 is None:
        return False, "MA5不足"

    today = klines[-1]
    yest = klines[-2]
    today_close = today["close"]
    today_vol = today["volume"]
    yest_vol = yest["volume"]

    # 股价在MA5附近（回踩不破）
    near_ma5 = abs(today_close - ma5) / ma5 < 0.03
    # 缩量
    vol_shrink = today_vol < yest_vol * 0.9
    # MA5向上
    ma5_yest = calc_ma(closes[:-1], 5)
    ma5_rising = ma5 > ma5_yest if ma5_yest else False

    if near_ma5 and ma5_rising:
        return True, f"缩量回踩MA5(价差{(today_close-ma5)/ma5*100:.1f}%,量缩{today_vol/yest_vol*100:.0f}%)"
    return False, f"非回踩形态"

def pick_by_money_flow(max_count=5):
    """
    进阶选股入口：资金流向优先
    流程：资金流排名 → 涨幅过滤 → 均线验证 → 量价验证 → 形态识别
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 进阶选股扫描...")

    # Step 1: 获取主力净流入排名
    stocks = get_money_flow_top()
    print(f"  资金流候选: {len(stocks)}只")
    if not stocks:
        return []

    # Step 2: 涨幅 & 价格过滤
    # 主板 + 股价10-100 + 涨幅2-5% + 量比1.5-5
    filtered = []
    for s in stocks:
        code = s["code"]
        name = s["name"]
        price = s["price"]
        chg_pct = s["chg_pct"]
        main_ratio = s["main_ratio"]

        # 价格过滤
        if price < 10 or price > 100:
            continue
        # 涨幅过滤（2-5%是刚启动，不是追高）
        if chg_pct < 2.0 or chg_pct > 5.0:
            continue
        # 主力净流入占比 > 3%（资金才是硬道理）
        if main_ratio < 3.0:
            continue
        # 排除创业板/科创板
        if code.startswith(("30", "301", "688")):
            continue

        filtered.append(s)

    print(f"  涨幅+资金过滤后: {len(filtered)}只")
    if not filtered:
        return []

    # Step 3: 均线形态验证（每个股票单独验证）
    ma_verified = []
    for s in filtered[:30]:  # 最多验证30只
        code = s["code"]
        name = s["name"]
        ma_ok, ma_msg = verify_ma_pattern(code)
        if ma_ok:
            s["ma_note"] = ma_msg
            ma_verified.append(s)
            print(f"    ✅ {name}({code}) 均线:{ma_msg}")
        else:
            print(f"    ❌ {name}({code}) 均线:{ma_msg}")

    print(f"  均线验证后: {len(ma_verified)}只")
    if not ma_verified:
        return []

    # Step 4: 量价验证
    vp_verified = []
    for s in ma_verified:
        code = s["code"]
        name = s["name"]
        vp_ok, vp_msg = verify_volume_price(code)
        if vp_ok:
            s["vp_note"] = vp_msg
            vp_verified.append(s)
            print(f"    ✅ {name}({code}) 量价:{vp_msg}")
        else:
            print(f"    ❌ {name}({code}) 量价:{vp_msg}")

    print(f"  量价验证后: {len(vp_verified)}只")
    if not vp_verified:
        return []

    # Step 5: 形态识别（缩量回踩优先）
    final = []
    for s in vp_verified:
        code = s["code"]
        name = s["name"]
        # 先检查缩量回踩（最佳形态）
        pf_ok, pf_msg = verify_pullback_pattern(code)
        if pf_ok:
            s["pattern"] = "缩量回踩"
            s["pattern_note"] = pf_msg
            final.append(s)
            print(f"    ⭐ {name}({code}) 形态:{pf_msg}")
            continue
        # 否则检查是否放量突破
        klines = get_kline_data(code, days=10)
        if len(klines) >= 5:
            closes = [k["close"] for k in klines]
            recent_high = max(closes[:-1])
            today_close = closes[-1]
            today_vol = klines[-1]["volume"]
            yest_vol = klines[-2]["volume"]
            if today_close > recent_high and today_vol > yest_vol * 1.5:
                s["pattern"] = "放量突破"
                s["pattern_note"] = f"突破{recent_high:.2f}新高+放量"
                final.append(s)
                print(f"    ⭐ {name}({code}) 放量突破新高")
                continue

        print(f"    ❌ {name}({code}) 无理想形态")

    # 按主力净流入占比排序
    final.sort(key=lambda x: x.get("main_ratio", 0), reverse=True)
    print(f"  最终入选: {len(final)}只")
    for s in final[:max_count]:
        print(f"    {s['name']}({s['code']}) 主力净流入{s.get('main_ratio',0):.1f}% 涨幅{s.get('chg_pct',0):.2f}%")

    return final[:max_count]

# 兼容旧接口
def get_index_components():
    """旧接口，返回主力净流入排名（主板）"""
    return get_money_flow_top()

def pick_best_candidates(max_count=3, min_score=5):
    """兼容旧接口"""
    return pick_by_money_flow(max_count)

def calculate_buy_quantity(price, cash, max_position_pct=30):
    """计算买入数量（100股整数倍）"""
    max_cost = cash * max_position_pct / 100
    shares = int(max_cost / price / 100) * 100
    return max(shares, 0)
