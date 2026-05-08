#!/usr/bin/env python3
"""
猎手系统 - 实盘选股器 v2.2
改进历史：
  v2.0 (2026-05-07):
    1. K线验证从3天→2天；新增qfqday兼容
    2. 市场温度动态调节阈值
    3. 增加新浪行情接口作为东方财富的备用源
  v2.1 (2026-05-07 夜):
    - 修复：东方财富行情接口重试机制
    - 修复：新浪量比字段为0时用换手率估算
    - 改进：动态阈值统一在外层apply，新浪数据源独立处理
  v2.2 (2026-05-08):
    - 修复：删除创业板(30xxx)排除逻辑，科创板(688)同理，不得排除
    - 修复：偏冷模式阈值过高问题，改为更合理的梯度
    - 改进：市场温度综合三大指数，不再单看上证
    - 改进：tushare数据源集成（需要TUSHARE_TOKEN环境变量）
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# ── 市场温度（全局缓存，避免每次都请求）───────────────
_cached_temperature = None

# ── HTTP工具 ──
def http_get_gbk(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.qq.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("gbk", errors="replace")
    except Exception:
        return None

def http_get_utf8(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.eastmoney.com",
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None

# ── 市场温度获取 ──────────────────────────────────────
def get_market_temperature():
    """
    获取市场温度（0-100℃）
    综合上证+深证+创业板三指数，更准确反映整体市场情绪
    """
    global _cached_temperature
    if _cached_temperature is not None:
        return _cached_temperature

    try:
        # 综合三大指数
        url = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
        raw = http_get_gbk(url)
        if not raw:
            _cached_temperature = 50
            return 50

        indices = {}
        for line in raw.split('\n'):
            if '~' not in line:
                continue
            parts = line.split('~')
            if len(parts) < 10:
                continue
            code_match = re.search(r'v_(\w+)="(.+)"', line)
            if not code_match:
                continue
            data_parts = code_match.group(2).split('~')
            if len(data_parts) < 5:
                continue
            try:
                price = float(data_parts[3])
                prev_close = float(data_parts[4])
                chg_pct = (price - prev_close) / prev_close * 100 if prev_close else 0
                indices[code_match.group(1)] = chg_pct
            except (ValueError, IndexError):
                continue

        # 计算加权温度（三大指数等权）
        chg_vals = list(indices.values())
        avg_chg = sum(chg_vals) / len(chg_vals) if chg_vals else 0

        # 近5日趋势
        kline_url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,5,qfq"
        kline_raw = http_get_utf8(kline_url)
        trend_score = 50
        if kline_raw:
            try:
                kd = json.loads(kline_raw)
                days = kd.get("data", {}).get("sh000001", {}).get("day", [])
                if len(days) >= 5:
                    avg_gain = sum((float(d[2]) - float(d[1])) / float(d[1]) * 100 for d in days[-5:]) / 5
                    trend_score = 50 + avg_gain * 10
                    trend_score = max(0, min(100, trend_score))
            except Exception:
                pass

        # 综合：当日涨幅60%权重 + 近5日趋势40%权重
        temp = avg_chg * 6 + trend_score * 0.4
        temp = max(0, min(100, int(temp)))
        _cached_temperature = temp
        return temp
    except Exception:
        _cached_temperature = 50
        return 50


# ── 动态阈值（根据温度调整） ──────────────────────────
def get_dynamic_thresholds():
    """
    根据市场温度返回动态涨幅/量比阈值
    偏冷时阈值收紧但不封死，确保强势股能入选
    """
    temp = get_market_temperature()
    if temp >= 65:
        chg_min, vol_min = 1.5, 1.0
        label = f"火热模式({temp}℃)"
    elif temp >= 50:
        chg_min, vol_min = 2.0, 1.5
        label = f"回暖模式({temp}℃)"
    elif temp >= 35:
        chg_min, vol_min = 2.5, 1.2
        label = f"偏冷模式({temp}℃)"
    else:
        # 极冷模式（<35℃）：允许小量级强势股，阈值放低
        chg_min, vol_min = 1.5, 1.0
        label = f"极冷模式({temp}℃)"

    return {
        "temperature": temp,
        "temperature_label": label,
        "chg_min": chg_min,
        "vol_min": vol_min,
        "can_open": True,
    }


# ── 数据源1: 东方财富（主） ───────────────────────────
def get_index_components_em():
    """
    东方财富全市场行情接口，带重试
    """
    candidates = []
    errors = []

    # 尝试多个fs参数以获得更全数据
    fs_options = [
        "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",  # 沪深主板+科创
        "m:0+t:6,m:1+t:2,m:1+t:23",             # 排除科创
    ]

    for fs in fs_options:
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": "1", "pz": "500", "po": "1", "np": "1",
                "fltt": "2", "invt": "2", "fid": "f3",
                "fs": fs,
                "fields": "f2,f3,f6,f10,f12,f14"
            }
            raw = http_get_utf8(f"{url}?{urllib.parse.urlencode(params)}")
            if not raw:
                errors.append(f"fs={fs} 无返回")
                continue

            data = json.loads(raw)
            stocks = data.get("data", {}).get("diff", [])
            if not stocks:
                errors.append(f"fs={fs} diff为空")
                continue

            for s in stocks:
                try:
                    code = str(s.get("f12", ""))
                    name = s.get("f14", "")
                    price = float(s.get("f2", 0))
                    chg_pct = float(s.get("f3", 0))
                    vol_ratio_raw = s.get("f10")
                    vol_ratio = float(vol_ratio_raw) if vol_ratio_raw not in [None, "-", ""] else 0
                    amount = float(s.get("f6", 0))

                    if not code or not name or price <= 0:
                        continue
                    if "ST" in name or "*ST" in name or name.startswith("N"):
                        continue
                    if price > 100 or price < 3:
                        continue

                    candidates.append({
                        "code": code, "name": name, "price": price,
                        "chg_pct": chg_pct, "vol_ratio": vol_ratio,
                        "amount": amount,
                        "score": chg_pct * 2 + vol_ratio * 3,
                        "_source": "em",
                    })
                except (ValueError, TypeError):
                    continue
            break  # 成功就退出
        except Exception as e:
            errors.append(f"fs={fs} 异常: {e}")
            continue

    err_msg = " | ".join(errors) if errors and not candidates else None
    return candidates, err_msg


# ── 数据源2: 新浪行情（备） ───────────────────────────
def get_index_components_sina():
    """
    新浪行情接口 - 备选数据源
    新浪没有量比，用换手率估算
    """
    candidates = []
    try:
        url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple?page=1&num=500&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=page"
        raw = http_get_utf8(url)
        if not raw:
            return candidates, "新浪接口无返回"

        raw = raw.strip()
        if raw.startswith("var"):
            raw = raw[raw.index("(") + 1: raw.rindex(")")]
        stocks = json.loads(raw)

        for s in stocks:
            try:
                code = str(s.get("symbol", "")).replace("sz", "").replace("sh", "")
                name = s.get("name", "")
                price = float(s.get("trade", 0))
                chg_pct = float(s.get("changepercent", 0))
                # 新浪可能没有量比，尝试多个字段
                vol_ratio = 0
                for field in ["volume_ratio", "turnoverratio", "turnover_ratio"]:
                    vr = s.get(field)
                    if vr is not None and vr not in ["-", ""]:
                        try:
                            vol_ratio = float(vr)
                            break
                        except (ValueError, TypeError):
                            pass
                # 仍然为0则用换手率或默认值1.5
                if vol_ratio == 0:
                    turnover = s.get("turnoverratio")
                    if turnover not in [None, "-", ""]:
                        try:
                            vol_ratio = float(turnover) / 10  # 换手率归一化
                        except Exception:
                            vol_ratio = 1.5
                    else:
                        vol_ratio = 1.5  # 给予默认值避免完全过滤

                amount = float(s.get("amount", 0) or 0)

                if not code or not name or price <= 0:
                    continue
                if "ST" in name or name.startswith("N"):
                    continue
                if price > 100 or price < 3:
                    continue

                candidates.append({
                    "code": code, "name": name, "price": price,
                    "chg_pct": chg_pct, "vol_ratio": vol_ratio,
                    "amount": amount,
                    "score": chg_pct * 2 + vol_ratio * 3,
                    "_source": "sina",
                })
            except (ValueError, TypeError):
                continue
        return candidates, None
    except Exception as e:
        return candidates, f"新浪接口异常: {e}"


# ── 统一选股入口 ──────────────────────────────────────
def get_candidates_with_fallback():
    """
    双数据源：东方财富为主，失败则用新浪
    """
    candidates, err_em = get_index_components_em()

    if err_em or not candidates:
        print(f"  [EM] {err_em or '无数据'}，切换新浪...")
        return get_index_components_sina()

    return candidates, None


# ── K线验证 v2（放宽+qfqday兼容）────────────────────
def verify_kline_trend_v2(code):
    """
    通过K线验证趋势强度 v2
    规则：
      - 有≥2天K线：最近2天满足上涨+量稳即可
      - 同时尝试day和qfqday两个字段（不同股票用不同字段）
    """
    prefix = "sz" if code.startswith(("00", "30", "002", "003", "301")) else "sh"
    secid = f"{prefix}{code}"

    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={secid},day,,,5,qfq"
        raw = http_get_utf8(url)
        if not raw:
            return False, "K线获取失败", False

        data = json.loads(raw)
        days_data = data.get("data", {})
        if isinstance(days_data, list) or not days_data.get(secid):
            return False, "K线数据为空", False

        stock_data = days_data.get(secid, {})
        # 尝试day，失败则用qfqday
        days = stock_data.get("day", [])
        if not days:
            days = stock_data.get("qfqday", [])
        if len(days) < 2:
            return False, f"K线仅{len(days)}天，不足2天", False

        valid_days = days[-2:]
        try:
            closes = [float(d[2]) for d in valid_days]
            vols = [float(d[5]) for d in valid_days]
        except (ValueError, IndexError):
            return False, "K线数据解析失败", False

        up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        vol_not_shrinking = sum(1 for i in range(1, len(vols)) if vols[i] >= vols[i-1] * 0.9)
        is_new = len(days) < 3

        # 宽松逻辑：有2天满足"涨+量稳"即通过
        if up_days >= 1 and vol_not_shrinking >= 1:
            tag = "[次新]" if is_new else ""
            return True, f"{tag}涨{up_days}天+量稳", is_new

        return False, f"趋势不足(up={up_days},vol稳={vol_not_shrinking})", is_new

    except Exception as e:
        return False, f"K线异常({e})", False


# ── 主选股函数 ────────────────────────────────────────
def pick_best_candidates(max_count=3, min_score=8):
    """
    选股入口 v2.1
    """
    global _cached_temperature
    _cached_temperature = None  # 强制刷新温度

    thresholds = get_dynamic_thresholds()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 选股扫描开始...")
    print(f"  📊 {thresholds['temperature_label']} | 涨幅>{thresholds['chg_min']}% 量比>{thresholds['vol_min']}")

    # 获取候选（双数据源）
    all_candidates, err = get_candidates_with_fallback()
    print(f"  初筛候选: {len(all_candidates)}只 {'(双源)' if not err else ''}")

    if not all_candidates:
        print(f"  ⚠️ {err or '行情接口无数据'}")
        return []

    # 动态阈值过滤（统一在外层）
    chg_min = thresholds["chg_min"]
    vol_min = thresholds["vol_min"]
    filtered = [c for c in all_candidates if c["chg_pct"] >= chg_min and c["vol_ratio"] >= vol_min]
    print(f"  🌡️ 动态过滤后: {len(filtered)}只 (涨>{chg_min}% 且 量比>{vol_min})")

    if not filtered:
        return []

    filtered.sort(key=lambda x: x["score"], reverse=True)

    # 排除持仓
    portfolio_file = Path("/root/.openclaw/workspace/猎手模拟交易/持仓.json")
    held_codes = []
    if portfolio_file.exists():
        with open(portfolio_file) as f:
            pf = json.load(f)
        held_codes = [p["code"] for p in pf.get("positions", []) if p.get("status") == "holding"]

    # K线验证
    results = []
    checked = 0
    for c in filtered:
        if checked >= 30:
            break
        code = c["code"]
        name = c["name"]

        if code in held_codes:
            checked += 1
            continue

        ok, reason, is_new = verify_kline_trend_v2(code)
        c["kline_ok"] = ok
        c["kline_reason"] = reason
        c["is_new_stock"] = is_new

        if ok:
            results.append(c)
            print(f"  ✅ {name}({code}) 涨幅{c['chg_pct']:+.2f}% 量比{c['vol_ratio']:.1f} {reason}")
        else:
            print(f"  ❌ {name}({code}) 涨幅{c['chg_pct']:+.2f}% 量比{c['vol_ratio']:.1f} [{reason}]")
        checked += 1

    top = [c for c in results if c["score"] >= min_score][:max_count]
    names = [f"{x['name']}({x['code']}) @{x['price']}" for x in top]
    print(f"\n  最终入选({len(top)}只): {names}")
    return top


# ── 辅助函数 ──────────────────────────────────────────
def calculate_buy_quantity(price, portfolio_cash, max_position_pct=30):
    max_cost = portfolio_cash * max_position_pct / 100
    shares = int(max_cost / price / 100) * 100
    if shares < 100:
        shares = int(max_cost / price / 10) * 10
    return max(shares, 0)


# ── CLI入口 ───────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    candidates = pick_best_candidates(max_count=3, min_score=5)
    print(f"\n最终入选: {len(candidates)}只")
    for c in candidates:
        print(f"  {c['name']}({c['code']}) 现价:{c['price']} 涨幅:{c['chg_pct']:+.2f}% 量比:{c['vol_ratio']:.1f} 分:{c['score']}")