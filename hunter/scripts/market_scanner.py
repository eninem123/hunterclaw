#!/usr/bin/env python3
"""
猎手系统 - 市场扫描核心引擎 v2
数据源优先级:
  1. 腾讯行情 qt.gtimg.cn (指数/个股实时)
  2. 腾讯分时 ifzq.gtimg.cn (K线数据)
  3. 腾讯证券 sector API
  4. 东方财富数据中心 (fallback)
"""
import json
import sys
import os
import re
from datetime import datetime, date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
WARNINGS_FILE = DATA_DIR / "warnings.json"


# ─────────────────────────────────────────────
# HTTP 工具
# ─────────────────────────────────────────────
def http_get(url, headers=None, timeout=5, encoding="gbk"):
    import urllib.request
    h = {
        "Referer": "https://finance.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # 腾讯/新浪行情使用GBK编码
            return raw.decode(encoding, errors="replace")
    except Exception:
        return None


# ─────────────────────────────────────────────
# 1. 指数实时行情（腾讯）
# ─────────────────────────────────────────────
def get_index_snapshot():
    """
    腾讯行情接口，返回主要指数快照
    格式: date,open,close,high,low,volume
    """
    result = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "indices": []}
    codes_map = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000300": "沪深300",
        "sh000016": "上证50",
        "sz399905": "科创50",
    }
    codes = ",".join(codes_map.keys())
    url = f"https://qt.gtimg.cn/q={codes}"
    raw = http_get(url)
    if not raw:
        result["error"] = "无法连接腾讯行情"
        return result

    for line in raw.strip().split("\n"):
        m = re.match(r'v_\w+="(.+)"', line)
        if not m:
            continue
        parts = m.group(1).split("~")
        if len(parts) < 35:
            continue
        code_raw = parts[2]
        name = codes_map.get(code_raw, parts[1])
        try:
            price = float(parts[3])
            prev_close = float(parts[4])
            pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
            high = float(parts[33]) if parts[33] else None
            low = float(parts[34]) if parts[34] else None
            vol = float(parts[6]) if parts[6] else None
            update_time = parts[30] if len(parts) > 30 else None
        except (ValueError, IndexError):
            continue

        result["indices"].append({
            "name": name, "code": code_raw,
            "price": price, "prev_close": prev_close,
            "pct": pct, "high": high, "low": low,
            "volume": vol, "time": update_time,
        })

    return result


# ─────────────────────────────────────────────
# 2. 历史K线（腾讯，检测背离用）
# ─────────────────────────────────────────────
def get_kline(secid, count=10):
    """
    获取日K线，格式 [date, open, close, high, low, vol]
    secid: sh000001 或 sz399006 格式
    """
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={secid},day,,,{count},qfq"
    raw = http_get(url)
    if not raw:
        return []
    try:
        import json as _json
        data = _json.loads(raw)
        items = data.get("data", {}).get(secid, {}).get("day", [])
        result = []
        for item in items:
            try:
                result.append({
                    "date": item[0],
                    "open": float(item[1]),
                    "close": float(item[2]),
                    "high": float(item[3]),
                    "low": float(item[4]),
                    "volume": float(item[5]),
                })
            except (ValueError, IndexError):
                continue
        return result
    except Exception:
        return []


# ─────────────────────────────────────────────
# 3. 分时数据（尾盘异动用）
# ─────────────────────────────────────────────
def get_intraday(secid):
    """
    获取当日分时数据（分钟级）
    """
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?param={secid},m1,,320"
    raw = http_get(url)
    if not raw:
        return {}
    try:
        import json as _json
        data = _json.loads(raw)
        m1 = data.get("data", {}).get(secid, {}).get("m1", [])
        today = data.get("data", {}).get(secid, {}).get("qt", {})
        if m1 and len(m1) > 0:
            last = m1[-1]  # 最后一条分钟线
            return {
                "last_time": last[0] if len(last) > 0 else None,
                "last_price": float(last[1]) if len(last) > 1 else None,
                "count": len(m1),
            }
    except Exception:
        pass
    return {}


# ─────────────────────────────────────────────
# 4. 市场广度估算（基于指数）
# ─────────────────────────────────────────────
def estimate_breadth(indices):
    """
    根据指数涨跌估算市场广度
    依赖：多个指数的涨跌幅分布
    """
    if not indices:
        return {}
    up_count = sum(1 for i in indices if i.get("pct", 0) > 0)
    down_count = sum(1 for i in indices if i.get("pct", 0) < 0)
    avg_pct = sum(i.get("pct", 0) for i in indices) / len(indices) if indices else 0
    return {
        "up_indices": up_count,
        "down_indices": down_count,
        "avg_pct": round(avg_pct, 2),
        "note": "基于主要指数估算",
    }


# ─────────────────────────────────────────────
# 5. 背离检测（核心逻辑）
# ─────────────────────────────────────────────
def detect_divergence(index_data, klines):
    """
    背离检测 v2:
    数据基础受限，只用【价格 + 成交量 + 历史K线】
    替代无法获取的主力资金流

    背离类型:
    1. 价涨量缩: 价格创新高但成交量低于前期 → 主力未跟进
    2. 放量滞涨: 成交量明显放大但价格不涨 → 主力出货
    3. 连续缩量上涨: 缺乏资金支撑，上涨不可持续
    """
    warnings = []
    if not klines or len(klines) < 5:
        return warnings

    # 取最近5天
    recent = klines[-5:]
    avg_vol5 = sum(k["volume"] for k in recent) / len(recent)
    last = recent[-1]
    prev = recent[-2] if len(recent) > 1 else last

    # 类型1: 价涨但量缩（相比5日均量）
    last_pct = (last["close"] - prev["close"]) / prev["close"] * 100 if prev["close"] else 0
    vol_ratio = last["volume"] / avg_vol5 if avg_vol5 else 0
    if last["close"] > prev["close"] and vol_ratio < 0.7:
        warnings.append({
            "type": "DIVERGENCE_PRICE_UP_VOL_DOWN",
            "level": "🔴 高危",
            "signal": "价涨量缩 — 上涨缺乏资金支撑",
            "detail": f"今日价格{last['close']}(+{last_pct:.2f}%)，但成交量仅均量的{vol_ratio*100:.0f}%，主力未参与，上涨难持续",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    # 类型2: 连续3天缩量上涨
    if len(recent) >= 3:
        con_up = all(recent[i]["close"] > recent[i-1]["close"] for i in range(1, len(recent)))
        con_shrink = all(recent[i]["volume"] < recent[i-1]["volume"] for i in range(1, len(recent)))
        if con_up and con_shrink:
            days = len(recent)
            total_gain = (recent[-1]["close"] - recent[0]["open"]) / recent[0]["open"] * 100
            warnings.append({
                "type": "DIVERGENCE_CONSECUTIVE",
                "level": "🟡 注意",
                "signal": f"连续{days}天缩量上涨 — 警惕回调",
                "detail": f"累计涨幅{total_gain:.2f}%但成交量逐日萎缩，量价背离，注意获利了结",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    # 类型3: 昨收微涨但成交异常大（出货阳嫌疑）
    if len(recent) >= 2:
        yesterday = recent[-2]
        yesterday_pct = (yesterday["close"] - yesterday["open"]) / yesterday["open"] * 100 if yesterday.get("open") else 0
        if 0 < yesterday_pct < 0.5 and yesterday["volume"] > avg_vol5 * 1.5:
            warnings.append({
                "type": "SELLING_RALLY",
                "level": "🔴 高危",
                "signal": "昨收微涨放大量 — 主力出货特征",
                "detail": f"昨日({yesterday.get('date','?')})涨幅仅{yesterday_pct:.2f}%但成交量达均量的{yesterday['volume']/avg_vol5*100:.0f}%，疑似主力借机派发",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    return warnings


# ─────────────────────────────────────────────
# 6. 尾盘异动检测
# ─────────────────────────────────────────────
def detect_closing_anomaly(index_data, klines):
    """
    尾盘异动检测（14:30-14:55专属）
    逻辑:
    - 尾盘快速下跌(>0.5%) → 跳水
    - 尾盘快速上涨(>0.8%) → 拉升出货
    - 尾盘成交异常放大 → 异动信号
    """
    warnings = []
    now = datetime.now()
    is_closing = (now.hour == 14 and 30 <= now.minute < 55) or \
                 (now.hour == 15 and now.minute < 5)

    if not is_closing:
        return warnings

    # 用指数快照判断当前状态
    sz = next((i for i in index_data.get("indices", []) if "上证" in i.get("name", "")), None)
    if not sz:
        return warnings

    pct_chg = sz.get("pct", 0)

    if pct_chg < -0.5:
        warnings.append({
            "type": "CLOSING_DROP",
            "level": "🔴 危险",
            "signal": "尾盘指数快速下滑",
            "detail": f"上证指数跌幅{pct_chg:.2f}%，持仓股有跟跌风险，注意止损",
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        })
    elif pct_chg > 1.0:
        # 涨幅过大，检查是否量价背离
        last_vol = klines[-1]["volume"] if klines else 0
        avg_vol = sum(k["volume"] for k in klines[-5:]) / 5 if klines else 1
        if last_vol < avg_vol * 0.8:
            warnings.append({
                "type": "CLOSING_RALLY_WARNING",
                "level": "🟡 谨慎",
                "signal": "尾盘拉升但量能不足",
                "detail": f"上证指数涨幅{pct_chg:.2f}%，但成交量萎缩，谨防次日主力借机出货",
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            })
        else:
            warnings.append({
                "type": "CLOSING_RALLY_STRONG",
                "level": "🟢 偏强",
                "signal": "尾盘强势拉升",
                "detail": f"上证指数涨幅{pct_chg:.2f}%，成交量配合，明日有望延续",
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            })

    return warnings


# ─────────────────────────────────────────────
# 7. 完整扫描
# ─────────────────────────────────────────────
def full_scan(closing_mode=False):
    """
    完整市场扫描
    """
    report = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "section": "尾盘决策" if closing_mode else "盘中推演",
        "warnings": [],
        "signals": [],
        "index": {},
        "breadth": {},
        "klines": {},
        "verdict": "SCAN_COMPLETE",
    }

    # 指数快照
    try:
        index_data = get_index_snapshot()
        report["index"] = index_data
    except Exception as e:
        report["index"]["error"] = str(e)

    # 市场广度
    if index_data.get("indices"):
        report["breadth"] = estimate_breadth(index_data["indices"])

    # 获取K线（用于背离检测）
    klines_all = {}
    for secid, name in [("sh000001", "上证"), ("sz399006", "创业板")]:
        try:
            klines_all[secid] = get_kline(secid, count=10)
        except Exception:
            pass
    report["klines"] = {k: [l["date"] for l in v] for k, v in klines_all.items()}

    # 背离检测
    sz_klines = klines_all.get("sh000001", [])
    divergence_warnings = detect_divergence(report["index"], sz_klines)
    report["warnings"].extend(divergence_warnings)

    # 尾盘异动（仅窗口期）
    if closing_mode:
        anomaly_warnings = detect_closing_anomaly(report["index"], sz_klines)
        report["warnings"].extend(anomaly_warnings)

    # 风险裁决
    high_risk = any(w["level"] in ["🔴 高危", "🔴 危险"] for w in report["warnings"])
    med_risk = any(w["level"] == "🟡 注意" for w in report["warnings"])

    if high_risk:
        report["verdict"] = "RISK_HIGH"
    elif med_risk:
        report["verdict"] = "RISK_MEDIUM"
    else:
        report["verdict"] = "MARKET_NORMAL"

    return report


# ─────────────────────────────────────────────
# 8. 推送格式化（微信友好）
# ─────────────────────────────────────────────
def format_report(report):
    lines = []
    now = report["time"]
    section = report["section"]

    lines.append(f"📊 猎手系统 | {section} | {now}")

    # 指数
    indices = report.get("index", {}).get("indices", [])
    if indices:
        lines.append("\n【大盘指数】")
        for idx in indices:
            p = idx.get("pct", 0)
            emoji = "🔼" if p > 0 else "🔽" if p < 0 else "➖"
            lines.append(f"  {emoji} {idx.get('name', idx.get('code',''))}: "
                         f"{idx.get('price','?')} ({p:+.2f}%) 高{idx.get('high','?')} 低{idx.get('low','?')}")
    else:
        lines.append("\n【大盘指数】 数据获取失败")

    # 市场广度
    b = report.get("breadth", {})
    if b:
        lines.append(f"\n【市场广度】 上涨指: {b.get('up_indices',0)} 下跌指: {b.get('down_indices',0)} "
                     f"均幅: {b.get('avg_pct',0):+.2f}%")

    # K线摘要
    klines = report.get("klines", {})
    if klines.get("sh000001"):
        k5 = klines["sh000001"]
        lines.append(f"\n【近期走势】 上证: {k5[-5:] if len(k5)>=5 else k5}")

    # 预警
    warns = report.get("warnings", [])
    if warns:
        lines.append("\n【⚠️ 预警】")
        for w in warns:
            lines.append(f"  {w['level']} {w['signal']}")
            lines.append(f"    → {w['detail']}")

    # 最终裁决
    v = report["verdict"]
    verdict_map = {
        "RISK_HIGH": "🔴 市场风险偏高，谨慎操作",
        "RISK_MEDIUM": "🟡 市场中性，轻仓观察",
        "MARKET_NORMAL": "🟢 市场正常，可伺机而动",
        "SCAN_COMPLETE": "✅ 扫描完成",
    }
    v_text = verdict_map.get(v, v)
    lines.append(f"\n━━━━ {v_text} ━━━━")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    closing = "--closing" in sys.argv
    report = full_scan(closing_mode=closing)
    print(format_report(report))

    # 保存日志
    DATA_DIR.mkdir(exist_ok=True)
    log_file = DATA_DIR / "logs" / f"{date.today().isoformat()}.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    sys.exit(1 if report["verdict"] == "RISK_HIGH" else 0)
