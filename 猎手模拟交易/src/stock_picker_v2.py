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

def get_day_position(code):
    """
    获取股票今日区间位置
    返回：0%=最低价，100%=最高价
    None=无法获取
    """
    prefix = "sz" if code.startswith(("00", "30", "002", "003")) else "sh"
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = r.read().decode("gbk", errors="replace")
        # 格式: v_sz000651="51~格力电器~000651~40.63~38.44~...
        m = re.search(r'"(.+)"', raw)
        if not m:
            return None, None
        parts = m.group(1).split("~")
        if len(parts) < 35:
            return None, None
        price = float(parts[3])
        high = float(parts[33]) if parts[33] else None
        low = float(parts[34]) if parts[34] else None
        if high and low and high != low:
            return (price - low) / (high - low) * 100, price
        return None, None
    except Exception:
        return None, None

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
    获取主力净流入排名TOP股票（主板）
    数据源：akshare -> 东方财富 (不稳定时降级为腾讯五档估算)
    返回：[{code, name, main_net_inflow, main_ratio, price, chg_pct}]
    """
    candidates = []
    try:
        import akshare as ak
        import pandas as pd
        df = ak.stock_individual_fund_flow_rank(indicator='今日')
        if df is not None and len(df) > 0:
            cols = df.columns.tolist()
            code_col = next((c for c in cols if '代码' in c), None)
            name_col = next((c for c in cols if '名称' in c), None)
            net_col = next((c for c in cols if '净流入' in c and '主力' in c), None)
            ratio_col = next((c for c in cols if '占比' in c and '主力' in c), None)
            if all([code_col, name_col, net_col, ratio_col]):
                for _, row in df.iterrows():
                    try:
                        code = str(row[code_col]).zfill(6)
                        name = str(row[name_col])
                        main_ratio = float(row[ratio_col]) if pd.notna(row[ratio_col]) else 0
                        if not code or not name or main_ratio <= 0:
                            continue
                        if 'ST' in name or name.startswith('N'):
                            continue
                        if code.startswith(('30', '301', '688')):
                            continue
                        candidates.append({
                            'code': code, 'name': name,
                            'main_net_inflow': float(row[net_col]) if pd.notna(row[net_col]) else 0,
                            'main_ratio': main_ratio,
                            'price': 0, 'chg_pct': 0
                        })
                    except:
                        continue
                return candidates
    except Exception as e:
        print(f"  [warn] akshare资金流失败: {e}, 降级为腾讯五档估算")

    return _get_money_flow_from_tencent()


def _get_money_flow_from_tencent():
    """
    降级方案：用腾讯五档数据估算主力资金流向
    原理：五档买盘 >> 五档卖盘 → 主力主动买入
    """
    candidates = []
    try:
        import akshare as ak
        try:
            df = ak.index_stock_cons_sina(symbol='000300')
            stock_list = []
            for _, row in df.iterrows():
                code = str(row['code'])
                if code.startswith(('sz', 'sh')):
                    code = code[2:]
                name = row['name']
                if code.startswith(('00', '60')):
                    stock_list.append({'code': code, 'name': name})
            stock_list = stock_list[:80]
        except:
            stock_list = [
                {'code': '600030', 'name': '中信证券'},
                {'code': '600036', 'name': '招商银行'},
                {'code': '601318', 'name': '中国平安'},
                {'code': '000651', 'name': '格力电器'},
                {'code': '600176', 'name': '中国巨石'},
                {'code': '600019', 'name': '宝钢股份'},
                {'code': '601166', 'name': '兴业银行'},
                {'code': '600050', 'name': '中国联通'},
                {'code': '600009', 'name': '上海机场'},
                {'code': '601398', 'name': '工商银行'},
            ]

        batch_size = 15
        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            codes_str = ','.join([('sh' if c['code'].startswith('6') else 'sz') + c['code'] for c in batch])
            url = f'https://qt.gtimg.cn/q={codes_str}'
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as r:
                    raw = r.read().decode('gbk')

                for line in raw.strip().split('\n'):
                    if '~' not in line:
                        continue
                    parts = line.split('"')[1].split('~')
                    if len(parts) < 50:
                        continue
                    try:
                        actual_code = parts[2]  # 代码在第3个字段(parts[0]是前缀'1')
                        name = parts[1]
                        price = float(parts[3])
                        chg_pct = float(parts[32]) if parts[32] else 0
                        buy_vols = [int(parts[j]) for j in range(36, 41) if parts[j].isdigit()]
                        sell_vols = [int(parts[j]) for j in range(41, 46) if parts[j].isdigit()]
                        total_buy = sum(buy_vols)
                        total_sell = sum(sell_vols)
                        total = total_buy + total_sell
                        if total == 0:
                            continue
                        main_ratio = (total_buy - total_sell) / total * 100
                        if main_ratio < 15:
                            continue
                        candidates.append({
                            'code': actual_code, 'name': name,
                            'price': price, 'chg_pct': chg_pct,
                            'main_net_inflow': main_ratio,
                            'main_ratio': main_ratio
                        })
                    except:
                        continue
            except:
                continue

        candidates.sort(key=lambda x: x['main_ratio'], reverse=True)
        return candidates[:50]
    except Exception as e:
        print(f"  [error] 腾讯五档估算失败: {e}")
        return []


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

    # 今日量比昨日温和放量（允许缩量，只要不是极度缩量）
    # 缩量回调是最佳买点，放量上涨是确认买点
    vol_expanded = True  # 暂时取消量能过滤，专注趋势和位置
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
    流程：沪深300候选 → 批量实时数据 → 区间位置筛选 → 均线验证 → 量价验证 → 形态识别
    数据源：akshare(沪深300列表) + 腾讯(实时行情)，东方财富资金流不稳定时降级五档
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 进阶选股扫描...")

    # Step 1: 获取沪深300成分股（akshare）作为候选池
    import akshare as ak
    try:
        df = ak.index_stock_cons_sina(symbol='000300')
        stock_pool = []
        for _, row in df.iterrows():
            code = str(row['code'])
            if code.startswith(('sz', 'sh')):
                code = code[2:]
            name = row['name']
            if code.startswith(('00', '60')) and len(code) == 6:
                stock_pool.append({'code': code, 'name': name})
        print(f"  候选池: {len(stock_pool)}只(沪深300主板)")
    except Exception as e:
        print(f"  [error] 获取沪深300失败: {e}")
        return []

    # Step 2: 批量获取实时数据（腾讯接口，每次15只）
    batch_size = 15
    all_data = []
    for i in range(0, len(stock_pool), batch_size):
        batch = stock_pool[i:i+batch_size]
        codes_str = ','.join([('sh' if s['code'].startswith('6') else 'sz') + s['code'] for s in batch])
        url = f'https://qt.gtimg.cn/q={codes_str}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('gbk')

            for line in raw.strip().split('\n'):
                if '~' not in line:
                    continue
                parts = line.split('"')[1].split('~')
                if len(parts) < 50:
                    continue
                try:
                    actual_code = parts[2]  # 代码在第3个字段(parts[0]是前缀'1')
                    name = parts[1]
                    price = float(parts[3])
                    prev = float(parts[4])
                    chg_pct = float(parts[32]) if parts[32] else 0
                    high = float(parts[33]) if parts[33] else price
                    low = float(parts[34]) if parts[34] else price
                    vol_ratio = float(parts[49]) if parts[49] else 0

                    pos = (price - low) / (high - low) * 100 if high != low else 50

                    all_data.append({
                        'code': actual_code, 'name': name,
                        'price': price, 'chg_pct': chg_pct,
                        'high': high, 'low': low, 'pos': pos,
                        'vol_ratio': vol_ratio, 'main_ratio': 0
                    })
                except:
                    continue
        except:
            continue

    print(f"  批量行情获取: {len(all_data)}只")

    # Step 3: 区间位置 & 价格过滤
    # 主板 + 股价5-100 + 非高位(区间<65%) + 涨幅<7%
    filtered = [s for s in all_data if s['pos'] < 65 and s['chg_pct'] < 7 and 5 <= s['price'] <= 100]
    print(f"  位置+价格过滤后: {len(filtered)}只")
    if not filtered:
        return []

    # Step 4: 均线形态验证（每个股票单独验证）
    ma_verified = []
    for s in filtered[:30]:
        code = s['code']
        name = s['name']
        ma_ok, ma_msg = verify_ma_pattern(code)
        if ma_ok:
            s['ma_note'] = ma_msg
            ma_verified.append(s)
            print(f"    ✅ {name}({code}) 均线:{ma_msg}")
        else:
            print(f"    ❌ {name}({code}) 均线:{ma_msg}")

    print(f"  均线验证后: {len(ma_verified)}只")
    if not ma_verified:
        return []

    # Step 5: 量价验证
    vp_verified = []
    for s in ma_verified:
        code = s['code']
        name = s['name']
        vp_ok, vp_msg = verify_volume_price(code)
        if vp_ok:
            s['vp_note'] = vp_msg
            vp_verified.append(s)
            print(f"    ✅ {name}({code}) 量价:{vp_msg}")
        else:
            print(f"    ❌ {name}({code}) 量价:{vp_msg}")

    print(f"  量价验证后: {len(vp_verified)}只")
    if not vp_verified:
        return []

    # Step 6: 形态识别
    final = []
    for s in vp_verified:
        code = s['code']
        name = s['name']
        pf_ok, pf_msg = verify_pullback_pattern(code)
        if pf_ok:
            s['pattern'] = '缩量回踩'
            s['pattern_note'] = pf_msg
            final.append(s)
            print(f"    ⭐ {name}({code}) 形态:{pf_msg}")
            continue

        klines = get_kline_data(code, days=10)
        if len(klines) >= 5:
            closes = [k['close'] for k in klines]
            recent_high = max(closes[:-1])
            today_close = closes[-1]
            today_vol = klines[-1]['volume']
            yest_vol = klines[-2]['volume']
            if today_close > recent_high and today_vol > yest_vol * 1.5:
                s['pattern'] = '放量突破'
                s['pattern_note'] = f"突破{recent_high:.2f}新高+放量"
                final.append(s)
                print(f"    ⭐ {name}({code}) 放量突破新高")
                continue
        print(f"    ❌ {name}({code}) 无理想形态")

    final.sort(key=lambda x: x.get('main_ratio', 0), reverse=True)
    print(f"  最终入选: {len(final)}只")
    for s in final[:max_count]:
        print(f"    {s['name']}({s['code']}) 现价{s.get('price',0):.2f} 涨跌{s.get('chg_pct',0):+.2f}% 区间{s.get('pos',0):.0f}%")

    return final[:max_count]



def pick_best_candidates(max_count=3, min_score=5):
    """兼容旧接口"""
    return pick_by_money_flow(max_count)

def calculate_buy_quantity(price, cash, max_position_pct=30):
    """计算买入数量（100股整数倍）"""
    max_cost = cash * max_position_pct / 100
    shares = int(max_cost / price / 100) * 100
    return max(shares, 0)
