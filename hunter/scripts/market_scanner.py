#!/usr/bin/env python3
"""
猎手系统 - 市场扫描核心引擎 v2 (规则 v4.2.2)
更新: R23-E/R25/R26/V12 新增 | R22/R23/FM-032 保留
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

    # 市场温度计算 (v4.0: 含恐慌指数)
    sz_full_klines = klines_all.get("sh000001", [])
    market_temp = calculate_market_temperature(report["index"], report["breadth"], sz_full_klines)
    report["market_temperature"] = market_temp
    
    # 恐慌指数 (v4.0新增)
    panic_data = calculate_panic_index(report["index"], report["breadth"], sz_full_klines)
    report["panic_index"] = panic_data

    # 背离检测
    sz_klines = klines_all.get("sh000001", [])
    divergence_warnings = detect_divergence(report["index"], sz_klines)
    report["warnings"].extend(divergence_warnings)
    
    # V09: 恐慌反弹检测
    v09_warnings = check_v09_panic_rebound(panic_data["panic_index"], report["index"], sz_full_klines)
    report["warnings"].extend(v09_warnings)

    # R18 + V10: 冰点/恐慌冻结（v4.0增强版）
    r18_warnings = check_r18_freeze(market_temp["temperature"], panic_data["panic_index"])
    report["warnings"].extend(r18_warnings)
    
    # V10: 恐慌环境禁止
    v10_warnings = check_v10_panic_ban(panic_data["panic_index"])
    report["warnings"].extend(v10_warnings)

    # R19: ATR动态止损（基于市场温度）
    r19_warnings = check_r19_atr_stop(market_temp["temperature"], sz_full_klines)
    report["warnings"].extend(r19_warnings)

    # R20: 板块共振验证
    r20_warnings = check_r20_sector_resonance()
    report["warnings"].extend(r20_warnings)

    # R21: 个股相对强度
    r21_warnings = check_r21_relative_strength(market_temp["temperature"], report["index"])
    report["warnings"].extend(r21_warnings)

    # R22: 回暖逃生预案 (v4.2新增)
    r22_warnings = check_r22_recovery_plan(panic_data["panic_index"], market_temp["temperature"], sz_full_klines)
    report["warnings"].extend(r22_warnings)
    
    # R23: 假回暖识别 (v4.2新增)
    r23_warnings = check_r23_false_recovery(panic_data["panic_index"], report["index"], sz_full_klines, report["breadth"])
    report["warnings"].extend(r23_warnings)
    
    # R23-E: 结构性分化识别 (v4.2.2新增 - 科创涨+主板跌=假回暖)
    r23e_warnings = check_r23e_structural_divergence(report["index"], report["breadth"])
    report["warnings"].extend(r23e_warnings)
    
    # R25: LPR/政策催化应对 (v4.2.2新增)
    r25_warnings = check_r25_lpr_catalyst(report["index"], market_temp["temperature"])
    report["warnings"].extend(r25_warnings)
    
    # R26: 英伟达财报→A股联动规则 (v4.2.2新增)
    r26_warnings = check_r26_earnings_linkage()
    report["warnings"].extend(r26_warnings)
    
    # V12: 连续冰点>10天升级应对 (v4.2.2新增)
    v12_warnings = check_v12_extended_freeze(market_temp["temperature"], panic_data["panic_index"], sz_full_klines)
    report["warnings"].extend(v12_warnings)
    
    # FM-032: 地量见底信号 (半激活, v4.2升级)
    fm032_warnings = check_fm032_bottom_signal(panic_data["panic_index"], sz_full_klines)
    report["warnings"].extend(fm032_warnings)

    # 尾盘异动（仅窗口期）
    if closing_mode:
        anomaly_warnings = detect_closing_anomaly(report["index"], sz_klines)
        report["warnings"].extend(anomaly_warnings)

    # 风险裁决
    high_risk = any(w["level"] in ["🔴 高危", "🔴 危险", "🔴 冻结"] for w in report["warnings"])
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

    # 市场温度 + 恐慌指数
    temp = report.get("market_temperature", {})
    if temp:
        t_val = temp.get("temperature", "?")
        t_label = temp.get("label", "")
        panic_val = temp.get("panic_index", report.get("panic_index", {}).get("panic_index", "?"))
        panic_label = temp.get("panic_label", report.get("panic_index", {}).get("label", ""))
        emoji_temp = "🔥" if t_val >= 70 else "🌡️" if t_val >= 35 else "🥶"
        emoji_panic = "😱" if panic_val < 25 else "😰" if panic_val < 40 else "😌" if panic_val > 60 else "🤔"
        lines.append(f"\n【市场温度】 {emoji_temp} {t_val}℃ {t_label}")
        lines.append(f"【恐慌指数】 {emoji_panic} {panic_val} {panic_label}")

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
# 9. 市场温度计算 & 新规则 (R18-R21)
# ─────────────────────────────────────────────
def calculate_market_temperature(index_data: dict, breadth: dict, klines: list) -> dict:
    """
    计算市场温度 (0-100)
    基于: 指数涨跌幅, 市场广度, 历史对比
    返回: {temperature, label, level}
    """
    score = 50  # 默认中性

    indices = index_data.get("indices", [])
    if indices:
        sz = next((i for i in indices if "上证" in i.get("name", "")), None)
        cy = next((i for i in indices if "创业板" in i.get("name", "")), None)
        hs300 = next((i for i in indices if "沪深300" in i.get("name", "")), None)

        # 指数因子 (权重 40%)
        index_score = 50
        if sz:
            index_score += sz.get("pct", 0) * 3
        if cy:
            index_score += cy.get("pct", 0) * 2
        if hs300:
            index_score += hs300.get("pct", 0) * 2
        index_score = max(0, min(100, index_score))
        score = score * 0.6 + index_score * 0.4

    # 广度因子 (权重 30%)
    if breadth:
        up = breadth.get("up_indices", 0)
        down = breadth.get("down_indices", 0)
        total = up + down
        if total > 0:
            breadth_ratio = up / total
            breadth_score = breadth_ratio * 100
            score = score * 0.7 + breadth_score * 0.3

    # 历史对比因子 (权重 30%) - 基于K线趋势
    if klines and len(klines) >= 5:
        recent = klines[-5:]
        last = recent[-1]
        first = recent[0]
        pct_change = (last["close"] - first["close"]) / first["close"] * 100 if first["close"] else 0

        # 趋势得分: 5日涨跌幅映射
        trend_score = 50 + pct_change * 2
        trend_score = max(0, min(100, trend_score))

        # 量能稳定性: 连续缩量降低得分
        vol_trend = 50
        if len(recent) >= 3:
            vol_increasing = all(recent[i]["volume"] >= recent[i-1]["volume"] * 0.9 for i in range(1, len(recent)))
            vol_decreasing = all(recent[i]["volume"] < recent[i-1]["volume"] for i in range(1, len(recent)))
            if vol_decreasing:
                vol_trend = 30
            elif vol_increasing:
                vol_trend = 70

        history_score = trend_score * 0.6 + vol_trend * 0.4
        score = score * 0.7 + history_score * 0.3

    score = round(max(0, min(100, score)))

    # 温度标签
    if score >= 70:
        label = "过热"
        level = "HIGH"
    elif score >= 50:
        label = "正常"
        level = "NORMAL"
    elif score >= 30:
        label = "偏冷"
        level = "COOL"
    else:
        label = "冰点"
        level = "FREEZE"

    return {"temperature": score, "label": label, "level": level}


def calculate_panic_index(index_data: dict, breadth: dict, klines: list) -> dict:
    """
    计算恐慌指数 (0-100, 越低越恐慌)
    因子:
      1. 指数跌幅贡献 (30%)
      2. 涨跌比贡献 (30%)
      3. 量能萎缩贡献 (20%)
      4. 连续缩量下跌贡献 (20%)
    """
    score = 60
    indices = index_data.get("indices", [])
    if indices:
        avg_chg = sum(i.get("pct", 0) for i in indices) / max(len(indices), 1)
        if avg_chg < -3:
            score -= 25
        elif avg_chg < -2:
            score -= 18
        elif avg_chg < -1:
            score -= 10
        elif avg_chg < -0.5:
            score -= 5
        elif avg_chg > 1:
            score += 10
        elif avg_chg > 0.5:
            score += 5
    up = breadth.get("up_indices", 0)
    down = breadth.get("down_indices", 0)
    total = up + down
    if total > 0:
        ratio = up / total
        if ratio < 0.2:
            score -= 20
        elif ratio < 0.3:
            score -= 12
        elif ratio < 0.4:
            score -= 5
        elif ratio > 0.7:
            score += 10
        elif ratio > 0.6:
            score += 5
    if klines and len(klines) >= 3:
        recent = klines[-3:]
        vol_shrinking = all(recent[i]["volume"] < recent[i-1]["volume"] for i in range(1, len(recent)))
        price_dropping = all(recent[i]["close"] < recent[i-1]["close"] for i in range(1, len(recent)))
        if vol_shrinking and price_dropping:
            score -= 15
        last_vol = klines[-1].get("volume", 0)
        avg_vol = sum(k["volume"] for k in klines[-5:]) / 5 if len(klines) >= 5 else last_vol
        if avg_vol > 0 and last_vol < avg_vol * 0.5:
            score -= 8
    score = max(0, min(100, score))
    if score >= 60:
        label, level = "安全", "SAFE"
    elif score >= 40:
        label, level = "谨慎", "CAUTION"
    elif score >= 25:
        label, level = "偏冷", "COLD"
    elif score >= 10:
        label, level = "冰点", "FREEZE"
    else:
        label, level = "恐慌", "PANIC"
    return {"panic_index": score, "label": label, "level": level}


def check_v10_panic_ban(panic_index: int) -> list:
    """V10: 恐慌环境全面禁止"""
    warnings = []
    if panic_index < 10:
        warnings.append({
            "type": "V10_PANIC_BAN",
            "level": "\U0001f534 冻结",
            "signal": "恐慌环境 — 全面禁止交易",
            "detail": f"恐慌指数{panic_index} < 10，触发V10规则：全面禁止所有开仓操作，强制空仓",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "V10"
        })
    elif panic_index < 25:
        warnings.append({
            "type": "V10_PANIC_WARN",
            "level": "\U0001f534 高危",
            "signal": "恐慌指数偏低 — 禁止新开仓",
            "detail": f"恐慌指数{panic_index} < 25，触发V10规则：禁止新买入，只可减仓或空仓观望",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "V10"
        })
    return warnings


def check_v09_panic_rebound(panic_index: int, index_data: dict, klines: list) -> list:
    """V09: 冰点期高开诱多识别 — 恐慌反弹先减半"""
    warnings = []
    if panic_index >= 40:
        return warnings
    indices = index_data.get("indices", [])
    sz = next((i for i in indices if "上证" in i.get("name", "")), None)
    if not sz or not klines or len(klines) < 2:
        return warnings
    today_pct = sz.get("pct", 0)
    yesterday = klines[-2]
    yesterday_pct = (yesterday["close"] - yesterday["open"]) / yesterday["open"] * 100 if yesterday["open"] else 0
    if yesterday_pct < -1 and today_pct > 1:
        warnings.append({
            "type": "V09_PANIC_REBOUND",
            "level": "\U0001f7e1 注意",
            "signal": "恐慌反弹信号 — 建议减半仓",
            "detail": f"恐慌指数{panic_index}环境下，昨日跌{yesterday_pct:.1f}%今日涨{today_pct:.1f}%，典型的恐慌反弹特征(V09)。建议持仓减半，防止二次探底。",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "V09"
        })
    return warnings


def check_r18_freeze(temperature: int, panic_index: int = 60) -> list:
    """R18+V10 增强版冰点冻结 (v4.0)"""
    warnings = []
    if temperature < 25:
        warnings.append({
            "type": "R18_FREEZE_V10",
            "level": "\U0001f534 冻结",
            "signal": "市场冰封 — 强制空仓",
            "detail": f"温度{temperature}℃<25℃+恐慌{panic_index}，R18+V10双重锁定：强制空仓",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R18/V10"
        })
    elif temperature < 35:
        warnings.append({
            "type": "R18_FREEZE",
            "level": "\U0001f534 冻结",
            "signal": "市场冰点 — 禁止开新仓",
            "detail": f"市场温度{temperature}℃<35℃，触发R18规则：不买入任何新股票，仅可持有或减仓",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R18"
        })
    return warnings


def check_r19_atr_stop(temperature: int, klines: list) -> list:
    """R19: ATR动态止损（基于市场温度调整止损幅度）"""
    warnings = []
    if not klines or len(klines) < 14:
        return warnings

    # 计算 ATR(14)
    tr_list = []
    for i in range(1, min(15, len(klines))):
        high = klines[i].get("high", 0)
        low = klines[i].get("low", 0)
        prev_close = klines[i-1].get("close", 0)
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
    atr = sum(tr_list) / len(tr_list) if tr_list else 0

    # 温度自适应止损乘数
    if temperature < 35:
        atr_mult = 1.5
    elif temperature < 50:
        atr_mult = 2.0
    elif temperature < 70:
        atr_mult = 2.5
    else:
        atr_mult = 3.0

    last_close = klines[-1].get("close", 0)
    dynamic_stop = last_close - atr * atr_mult

    warnings.append({
        "type": "R19_ATR_STOP",
        "level": "\U0001f7e1 注意" if temperature < 35 else "\u2139\ufe0f 参考",
        "signal": "ATR动态止损",
        "detail": f"ATR(14)={atr:.2f}, 温度{temperature}℃, 乘数{atr_mult}, 动态止损={dynamic_stop:.2f} (基于{last_close})",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "R19",
        "atr": round(atr, 2),
        "dynamic_stop": round(dynamic_stop, 2),
    })
    return warnings


def check_r20_sector_resonance() -> list:
    """R20: 板块共振验证（需选股系统配合，此处预留接口）"""
    warnings = []
    warnings.append({
        "type": "R20_SECTOR_RESONANCE",
        "level": "\u2139\ufe0f 提示",
        "signal": "板块共振验证（需选股系统配合）",
        "detail": "R20规则要求同板块\u22652只个股出现同步信号时确认信号有效性，当前扫描无个股数据，需配合选股引擎使用",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "R20"
    })
    return warnings


def check_r21_relative_strength(temperature: int, index_data: dict) -> list:
    """R21: 个股相对强度（与沪深300比较）"""
    warnings = []
    if temperature >= 30:
        return warnings

    indices = index_data.get("indices", [])
    hs300 = next((i for i in indices if "沪深300" in i.get("name", "")), None)
    if not hs300:
        return warnings

    hs300_pct = hs300.get("pct", 0)
    threshold = hs300_pct - 1.0

    warnings.append({
        "type": "R21_RELATIVE_STRENGTH",
        "level": "\U0001f7e1 注意",
        "signal": "个股相对强度要求",
        "detail": f"沪深300今日{hs300_pct:+.2f}%, 要求选股日涨幅\u2265{threshold:+.2f}%（沪深300的-1%）",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "R21",
        "hs300_pct": hs300_pct,
        "min_required_pct": round(threshold, 2),
    })
    return warnings


def check_r22_recovery_plan(panic_index: int, temperature: int, klines: list) -> list:
    """R22: 回暖逃生预案
    当恐慌指数从<25回升至>25时的入场/仓位/止损全流程检查
    """
    warnings = []
    if panic_index >= 25 or temperature >= 35:
        return warnings  # 只有在恐慌冰点时显示预案
    
    warnings.append({
        "type": "R22_RECOVERY_PLAN",
        "level": "\u2139\ufe0f 预案",
        "signal": "R22回暖预案待命 — 恐慌回升>25时启用",
        "detail": f"恐慌{panic_index}<25冰点中，R22回暖预案准备就绪。"
                  f"回暖确认条件：恐慌连续2日>25+上证收涨+涨跌比>1:1。"
                  f"恢复第1周仓位≤20%，仅限防御型标的，止损收紧至-2.5%",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "R22"
    })
    return warnings


def check_r23_false_recovery(panic_index: int, index_data: dict, klines: list, breadth: dict) -> list:
    """R23: 假回暖识别与保护 (v4.2.1 阈值修正)
    防止追入一日游反弹的陷阱
    识别条件：A)恐慌单日回升后次日回跌 B)放量不涨 C)虚涨 D)Level2主力净流入反转
    
    v4.2.1变更:
    - R23-C阈值: 上涨家数>65%(原70%) + 涨停<25只(原30只)
    - R23-D数据源: 北向→Level2板块主力净流入(北向已改为T+1盘后)
    """
    warnings = []
    if panic_index >= 25:
        return warnings  # 非冰点不需要
    
    indices = index_data.get("indices", [])
    sz = next((i for i in indices if "上证" in i.get("name", "")), None)
    if not sz or not klines or len(klines) < 3:
        return warnings
    
    today_pct = sz.get("pct", 0)
    
    # 条件B：上证单日涨幅>1.5%但成交量小于前3日均量
    recent = klines[-4:-1] if len(klines) >= 4 else klines[-3:]
    avg_vol3 = sum(k["volume"] for k in recent) / len(recent) if recent else 1
    last_vol = klines[-1]["volume"] if klines else 0
    
    # 条件A：昨日涨+今日跌的快速反转
    yesterday = klines[-2] if len(klines) >= 2 else None
    if yesterday and yesterday["close"] > yesterday["open"] and sz.get("pct", 0) < -0.5:
        yest_gain = (yesterday["close"] - yesterday["open"]) / yesterday["open"] * 100
        warnings.append({
            "type": "R23_FALSE_RECOVERY_A",
            "level": "\U0001f534 警惕",
            "signal": "假回暖预警A：快速反转 — 昨日涨今日跌",
            "detail": f"昨日涨{yest_gain:.1f}%今日跌{today_pct:.1f}%，典型的冰点假回暖一日游。保护动作：维持空仓，冷却≥3交易日",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R23"
        })
    
    # 条件B：放量不涨（虚涨）
    if avg_vol3 > 0 and last_vol > 0:
        vol_ratio = last_vol / avg_vol3
        if vol_ratio > 1.5 and abs(today_pct) < 0.3:
            warnings.append({
                "type": "R23_FALSE_RECOVERY_B",
                "level": "\U0001f7e1 谨慎",
                "signal": "假回暖预警B：放量滞涨 — 虚涨特征",
                "detail": f"成交量放大至近期均量的{vol_ratio:.1f}倍但价格变化仅{today_pct:.2f}%，疑似非真实回暖。保护动作：仓位上限降至15%",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rule": "R23"
            })
    
    # 条件C (v4.2.1: 阈值下调)：上涨家数>65%但涨停家数<25只（虚涨) 
    up_ratio_pct = breadth.get("up_ratio_pct", breadth.get("up_indices", 0) / max(1, breadth.get("up_indices", 0) + breadth.get("down_indices", 1)) * 100)
    limit_up = breadth.get("limit_up", breadth.get("up_indices", 0))
    if isinstance(up_ratio_pct, float) and up_ratio_pct > 65 and isinstance(limit_up, (int, float)) and limit_up < 25:
        warnings.append({
            "type": "R23_FALSE_RECOVERY_C",
            "level": "\U0001f7e1 谨慎",
            "signal": f"假回暖预警C(v4.2.1)：虚涨 — 涨跌比{up_ratio_pct:.0f}%但涨停仅{int(limit_up)}只",
            "detail": f"上涨占比{up_ratio_pct:.0f}% > 65%(阈值已下调)但涨停仅{int(limit_up)}只 < 25只，典型的虚涨假回暖。保护动作：维持空仓或上限≤10%",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R23"
        })
    
    # 条件D (v4.2.1: 北向→Level2切换)：板块主力净流入D1为正→D2为负 = 假回暖信号
    sector_flow = index_data.get("sector_flow", index_data.get("top_sectors", []))
    if isinstance(sector_flow, list) and len(sector_flow) >= 2:
        d1_net = sector_flow[-2].get("net_amount", sector_flow[-2].get("net_inflow", 0)) if isinstance(sector_flow[-2], dict) else 0
        d2_net = sector_flow[-1].get("net_amount", sector_flow[-1].get("net_inflow", 0)) if isinstance(sector_flow[-1], dict) else 0
        if isinstance(d1_net, (int, float)) and isinstance(d2_net, (int, float)):
            if d1_net > 0 > d2_net:
                warnings.append({
                    "type": "R23_FALSE_RECOVERY_D",
                    "level": "\U0001f7e1 谨慎",
                    "signal": "假回暖预警D(v4.2.1)：主力净流入反转 — 前日正→今日负",
                    "detail": f"板块主力净流入从前日正转为今日负，主力资金一日游。保护动作：维持空仓，冷却≥2交易日",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "rule": "R23"
                })
    
    return warnings


def check_r23e_structural_divergence(index_data: dict, breadth: dict) -> list:
    """R23-E: 结构性分化识别 (v4.2.2)
    识别科创涨+主板跌的假回暖陷阱
    核心信号:
      1. 科创50涨幅>1% 但 上证50跌幅>0.5% → 结构性分化
      2. 创业板涨幅>0.8% 但 上证50跌>0.3% → 小盘确认大盘未确认
      3. 多个指数中仅1-2个上涨其余均跌 → 分化信号
    """
    warnings = []
    indices = index_data.get("indices", [])
    if not indices or len(indices) < 3:
        return warnings

    kc50 = next((i for i in indices if "科创" in i.get("name", "")), None)
    sz = next((i for i in indices if "上证" in i.get("name", "") and "50" not in i.get("name", "")), None)
    sz50 = next((i for i in indices if "上证50" in i.get("name", "")), None)
    cy = next((i for i in indices if "创业板" in i.get("name", "")), None)

    if kc50 and sz:
        kc_pct = kc50.get("pct", 0)
        sz_pct = sz.get("pct", 0)
        if kc_pct > 1.0 and sz_pct < -0.3:
            warnings.append({
                "type": "R23E_STRUCTURAL_DIVERGENCE_KC",
                "level": "\U0001f534 警惕",
                "signal": "结构性分化：科创涨+上证跌 — 假回暖",
                "detail": f"科创50涨{kc_pct:.2f}%但上证跌{sz_pct:.2f}%，科技孤岛假回暖。维持空仓，冷却>=2交易日",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rule": "R23-E"
            })

    if cy and sz50:
        cy_pct = cy.get("pct", 0)
        sz50_pct = sz50.get("pct", 0)
        if cy_pct > 0.8 and sz50_pct < -0.3:
            warnings.append({
                "type": "R23E_STRUCTURAL_DIVERGENCE_CY50",
                "level": "\U0001f7e1 谨慎",
                "signal": "结构性分化：创业板涨+上证50跌",
                "detail": f"创业板涨{cy_pct:.2f}%但上证50跌{sz50_pct:.2f}%，权重未确认回暖。空仓上限<=10%",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rule": "R23-E"
            })

    up_count = sum(1 for i in indices if i.get("pct", 0) > 0.3)
    down_count = sum(1 for i in indices if i.get("pct", 0) < -0.3)
    total = up_count + down_count
    if total >= 4 and up_count <= 2 and down_count >= 3:
        warnings.append({
            "type": "R23E_STRUCTURAL_DIVERGENCE_SPLIT",
            "level": "\U0001f7e1 谨慎",
            "signal": f"结构性分化：仅{up_count}指上涨 vs {down_count}指下跌",
            "detail": f"市场分裂严重({up_count}升{down_count}跌)，不具备整体回暖条件。维持空仓",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R23-E"
        })

    return warnings


def check_r25_lpr_catalyst(index_data: dict, temperature: int) -> list:
    """R25: LPR/政策催化剂应对规则 (v4.2.2)
    LPR报价日为每月20日
    规则:
      1. LPR调降 -> 开盘30分钟观测，不放量不追
      2. LPR不变 -> 维持原有策略
      3. 降准等重大政策 -> 3日观察期
    """
    warnings = []
    today = date.today()
    lpr_day = date(today.year, today.month, 20)
    while lpr_day.weekday() >= 5:
        lpr_day += timedelta(days=1)

    if today != lpr_day:
        return warnings

    warnings.append({
        "type": "R25_LPR_DAY",
        "level": "\U0001f7e1 关注",
        "signal": "今日LPR报价日 — 09:15公布结果",
        "detail": f"LPR报价日：开盘30分钟内勿追涨杀跌。调降也需量能配合，不变维持原策略。当前温度{temperature}度",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "R25"
    })

    if temperature < 35:
        warnings.append({
            "type": "R25_LPR_ICE",
            "level": "\U0001f7e1 谨慎",
            "signal": "LPR日+冰点 — 警惕政策博弈假回暖",
            "detail": f"冰点温度{temperature}度+LPR日，LPR调降可能短时反弹(R23假回暖)。观望30分钟，确认放量+涨跌比>1后方可试探仓<=10%",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R25"
        })

    return warnings


def check_r26_earnings_linkage() -> list:
    """R26: 核心标的财报->A股联动规则 (v4.2.2)
    英伟达/特斯拉/苹果等核心科技股财报->A股映射板块联动
    """
    warnings = []
    today = date.today()

    earnings_calendar = {
        date(2026, 5, 20): {
            "name": "NVIDIA (NVDA)",
            "sector": "AI算力",
            "a_stock_map": "工业富联(601138)/中际旭创(300308)/新易盛(300502)",
            "timing": "美股盘后(北京时间明早)"
        },
        date(2026, 5, 21): {
            "name": "NVIDIA 财报反应日",
            "sector": "AI算力",
            "a_stock_map": "工业富联(601138)/中际旭创(300308)/浪潮(000977)",
            "timing": "今日A股开盘反应前夜英伟达财报"
        },
    }

    for edate, info in earnings_calendar.items():
        delta = (today - edate).days
        if abs(delta) <= 1:
            level = "\U0001f535 重点" if delta == 0 else "\U0001f7e1 关注"
            prefix = "前夜" if delta == -1 else ("今日" if delta == 0 else "昨日")
            warnings.append({
                "type": "R26_EARNINGS_LINKAGE",
                "level": level,
                "signal": f"{info['name']}财报{prefix} — {info['sector']}板块扰动预警",
                "detail": f"{info['timing']}。A股映射: {info['a_stock_map']}。R26: 财报超预期!=追涨，利好出尽常见；miss可能引发板块恐慌补跌",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rule": "R26"
            })

    return warnings


def check_v12_extended_freeze(temperature: int, panic_index: int, klines: list) -> list:
    """V12: 连续冰点>10天触发升级应对 (v4.2.2)
    黄色(7-9天): 准备回暖预案
    橙色(10-14天): 仓位上限降至10%
    红色(15天+): 强制空仓+系统体检
    """
    warnings = []
    if not klines or len(klines) < 5:
        return warnings

    ice_days = 0
    for k in reversed(klines):
        daily_chg = (k["close"] - k["open"]) / k["open"] * 100 if k.get("open") else 0
        if daily_chg < -0.3 or k.get("volume", 0) < sum(item.get("volume", 0) for item in klines[-5:]) / 5 * 0.8:
            ice_days += 1
        else:
            break

    if temperature >= 35 or panic_index >= 25:
        return warnings

    consecutive_freeze = max(ice_days, 9)

    if consecutive_freeze >= 15:
        warnings.append({
            "type": "V12_RED_ALERT",
            "level": "\U0001f534 冻结",
            "signal": f"V12红色预警：连续冰点{consecutive_freeze}天 — 强制体检",
            "detail": f"冰点{consecutive_freeze}天>=15红线。强制: 系统检查+规则审计+现金>=90%+回暖需3日确认",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "V12"
        })
    elif consecutive_freeze >= 10:
        warnings.append({
            "type": "V12_ORANGE_ALERT",
            "level": "\U0001f7e0 橙色",
            "signal": f"V12橙色预警：连续冰点{consecutive_freeze}天 — 仓位上限10%",
            "detail": f"冰点第{consecutive_freeze}天(10-14区间)。仓位<=10%，最小单位减半，止损收紧至-2%",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "V12"
        })
    elif consecutive_freeze >= 7:
        warnings.append({
            "type": "V12_YELLOW_ALERT",
            "level": "\U0001f7e1 注意",
            "signal": f"V12黄色预警：连续冰点{consecutive_freeze}天 — 准备回暖预案",
            "detail": f"冰点第{consecutive_freeze}天(7-9区间)。提前准备防御型备选标的池，等待恐慌>25信号",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "V12"
        })

    return warnings


def check_fm032_bottom_signal(panic_index: int, klines: list) -> list:
    """FM-032 地量见底信号（半激活）
    不作为主动买入信号，仅作为回暖期参考信号
    """
    warnings = []
    if panic_index >= 40 or not klines or len(klines) < 5:
        return warnings
    
    recent = klines[-5:]
    avg_vol20_approx = sum(k["volume"] for k in klines) / len(klines)
    
    # 连续3日成交量 < 40% 前20日均量（近似）
    con_shrink = all(recent[i]["volume"] < avg_vol20_approx * 0.4 for i in range(-3, 0)) if len(recent) >= 3 else False
    
    # 跌幅趋缓
    if con_shrink:
        daily_drops = []
        for i in range(1, 4):
            if i < len(recent):
                drop = (recent[-i]["close"] - recent[-i-1]["close"]) / recent[-i-1]["close"] * 100 if recent[-i-1]["close"] else 0
                daily_drops.append(drop)
        slowing = all(abs(d) < 1.0 for d in daily_drops) if daily_drops else False
        
        warnings.append({
            "type": "FM032_BOTTOM_SIGNAL",
            "level": "\U0001f7e1 参考" if not slowing else "\U0001f7e0 信号",
            "signal": "FM-032 地量见底" + ("确认" if slowing else "观察中"),
            "detail": f"连续缩量至均量的40%以下{'且跌幅趋缓' if slowing else '，等待跌幅趋缓确认'}。"
                      f"回暖期可作为筛选标的的参考信号，不可单独触发交易",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "FM-032"
        })
    
    return warnings


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# 猎手系统 v4.2 - 置信度标签系统 (R22/R23回暖防护)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

# ─────────────────────────────────────────────
# 猎手系统 v4.2.1 - 交易纪律评分系统
# ─────────────────────────────────────────────

def calculate_discipline_score(trade_log: list) -> dict:
    """计算交易纪律评分 v4.2.1
    
    评估维度：
    1. 冰点拒绝入场(R18) — 冰点期违规交易占比
    2. 按照信号执行 — 非情绪化交易占比
    3. 冰期不重仓(R09-v2) — 单次仓位不超过对应温度上限
    4. 单日不超2次(R05) — 单日交易次数
    
    Args:
        trade_log: 交易日志列表，每条含 {date, symbol, direction, panic_index, 
                    position_pct, is_signal_based, pnl_pct}
    
    Returns:
        score dict
    """
    if not trade_log:
        return {
            "total_score": 100,
            "items": [],
            "valid_trades": 0,
            "violations": 0,
            "score_label": "🏆 完美",
            "version": "v4.2.1"
        }
    
    valid_trades = 0
    violations = 0
    items = []
    
    # 1. R18检查：冰点期违规 (panic_index < 35)
    r18_violations = sum(1 for t in trade_log if t.get("panic_index", 50) < 35 and t.get("direction", "") in ["买入", "buy"])
    r18_total = sum(1 for t in trade_log if t.get("panic_index", 50) < 50)
    r18_score = max(0, 100 - (r18_violations / max(1, r18_total) * 100)) if r18_total > 0 else 100
    items.append({
        "rule": "R18-冰点禁入",
        "weight": 0.40,
        "score": round(r18_score, 1),
        "detail": f"冰点期违规买入{r18_violations}/{r18_total}次"
    })
    
    # 2. 信号执行检查
    not_signal = sum(1 for t in trade_log if not t.get("is_signal_based", True))
    signal_score = max(0, 100 - (not_signal / max(1, len(trade_log)) * 100))
    items.append({
        "rule": "信号执行",
        "weight": 0.30,
        "score": round(signal_score, 1),
        "detail": f"非信号交易{not_signal}/{len(trade_log)}笔"
    })
    
    # 3. R09-v2检查：超仓位上限
    over_pos = sum(1 for t in trade_log if t.get("position_pct", 0) > t.get("max_allowed_pct", 100))
    pos_score = max(0, 100 - (over_pos / max(1, len(trade_log)) * 100))
    items.append({
        "rule": "R09-v2-仓位上限",
        "weight": 0.15,
        "score": round(pos_score, 1),
        "detail": f"超仓位上限{over_pos}/{len(trade_log)}笔"
    })
    
    # 4. R05检查：单日超2次
    from collections import Counter
    daily_counts = Counter(t.get("date", "") for t in trade_log)
    exceed_days = sum(1 for c in daily_counts.values() if c > 2)
    r05_score = max(0, 100 - exceed_days * 25)
    items.append({
        "rule": "R05-单日≤2次",
        "weight": 0.15,
        "score": round(r05_score, 1),
        "detail": f"单日超2次天数: {exceed_days}"
    })
    
    total_score = sum(item["score"] * item["weight"] for item in items)
    
    if total_score >= 90:
        label = "🏆 优秀"
    elif total_score >= 80:
        label = "✅ 良好"
    elif total_score >= 60:
        label = "⚠️ 及格"
    else:
        label = "❌ 不及格"
    
    violations = int(sum(item["score"] < 60 for item in items))
    
    return {
        "total_score": round(total_score, 1),
        "items": items,
        "valid_trades": len([t for t in trade_log if t.get("pnl_pct", 0) >= 0]) if trade_log else 0,
        "violations": violations,
        "score_label": label,
        "version": "v4.2.1"
    }


# ─────────────────────────────────────────────
# 猎手系统 v4.2 - 置信度标签系统 (R22/R23回暖防护)
# ─────────────────────────────────────────────

CONFIDENCE_LEVELS = {
    "HIGH": {"emoji": "\U0001f3af", "label": "\u9ad8\u7f6e\u4fe1", "min": 75, "color": "green"},
    "MEDIUM": {"emoji": "\u26a1", "label": "\u4e2d\u7f6e\u4fe1", "min": 50, "color": "yellow"},
    "LOW": {"emoji": "\U0001f3b2", "label": "\u4f4e\u7f6e\u4fe1", "min": 0, "color": "gray"},
}

SIGNAL_STRENGTH = {
    "STRONG": {"emoji": "\U0001f48e", "label": "\u5f3a\u52bf\u4fe1\u53f7", "min_score": 85},
    "MODERATE": {"emoji": "\U0001f4c8", "label": "\u4e2d\u6027\u4fe1\u53f7", "min_score": 60},
    "WEAK": {"emoji": "\U0001f4ca", "label": "\u5f31\u52bf\u4fe1\u53f7", "min_score": 0},
}

def calculate_confidence(factors: dict) -> tuple:
    """
    \u8ba1\u7b97\u7efc\u5408\u7f6e\u4fe1\u5ea6
    \u56e0\u7d20: trend, volume, momentum, breadth, divergence
    \u8fd4\u56de: (level, score, label)
    """
    weights = {"trend": 0.25, "volume": 0.20, "momentum": 0.20, "breadth": 0.20, "divergence": 0.15}

    score = 0
    for factor, weight in weights.items():
        factor_score = factors.get(factor, 50)
        score += factor_score * weight

    if score >= 75:
        level, config = "HIGH", CONFIDENCE_LEVELS["HIGH"]
    elif score >= 50:
        level, config = "MEDIUM", CONFIDENCE_LEVELS["MEDIUM"]
    else:
        level, config = "LOW", CONFIDENCE_LEVELS["LOW"]

    label = config[chr(34) + "emoji" + chr(34)] + " " + config[chr(34) + "label" + chr(34)] + " (" + str(round(score)) + "%)"
    return level, score, label


def get_signal_strength(score: float) -> str:
    """\u6839\u636e\u5206\u6570\u83b7\u53d6\u4fe1\u53f7\u5f3a\u5ea6\u6807\u7b7e"""
    if score >= 85:
        config = SIGNAL_STRENGTH["STRONG"]
    elif score >= 60:
        config = SIGNAL_STRENGTH["MODERATE"]
    else:
        config = SIGNAL_STRENGTH["WEAK"]
    return f'{config["emoji"]} {config["label"]}'


def analyze_confidence_factors(index_data: dict, klines: list, breadth: dict, warnings: list) -> dict:
    """
    \u5206\u6790\u7f6e\u4fe1\u5ea6\u56e0\u7d20
    """
    factors = {}

    indices = index_data.get("indices", [])
    if indices:
        avg_pct = sum(i.get("pct", 0) for i in indices) / len(indices) if indices else 0
        factors["trend"] = 50 + avg_pct * 5
        factors["trend"] = max(0, min(100, factors["trend"]))
    else:
        factors["trend"] = 50

    if klines and len(klines) >= 2:
        recent_vol = klines[-1].get("volume", 0)
        prev_vol = klines[-2].get("volume", 1)
        vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1
        factors["volume"] = min(100, 50 + (vol_ratio - 1) * 25)
    else:
        factors["volume"] = 50

    if klines and len(klines) >= 3:
        recent_changes = []
        for i in range(-3, 0):
            if i >= -len(klines):
                k = klines[i]
                recent_changes.append((k.get("close", 0) - k.get("open", 0)) / k.get("open", 1) * 100)
        factors["momentum"] = 50 + sum(recent_changes) / len(recent_changes) * 5
        factors["momentum"] = max(0, min(100, factors["momentum"]))
    else:
        factors["momentum"] = 50

    up = breadth.get("up_indices", 0)
    down = breadth.get("down_indices", 1)
    breadth_ratio = up / (up + down) if (up + down) > 0 else 0.5
    factors["breadth"] = breadth_ratio * 100
    factors["breadth"] = max(0, min(100, factors["breadth"]))

    has_divergence = any("\u80cc\u79bb" in w.get("signal", "") for w in warnings)
    has_anomaly = any("\u5f02\u52a8" in w.get("signal", "") for w in warnings)
    factors["divergence"] = 30 if has_divergence else (60 if has_anomaly else 80)

    return factors


def add_confidence_to_report(report: dict) -> dict:
    """
    \u4e3a\u62a5\u544a\u6dfb\u52a0\u7f6e\u4fe1\u5ea6\u6807\u7b7e
    """
    factors = analyze_confidence_factors(
        report.get("index", {}),
        report.get("klines", {}).get("sh000001", []),
        report.get("breadth", {}),
        report.get("warnings", [])
    )

    level, score, label = calculate_confidence(factors)
    signal_strength = get_signal_strength(score)

    report["confidence"] = {
        "level": level,
        "score": round(score, 1),
        "label": label,
        "factors": factors,
        "signal_strength": signal_strength,
        "version": "3.37"
    }

    return report


def format_confidence_report(report: dict) -> str:
    """\u683c\u5f0f\u5316\u7f6e\u4fe1\u5ea6\u62a5\u544a"""
    conf = report.get("confidence", {})
    lines = []

    lines.append(f"\n{'='*20}")
    lines.append(f"\u3010\U0001f3af \u7f6e\u4fe1\u5ea6\u5206\u6790 v3.37\u3011")
    lines.append(f"{'='*20}")
    lines.append(f"  \u7efc\u5408\u7f6e\u4fe1\u5ea6: {conf.get('label', 'N/A')}")
    lines.append(f"  \u4fe1\u53f7\u5f3a\u5ea6: {conf.get('signal_strength', 'N/A')}")

    factors = conf.get("factors", {})
    lines.append(f"\n  \u56e0\u5b50\u5206\u89e3:")
    lines.append(f"    \U0001f4ca \u8d8b\u52bf: {factors.get('trend', 0):.1f}")
    lines.append(f"    \U0001f4e6 \u6210\u4ea4\u91cf: {factors.get('volume', 0):.1f}")
    lines.append(f"    \u26a1 \u52a8\u91cf: {factors.get('momentum', 0):.1f}")
    lines.append(f"    \U0001f30a \u5e7f\u5ea6: {factors.get('breadth', 0):.1f}")
    lines.append(f"    \U0001f504 \u80cc\u79bb: {factors.get('divergence', 0):.1f}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    closing = "--closing" in sys.argv
    report = full_scan(closing_mode=closing)
    report = add_confidence_to_report(report)
    print(format_report(report))
    print(format_confidence_report(report))

    # 保存日志
    DATA_DIR.mkdir(exist_ok=True)
    log_file = DATA_DIR / "logs" / f"{date.today().isoformat()}.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    sys.exit(1 if report["verdict"] == "RISK_HIGH" else 0)


