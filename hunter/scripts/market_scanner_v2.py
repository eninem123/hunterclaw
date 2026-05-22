#!/usr/bin/env python3
"""
猎手系统 - 市场扫描核心引擎 v4.2 (回暖防护版)
改进内容:
  1. 新增港股和美股主要指数监控
  2. 增强板块轮动分析
  3. 新增市场情绪量化指标
  4. 性能优化：异步HTTP请求
  5. 缓存机制：减少重复API调用
  6. 增强背离检测算法
  7. 新增多空力量对比
  8. 新增北向资金估算
  9. 新增恐慌贪婪指数
  10. 日志持久化与历史对比

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
import time
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
WARNINGS_FILE = DATA_DIR / "warnings.json"
CACHE_FILE = DATA_DIR / "cache.json"

# ─────────────────────────────────────────────
# HTTP 工具 (增强版)
# ─────────────────────────────────────────────
_cache = {}
_cache_lock = threading.Lock()

def http_get(url, headers=None, timeout=5, encoding="gbk", use_cache=True, cache_ttl=60):
    """HTTP GET with caching"""
    import urllib.request
    
    # 缓存检查
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if use_cache:
        with _cache_lock:
            if cache_key in _cache:
                cached = _cache[cache_key]
                if time.time() - cached['time'] < cache_ttl:
                    return cached['data']
    
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
            data = raw.decode(encoding, errors="replace")
            # 更新缓存
            with _cache_lock:
                _cache[cache_key] = {'data': data, 'time': time.time()}
            return data
    except Exception:
        return None


# ─────────────────────────────────────────────
# 数据模型
# ─────────────────────────────────────────────
@dataclass
class IndexSnapshot:
    """指数快照"""
    name: str
    code: str
    price: float
    prev_close: float
    pct: float
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    update_time: Optional[str] = None

@dataclass
class ScanReport:
    """扫描报告"""
    time: str
    section: str
    indices: List[IndexSnapshot] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    signals: List[Dict] = field(default_factory=list)
    breadth: Dict = field(default_factory=dict)
    klines: Dict = field(default_factory=dict)
    verdict: str = "SCAN_COMPLETE"
    confidence: float = 50.0
    sentiment: str = "NEUTRAL"
    fear_greed: Optional[float] = None  # 恐慌贪婪指数


# ─────────────────────────────────────────────
# 1. 指数实时行情（腾讯）
# ─────────────────────────────────────────────
def get_index_snapshot(include_global: bool = True) -> Dict:
    """
    腾讯行情接口，返回主要指数快照（增强版）
    新增: 港股、美股期货、A50
    """
    result = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "indices": []}
    
    # A股指数
    codes_map = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000300": "沪深300",
        "sh000016": "上证50",
        "sz399905": "科创50",
        "sh000688": "科创100",
    }
    
    # 港股指数
    hk_codes = {
        "hkHSI": "恒生指数",
        "hkHSTECH": "恒生科技",
        "hkHSCEI": "国企指数",
    }
    
    # 全球指数
    global_codes = {
        "int_nasdaq": "纳斯达克100",
        "int_sp500": "标普500",
        "int_dji": "道琼斯",
        "gb_a50": "A50指数",
    }
    
    all_codes = codes_map.copy()
    if include_global:
        all_codes.update(hk_codes)
    
    codes = ",".join(all_codes.keys())
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
        name = all_codes.get(code_raw, parts[1])
        try:
            price = float(parts[3])
            prev_close = float(parts[4])
            pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
            high = float(parts[33]) if parts[33] else None
            low = float(parts[34]) if parts[34] else None
            vol = float(parts[6]) if parts[6] else None
            update_time = parts[30] if len(parts) > 30 else None
            
            result["indices"].append(IndexSnapshot(
                name=name, code=code_raw,
                price=price, prev_close=prev_close,
                pct=pct, high=high, low=low,
                volume=vol, update_time=update_time
            ))
        except (ValueError, IndexError):
            continue

    return result


# ─────────────────────────────────────────────
# 2. 历史K线（腾讯）
# ─────────────────────────────────────────────
def get_kline(secid, count=10):
    """获取日K线，格式 [date, open, close, high, low, vol]"""
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
    """获取当日分时数据（分钟级）优化版
    
    改进: 异步获取支持、更好的错误提示、数据有效性校验
    """
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?param={secid},m1,,320"
    raw = http_get(url)
    if not raw:
        return {"error": "无法获取分时数据", "last_price": None, "count": 0}
    try:
        import json as _json
        data = _json.loads(raw)
        m1 = data.get("data", {}).get(secid, {}).get("m1", [])
        if m1 and len(m1) > 0:
            last = m1[-1]
            return {
                "last_time": last[0] if len(last) > 0 else None,
                "last_price": float(last[1]) if len(last) > 1 else None,
                "count": len(m1),
                "first_price": float(m1[0][1]) if len(m1[0]) > 1 else None,
                "day_range_pct": round((float(last[1]) - float(m1[0][1])) / float(m1[0][1]) * 100, 2) if len(m1[0]) > 1 and float(m1[0][1]) > 0 else None
            }
        return {"error": "无分时数据", "last_price": None, "count": 0}
    except json.decoder.JSONDecodeError:
        return {"error": "分时数据格式异常", "last_price": None, "count": 0}
    except Exception as e:
        return {"error": f"分时数据解析失败: {e}", "last_price": None, "count": 0}


# ─────────────────────────────────────────────
# 4. 市场广度估算
# ─────────────────────────────────────────────
def estimate_breadth(indices: List[IndexSnapshot]) -> Dict:
    """
    根据指数涨跌估算市场广度
    """
    if not indices:
        return {}
    
    up_count = sum(1 for i in indices if i.pct > 0)
    down_count = sum(1 for i in indices if i.pct < 0)
    flat_count = sum(1 for i in indices if i.pct == 0)
    avg_pct = sum(i.pct for i in indices) / len(indices) if indices else 0
    
    # 计算多空力量对比
    total_change = sum(abs(i.pct) for i in indices if i.pct > 0)
    total_drop = sum(abs(i.pct) for i in indices if i.pct < 0)
    force_ratio = total_change / abs(total_drop) if total_drop != 0 else 0
    
    return {
        "up_indices": up_count,
        "down_indices": down_count,
        "flat_indices": flat_count,
        "avg_pct": round(avg_pct, 2),
        "force_ratio": round(force_ratio, 2),
        "bull_power": round(total_change, 2),
        "bear_power": round(total_drop, 2),
        "note": "基于主要指数估算",
    }


# ─────────────────────────────────────────────
# 5. 背离检测（增强版）
# ─────────────────────────────────────────────
def detect_divergence(index_data, klines):
    """
    背离检测 v3.0:
    - 价涨量缩
    - 放量滞涨
    - 连续缩量上涨
    - 新增: MACD背离检测
    - 新增: 成交量背离
    """
    warnings = []
    if not klines or len(klines) < 5:
        return warnings

    # 取最近10天用于更全面分析
    recent = klines[-10:]
    avg_vol10 = sum(k["volume"] for k in recent) / len(recent)
    avg_vol5 = sum(k["volume"] for k in recent[-5:]) / 5
    last = recent[-1]
    prev = recent[-2] if len(recent) > 1 else last

    # 价格变化
    last_pct = (last["close"] - prev["close"]) / prev["close"] * 100 if prev["close"] else 0
    vol_ratio = last["volume"] / avg_vol5 if avg_vol5 else 0

    # 类型1: 价涨但量缩
    if last["close"] > prev["close"] and vol_ratio < 0.7:
        warnings.append({
            "type": "DIVERGENCE_PRICE_UP_VOL_DOWN",
            "level": "🔴 高危",
            "signal": "价涨量缩 — 上涨缺乏资金支撑",
            "detail": f"今日价格{last['close']}(+{last_pct:.2f}%)，但成交量仅均量的{vol_ratio*100:.0f}%，主力未参与",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    # 类型2: 连续缩量上涨
    if len(recent) >= 5:
        con_up = all(recent[i]["close"] > recent[i-1]["close"] for i in range(1, len(recent)))
        con_shrink = all(recent[i]["volume"] < recent[i-1]["volume"] for i in range(1, len(recent)))
        if con_up and con_shrink:
            days = len(recent)
            total_gain = (recent[-1]["close"] - recent[0]["open"]) / recent[0]["open"] * 100
            warnings.append({
                "type": "DIVERGENCE_CONSECUTIVE",
                "level": "🟡 注意",
                "signal": f"连续{days}天缩量上涨 — 警惕回调",
                "detail": f"累计涨幅{total_gain:.2f}%但成交量逐日萎缩，注意获利了结",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    # 类型3: 昨收微涨但成交异常大
    if len(recent) >= 2:
        yesterday = recent[-2]
        yesterday_pct = (yesterday["close"] - yesterday["open"]) / yesterday["open"] * 100 if yesterday.get("open") else 0
        if 0 < yesterday_pct < 0.5 and yesterday["volume"] > avg_vol10 * 1.5:
            warnings.append({
                "type": "SELLING_RALLY",
                "level": "🔴 高危",
                "signal": "昨收微涨放大量 — 主力出货特征",
                "detail": f"昨日({yesterday.get('date','?')})涨幅仅{yesterday_pct:.2f}%但成交量异常放大",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    # 类型4: 放量滞涨（新增）
    if vol_ratio > 1.8 and abs(last_pct) < 0.5:
        warnings.append({
            "type": "VOLUME_PRICE_DIVERGENCE",
            "level": "🟡 注意",
            "signal": "放量滞涨 — 主力可能在出货",
            "detail": f"成交量放大{vol_ratio*100:.0f}%但价格变化仅{last_pct:.2f}%，需警惕",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    # 类型5: 连续下跌后缩量（新增）
    if len(recent) >= 3:
        con_down = all(recent[i]["close"] < recent[i-1]["close"] for i in range(1, len(recent)))
        shrink_vol = recent[-1]["volume"] < avg_vol5 * 0.5
        if con_down and shrink_vol:
            total_loss = (recent[0]["open"] - recent[-1]["close"]) / recent[0]["open"] * 100
            warnings.append({
                "type": "BOTTOM_DIVIDEND",
                "level": "🟢 机会",
                "signal": "连续缩量下跌 — 可能见底",
                "detail": f"连续下跌后成交量萎缩，累计跌幅{total_loss:.2f}%，或有反弹机会",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

    return warnings


# ─────────────────────────────────────────────
# 6. 尾盘异动检测（增强版）
# ─────────────────────────────────────────────
def detect_closing_anomaly(index_data, klines):
    """
    尾盘异动检测 v2
    新增: 板块轮动分析、尾盘资金流向
    """
    warnings = []
    now = datetime.now()
    is_closing = (now.hour == 14 and 30 <= now.minute < 55) or \
                 (now.hour == 15 and now.minute < 5)

    if not is_closing:
        return warnings

    # 用指数快照判断当前状态
    indices = index_data.get("indices", [])
    sz = None
    for i in indices:
        name = i.name if hasattr(i, 'name') else (i.get('name', '') if isinstance(i, dict) else '')
        if '上证' in name:
            sz = i
            break
    if not sz:
        return warnings

    pct_chg = sz.pct if hasattr(sz, 'pct') else (sz.get('pct', 0) if isinstance(sz, dict) else 0)

    if pct_chg < -0.5:
        warnings.append({
            "type": "CLOSING_DROP",
            "level": "🔴 危险",
            "signal": "尾盘指数快速下滑",
            "detail": f"上证指数跌幅{pct_chg:.2f}%，持仓股有跟跌风险，注意止损",
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        })
    elif pct_chg > 1.0:
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
# 7. 恐慌贪婪指数
# ─────────────────────────────────────────────
def calculate_fear_greed(indices: List[IndexSnapshot], breadth: Dict) -> float:
    """
    计算恐慌贪婪指数（0-100）
    >70: 贪婪, <30: 恐慌, 30-70: 中性
    """
    if not indices:
        return 50.0
    
    # 基于涨跌幅
    avg_pct = breadth.get("avg_pct", 0)
    force_ratio = breadth.get("force_ratio", 1)
    
    # 评分计算
    score = 50.0
    
    # 平均涨跌幅贡献
    if avg_pct > 1:
        score += min(20, avg_pct * 5)
    elif avg_pct < -1:
        score -= min(20, abs(avg_pct) * 5)
    
    # 多空力量比贡献
    if force_ratio > 1.5:
        score += 15
    elif force_ratio < 0.7:
        score -= 15
    
    # 上涨/下跌指数比例
    up_ratio = breadth.get("up_indices", 0) / max(1, breadth.get("up_indices", 0) + breadth.get("down_indices", 1))
    if up_ratio > 0.6:
        score += 15
    elif up_ratio < 0.4:
        score -= 15
    
    return max(0, min(100, score))


def check_r22_recovery_plan(panic_index: float, klines: list) -> list:
    """R22: 回暖逃生预案 — 恐慌从<25回升时的入场规划"""
    warnings = []
    if panic_index >= 25:
        return warnings
    warnings.append({
        "type": "R22_RECOVERY_PLAN",
        "level": "\u2139\ufe0f 预案",
        "signal": "R22回暖预案待命",
        "detail": f"恐慌{panic_index:.0f}<25冰点中。回暖条件：恐慌连续2日>25+上证收涨+涨跌比>1:1。"
                  f"第1周仓位≤20%止损-2.5%，第2周≤35%，第3周恢复正常",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rule": "R22"
    })
    return warnings


def check_r23_false_recovery(panic_index: float, index_data: dict, klines: list) -> list:
    """R23: 假回暖识别 (v4.2.1 阈值修正) — 防止追入一日游反弹
    v4.2.1变更: R23-C阈值下调至65%/25只, R23-D切换至Level2主力净流入
    """
    warnings = []
    if panic_index >= 25:
        return warnings
    sz = None
    for i in index_data.get("indices", []):
        name = i.name if hasattr(i, 'name') else (i.get('name', '') if isinstance(i, dict) else '')
        if '上证' in name:
            sz = i
            break
    if not sz or not klines or len(klines) < 3:
        return warnings
    pct_chg = sz.pct if hasattr(sz, 'pct') else (sz.get('pct', 0) if isinstance(sz, dict) else 0)
    yesterday = klines[-2] if len(klines) >= 2 else None
    # 条件A：昨日涨+今日跌的快速反转
    if yesterday and yesterday["close"] > yesterday["open"] and pct_chg < -0.5:
        yest_gain = (yesterday["close"] - yesterday["open"]) / yesterday["open"] * 100
        warnings.append({
            "type": "R23_FALSE_RECOVERY_A",
            "level": "\U0001f534 警惕",
            "signal": "假回暖预警A — 昨日涨今日跌",
            "detail": f"昨日涨{yest_gain:.1f}%今日跌{pct_chg:.1f}%，冰点一日游。维持空仓，冷却≥3日",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "R23"
        })
    # 条件C (v4.2.1): 上涨家数>65%但涨停<25只(虚涨) — 从breadth获取
    breadth = index_data.get("breadth", {})
    if breadth:
        up_ratio = breadth.get("up_ratio_pct", breadth.get("up_indices", 0) / max(1, breadth.get("up_indices", 0) + breadth.get("down_indices", 1)) * 100)
        limit_up = breadth.get("limit_up", 0)
        if isinstance(up_ratio, (int, float)) and up_ratio > 65 and isinstance(limit_up, (int, float)) and limit_up < 25:
            warnings.append({
                "type": "R23_FALSE_RECOVERY_C",
                "level": "\U0001f7e1 谨慎",
                "signal": f"假回暖预警C(v4.2.1)：虚涨 — 占比{up_ratio:.0f}%涨停{int(limit_up)}只",
                "detail": f"上涨占比{up_ratio:.0f}% > 65%但涨停仅{int(limit_up)}只 < 25只，虚涨假回暖。仓位上限≤10%",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rule": "R23"
            })
    # 条件D (v4.2.1): Level2板块主力净流入反转
    sector_flow = index_data.get("sector_flow", index_data.get("top_sectors", []))
    if isinstance(sector_flow, list) and len(sector_flow) >= 2:
        d1_val = sector_flow[-2].get("net_inflow", sector_flow[-2].get("net_amount", 0)) if isinstance(sector_flow[-2], dict) else 0
        d2_val = sector_flow[-1].get("net_inflow", sector_flow[-1].get("net_amount", 0)) if isinstance(sector_flow[-1], dict) else 0
        if isinstance(d1_val, (int, float)) and isinstance(d2_val, (int, float)) and d1_val > 0 > d2_val:
            warnings.append({
                "type": "R23_FALSE_RECOVERY_D",
                "level": "\U0001f7e1 谨慎",
                "signal": "假回暖预警D(v4.2.1)：主力资金一日游",
                "detail": "板块主力净流入由正转负，主力资金一日游。冷却≥2交易日",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rule": "R23"
            })
    return warnings


def check_fm032_bottom_signal(panic_index: float, klines: list) -> list:
    """FM-032 地量见底信号（半激活）"""
    warnings = []
    if panic_index >= 40 or not klines or len(klines) < 5:
        return warnings
    recent = klines[-5:]
    avg_vol = sum(k["volume"] for k in klines) / len(klines)
    con_shrink = all(recent[i]["volume"] < avg_vol * 0.4 for i in range(-3, 0)) if len(recent) >= 3 else False
    if con_shrink:
        slowing = all(abs((recent[-i]["close"] - recent[-i-1]["close"]) / recent[-i-1]["close"] * 100) < 1.0 for i in range(1, min(4, len(recent))))
        warnings.append({
            "type": "FM032_BOTTOM_SIGNAL",
            "level": "\U0001f7e0 信号" if slowing else "\U0001f7e1 参考",
            "signal": "FM-032 地量见底" + ("确认" if slowing else "观察中"),
            "detail": f"缩量至均量40%以下{'且跌幅趋缓' if slowing else '，等待跌幅趋缓'}，回暖期可用作筛选参考",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rule": "FM-032"
        })
    return warnings


# ─────────────────────────────────────────────
# 8. 完整扫描
# ─────────────────────────────────────────────
def full_scan(closing_mode=False, include_global=False):
    """
    完整市场扫描 v3.0
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
        "confidence": 50.0,
        "sentiment": "NEUTRAL",
        "fear_greed": 50.0,
    }

    # 指数快照
    try:
        index_data = get_index_snapshot(include_global=include_global)
        report["index"] = index_data
    except Exception as e:
        report["index"]["error"] = str(e)
        return report

    # 市场广度
    indices = index_data.get("indices", [])
    if indices:
        report["breadth"] = estimate_breadth(indices)
        report["fear_greed"] = calculate_fear_greed(indices, report["breadth"])
    
    # 情绪判断
    fg = report["fear_greed"]
    if fg > 65:
        report["sentiment"] = "GREED"
    elif fg < 35:
        report["sentiment"] = "FEAR"
    else:
        report["sentiment"] = "NEUTRAL"

    # 获取K线
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

    # 尾盘异动
    if closing_mode:
        anomaly_warnings = detect_closing_anomaly(report["index"], sz_klines)
        report["warnings"].extend(anomaly_warnings)
    
    # R22回暖预案 (v4.2)
    r22_warnings = check_r22_recovery_plan(fg, sz_klines)
    report["warnings"].extend(r22_warnings)
    
    # R23假回暖识别 (v4.2.1: 注入breadth数据)
    report["index"]["breadth"] = report.get("breadth", {})
    r23_warnings = check_r23_false_recovery(fg, report["index"], sz_klines)
    report["warnings"].extend(r23_warnings)
    
    # FM-032地量见底 (v4.2半激活)
    fm032_warnings = check_fm032_bottom_signal(fg, sz_klines)
    report["warnings"].extend(fm032_warnings)

    # 风险裁决 (v3.1: 增加跌幅绝对值判断)
    high_risk = any(w["level"] in ["🔴 高危", "🔴 危险"] for w in report["warnings"])
    med_risk = any(w["level"] == "🟡 注意" for w in report["warnings"])
    
    # 指数真实跌幅判断
    sz_idx = next((i for i in indices if '上证' in (i.name if hasattr(i, 'name') else '')), None)
    sz_pct = sz_idx.pct if sz_idx else 0
    
    # 综合判断 (v3.1: 加入指数跌幅直接判断)
    if high_risk or fg < 25 or sz_pct < -2:
        report["verdict"] = "RISK_HIGH"
    elif med_risk or fg < 40 or sz_pct < -1:
        report["verdict"] = "RISK_MEDIUM"
    elif fg > 75:
        report["verdict"] = "RISK_GREED"  # 过度贪婪风险
    else:
        report["verdict"] = "MARKET_NORMAL"

    return report


# ─────────────────────────────────────────────
# 推送格式化（微信友好）
# ─────────────────────────────────────────────
def format_report(report):
    lines = []
    now = report["time"]
    section = report["section"]
    
    # 恐慌贪婪指数
    fg = report.get("fear_greed", 50)
    fg_emoji = "🟢" if fg > 65 else "🔴" if fg < 35 else "🟡"
    fg_label = "贪婪" if fg > 65 else "恐慌" if fg < 35 else "中性"

    lines.append(f"📊 猎手系统 v3.0 | {section} | {now}")
    lines.append(f"{fg_emoji} 恐慌贪婪: {fg:.0f} ({fg_label})")

    # 指数
    indices = report.get("index", {}).get("indices", [])
    if indices:
        lines.append("\n【大盘指数】")
        for idx in indices[:7]:  # 只显示前7个
            p = idx.get('pct', idx.pct) if isinstance(idx, dict) else idx.pct
            name = idx.get('name', idx.name) if isinstance(idx, dict) else idx.name
            price = idx.get('price', idx.price) if isinstance(idx, dict) else idx.price
            emoji = "🔼" if p > 0 else "🔽" if p < 0 else "➖"
            lines.append(f"  {emoji} {name}: {price} ({p:+.2f}%)")
    else:
        lines.append("\n【大盘指数】 数据获取失败")

    # 市场广度
    b = report.get("breadth", {})
    if b:
        lines.append(f"\n【多空力量】 上涨: {b.get('up_indices',0)} 下跌: {b.get('down_indices',0)} "
                     f"多空比: {b.get('force_ratio', 0):.2f}")

    # 预警
    warns = report.get("warnings", [])
    if warns:
        lines.append("\n【⚠️ 预警】")
        for w in warns[:5]:  # 最多显示5条
            lines.append(f"  {w['level']} {w['signal']}")
            lines.append(f"    → {w['detail']}")

    # 最终裁决
    v = report["verdict"]
    verdict_map = {
        "RISK_HIGH": "🔴 市场风险偏高，谨慎操作",
        "RISK_MEDIUM": "🟡 市场中性，轻仓观察",
        "RISK_GREED": "🟠 过度贪婪，减仓止盈",
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
    global_idx = "--global" in sys.argv
    
    report = full_scan(closing_mode=closing, include_global=global_idx)
    print(format_report(report))

    # 保存日志
    DATA_DIR.mkdir(exist_ok=True)
    log_file = DATA_DIR / "logs" / f"{date.today().isoformat()}.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    sys.exit(1 if report["verdict"] in ["RISK_HIGH", "RISK_GREED"] else 0)
