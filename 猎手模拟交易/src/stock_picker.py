#!/usr/bin/env python3
"""
猎手系统 - 实盘选股器 v1.0
从全市场筛选符合买入条件的股票
筛选条件：
  1. 主板股票（60/00/688开头），排除创业板
  2. 股价 10-100元（避免高价股和低价仙股）
  3. 今日涨幅 > 2%（强势股）
  4. 量比 > 1.5（资金活跃）
  5. 当前不在持仓中
  6. 过滤ST/N股
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

def get_index_components():
    """
    获取涨幅前列的A股（主板为主）
    东方财富全市场行情接口
    """
    candidates = []

    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "300",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f2,f3,f6,f10,f12,f14"
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
                vol_ratio_raw = s.get("f10")
                vol_ratio = float(vol_ratio_raw) if vol_ratio_raw not in [None, "-", ""] else 0
                amount = float(s.get("f6", 0))

                # 基础过滤
                if not code or not name or price <= 0:
                    continue
                if "ST" in name or "*ST" in name or name.startswith("N"):
                    continue
                if price > 100 or price < 3:
                    continue

                # 排除创业板 (300/301开头)
                if code.startswith(("30", "301")):
                    continue

                # 涨幅 > 2% + 量比 > 1.5
                if chg_pct < 2.0:
                    continue
                if vol_ratio < 1.5:
                    continue

                candidates.append({
                    "code": code,
                    "name": name,
                    "price": price,
                    "chg_pct": chg_pct,
                    "vol_ratio": vol_ratio,
                    "amount": amount,
                    "score": chg_pct * 2 + vol_ratio * 3
                })
            except (ValueError, TypeError):
                continue

    except Exception as e:
        print(f"[选股接口异常] {e}")

    return candidates

def verify_kline_trend(code):
    """
    通过K线验证趋势强度
    要求：最近3天收盘价连续上涨 + 成交量逐日放大
    """
    # 添加交易所前缀
    prefix = "sz" if code.startswith(("00", "30", "002", "003", "002", "301")) else "sh"
    secid = f"{prefix}{code}"
    
    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={secid},day,,,5,qfq"
        raw = http_get_utf8(url)
        if not raw:
            return False, "K线获取失败"

        data = json.loads(raw)
        days_data = data.get("data", {})
        if isinstance(days_data, list) or not days_data.get(secid):
            return False, "K线数据为空"
        
        days = days_data.get(secid, {}).get("day", [])
        if len(days) < 3:
            return False, "K线不足3天"

        try:
            closes = [float(d[2]) for d in days[-3:]]
            vols = [float(d[5]) for d in days[-3:]]
        except (ValueError, IndexError):
            return False, "K线数据解析失败"

        # 连续上涨天数
        up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        # 成交量放大天数
        vol_up = sum(1 for i in range(1, len(vols)) if vols[i] > vols[i-1])

        if up_days >= 2 and vol_up >= 1:
            return True, f"连涨{up_days}天+量增"

        return False, f"趋势不足(up={up_days},vol={vol_up})"
    except Exception as e:
        return False, f"K线异常({e})"

def pick_best_candidates(max_count=3, min_score=8):
    """
    选股入口：返回最优候选股票列表
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 选股扫描开始...")

    candidates = get_index_components()
    print(f"  初筛候选: {len(candidates)}只")

    if not candidates:
        print("  ⚠️ 行情接口无数据")
        return []

    # 按评分排序
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 读取持仓，排除已在仓的
    portfolio_file = Path("/root/.openclaw/workspace/猎手模拟交易/持仓.json")
    held_codes = []
    if portfolio_file.exists():
        with open(portfolio_file) as f:
            pf = json.load(f)
        held_codes = [p["code"] for p in pf.get("positions", []) if p.get("status") == "holding"]

    # K线验证
    results = []
    checked = 0
    for c in candidates:
        if checked >= 30:
            break

        code = c["code"]
        name = c["name"]

        if code in held_codes:
            print(f"  🚫 {name}({code}) 已在持仓中，跳过")
            checked += 1
            continue

        ok, reason = verify_kline_trend(code)
        c["kline_ok"] = ok
        c["kline_reason"] = reason

        if ok:
            results.append(c)
            print(f"  ✅ {name}({code}) 涨幅{c['chg_pct']:+.2f}% 量比{c['vol_ratio']:.1f} [{reason}]")
        else:
            print(f"  ❌ {name}({code}) 涨幅{c['chg_pct']:+.2f}% 量比{c['vol_ratio']:.1f} [{reason}]")

        checked += 1

    # 按评分取top N，且评分>=min_score
    top = [c for c in results if c["score"] >= min_score][:max_count]

    names = [f"{x['name']}({x['code']}) @{x['price']}" for x in top]
    print(f"\n  最终入选({len(top)}只): {names}")
    return top

def calculate_buy_quantity(price, portfolio_cash, max_position_pct=30):
    """
    根据资金上限计算买入股数（100股为单位）
    """
    max_cost = portfolio_cash * max_position_pct / 100
    shares = int(max_cost / price / 100) * 100
    if shares < 100:
        shares = int(max_cost / price / 10) * 10
    return max(shares, 0)

if __name__ == "__main__":
    print("=" * 50)
    candidates = pick_best_candidates(max_count=3, min_score=5)
    print(f"\n最终入选: {len(candidates)}只")
    for c in candidates:
        print(f"  {c['name']}({c['code']}) 现价:{c['price']} 涨幅:{c['chg_pct']:+.2f}% 量比:{c['vol_ratio']:.1f} 分:{c['score']}")
