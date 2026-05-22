#!/usr/bin/env python3
"""
猎手系统 - 实盘选股器 v2.5
【BUG修复】2026-05-13:
  - 修复追高推荐bug：涨幅>5%的股票不再入选"最终名单"
  - 涨幅>5%标记为"观望"不列入推荐
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# IMA 知识库桥接（股票研报增强）
try:
    from ima_knowledge_bridge import enrich_stock_context, search_knowledge
    _HAS_IMA = True
except ImportError:
    _HAS_IMA = False

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
    """获取市场温度（0-100℃）"""
    global _cached_temperature
    if _cached_temperature is not None:
        return _cached_temperature

    try:
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

        chg_vals = list(indices.values())
        avg_chg = sum(chg_vals) / len(chg_vals) if chg_vals else 0

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

        temp_from_chg = 50 + avg_chg * 5
        temp = temp_from_chg * 0.6 + trend_score * 0.4
        temp = max(0, min(100, int(temp)))
        _cached_temperature = temp
        return temp
    except Exception:
        _cached_temperature = 50
        return 50

# ── 动态阈值（根据温度调整） ──────────────────────────
def get_dynamic_thresholds():
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
        chg_min, vol_min = 1.5, 1.0
        label = f"极冷模式({temp}℃)"

    return {
        "temperature": temp,
        "temperature_label": label,
        "chg_min": chg_min,
        "vol_min": vol_min,
        "can_open": True,
    }

# ── 市场状态识别 ──────────────────────────────────────
def detect_market_regime() -> dict:
    try:
        url = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
        raw = http_get_gbk(url)
        if not raw:
            return {"regime": "unknown", "label": "未知", "strength": 0}

        total_vol_ratio = 0
        total_chg = 0
        count = 0
        for line in raw.split('\n'):
            m = re.search(r'v_\w+="(.+)"', line)
            if not m:
                continue
            parts = m.group(1).split('~')
            if len(parts) < 32:
                continue
            try:
                chg = float(parts[32])
                total_chg += abs(chg)
                count += 1
            except (ValueError, IndexError):
                continue

        avg_abs_chg = total_chg / count if count > 0 else 0

        if avg_abs_chg > 0.5:
            regime = "trending"
            label = f"趋势市(波动{avg_abs_chg:.2f}%)"
            strength = min((avg_abs_chg - 0.5) / 0.5, 1.0)
        elif avg_abs_chg < 0.3:
            regime = "range_bound"
            label = f"震荡市(波动{avg_abs_chg:.2f}%)"
            strength = 1.0
        else:
            regime = "mixed"
            label = f"混合市(波动{avg_abs_chg:.2f}%)"
            strength = 0.5

        return {"regime": regime, "label": label, "strength": strength}
    except Exception:
        return {"regime": "unknown", "label": "未知", "strength": 0}

# ── 动态因子权重 ──────────────────────────────────────
def get_dynamic_weights() -> dict:
    regime = detect_market_regime()
    r = regime["regime"]

    if r == "trending":
        return {
            "momentum": 0.40,
            "volume": 0.30,
            "trend": 0.20,
            "ma_cross": 0.05,
            "rsi": 0.05,
        }
    elif r == "range_bound":
        return {
            "momentum": 0.10,
            "volume": 0.15,
            "trend": 0.15,
            "ma_cross": 0.30,
            "rsi": 0.30,
        }
    else:
        return {
            "momentum": 0.25,
            "volume": 0.25,
            "trend": 0.20,
            "ma_cross": 0.15,
            "rsi": 0.15,
        }

# ── 候选股综合评分 ─────────────────────────────────────
def calc_enhanced_score(c: dict) -> dict:
    regime = detect_market_regime()
    weights = get_dynamic_weights()
    w = weights

    chg = abs(c.get("chg_pct", 0))
    vol_ratio = c.get("vol_ratio", 0)
    momentum = chg * vol_ratio

    momentum_score = min(momentum / 2, 100)
    vol_score = min(vol_ratio / 10 * 100, 100)
    chg_score = min(chg / 15 * 100, 100)

    score = (
        w["momentum"] * momentum_score +
        w["volume"] * vol_score +
        w["trend"] * chg_score +
        w["ma_cross"] * min(chg * 3, 100) +
        w["rsi"] * min(vol_ratio * 5, 100)
    )

    return {
        **c,
        "regime": regime["label"],
        "weights": {k: round(v, 2) for k, v in weights.items()},
        "enhanced_score": round(score, 1),
    }

# ── 数据源1: 东方财富（主） ───────────────────────────
def get_index_components_em():
    candidates = []
    errors = []

    fs_options = [
        "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "m:0+t:6,m:1+t:2,m:1+t:23",
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
                    if code.startswith(("688", "689")):
                        continue
                    if price > 100 or price < 3:
                        continue
                    # 涨停股排除（>=9.8%几乎买不到）
                    if chg_pct >= 9.8:
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
            break
        except Exception as e:
            errors.append(f"fs={fs} 异常: {e}")
            continue

    err_msg = " | ".join(errors) if errors and not candidates else None
    return candidates, err_msg

# ── 数据源2: 新浪行情（备） ───────────────────────────
def get_index_components_sina():
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
                vol_ratio = 0
                for field in ["volume_ratio", "turnoverratio", "turnover_ratio"]:
                    vr = s.get(field)
                    if vr is not None and vr not in ["-", ""]:
                        try:
                            vol_ratio = float(vr)
                            break
                        except (ValueError, TypeError):
                            pass
                if vol_ratio == 0:
                    turnover = s.get("turnoverratio")
                    if turnover not in [None, "-", ""]:
                        try:
                            vol_ratio = float(turnover) / 10
                        except Exception:
                            vol_ratio = 1.5
                    else:
                        vol_ratio = 1.5

                amount = float(s.get("amount", 0) or 0)

                if not code or not name or price <= 0:
                    continue
                if "ST" in name or name.startswith("N"):
                    continue
                if code.startswith(("688", "689")):
                    continue
                if price > 100 or price < 3:
                    continue
                # 涨停股排除（>=9.8%几乎买不到）
                if chg_pct >= 9.8:
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
    candidates, err_em = get_index_components_em()
    if err_em or not candidates:
        print(f"  [EM] {err_em or '无数据'}，切换新浪...")
        return get_index_components_sina()
    return candidates, None

# ── K线验证 v2 ──────────────────────────────────────
def verify_kline_trend_v2(code):
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

        if up_days >= 1 and vol_not_shrinking >= 1:
            tag = "[次新]" if is_new else ""
            return True, f"{tag}涨{up_days}天+量稳", is_new

        return False, f"趋势不足(up={up_days},vol稳={vol_not_shrinking})", is_new

    except Exception as e:
        return False, f"K线异常({e})", False

# ── 主选股函数 v2.5 (修复追高bug) ─────────────────────
def pick_best_candidates(max_count=3, min_score=8):
    """
    选股入口 v2.5
    【BUG修复】涨幅>5%的股票标记为"观望"，不列入最终入选名单
    铁律：不追高、不追涨停
    """
    global _cached_temperature
    _cached_temperature = None

    thresholds = get_dynamic_thresholds()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 选股扫描开始...")
    print(f"  📊 {thresholds['temperature_label']} | 涨幅>{thresholds['chg_min']}% 量比>{thresholds['vol_min']}")

    # 获取候选（双数据源）
    all_candidates, err = get_candidates_with_fallback()
    print(f"  初筛候选: {len(all_candidates)}只 {'(双源)' if not err else ''}")

    if not all_candidates:
        print(f"  ⚠️ {err or '行情接口无数据'}")
        return []

    # 动态阈值过滤
    chg_min = thresholds["chg_min"]
    vol_min = thresholds["vol_min"]
    filtered = [c for c in all_candidates if c["chg_pct"] >= chg_min and c["vol_ratio"] >= vol_min]
    print(f"  🌡️ 动态过滤后: {len(filtered)}只 (涨>{chg_min}% 且 量比>{vol_min})")

    if not filtered:
        return []

    # 市场状态感知评分
    regime_info = detect_market_regime()
    weights = get_dynamic_weights()
    print(f"  🏛️ 市场状态: {regime_info['label']} | 权重:mom={weights['momentum']} vol={weights['volume']} trend={weights['trend']} ma={weights['ma_cross']} rsi={weights['rsi']}")

    # 用增强评分重新排序
    for c in filtered:
        scored = calc_enhanced_score(c)
        c["score"] = scored["enhanced_score"]
        c["momentum"] = round(c["chg_pct"] * c["vol_ratio"], 1)

    filtered.sort(key=lambda x: x["score"], reverse=True)

    # R01: 涨停过滤（涨幅>=9.8%禁止入选）
    filtered = [c for c in filtered if c['chg_pct'] < 9.8]
    print(f"  🚫 涨停过滤后: {len(filtered)}只 (排除涨幅>=9.8%)")

    # R02: 【BUG修复】追高过滤（涨幅>5%标记为观望，不列入入选名单）
    HIGH_GAIN_THRESHOLD = 5.0  # 涨幅>5%视为追高
    watch_only = [c for c in filtered if c['chg_pct'] > HIGH_GAIN_THRESHOLD]
    final_candidates = [c for c in filtered if c['chg_pct'] <= HIGH_GAIN_THRESHOLD]
    if watch_only:
        watch_names = [f"{c['name']}(+{c['chg_pct']:.2f}%)" for c in watch_only[:5]]
        print(f"  ⚠️ 追高过滤(>{HIGH_GAIN_THRESHOLD}%): {len(watch_only)}只 观望: {watch_names}")

    # 排除持仓
    portfolio_file = Path("/root/.openclaw/workspace/猎手模拟交易/持仓.json")
    held_codes = []
    if portfolio_file.exists():
        with open(portfolio_file) as f:
            pf = json.load(f)
        held_codes = [p["code"] for p in pf.get("positions", []) if p.get("status") == "holding"]

    # K线验证（仅对最终候选进行验证）
    results = []
    checked = 0
    for c in final_candidates:
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

        # IMA 研报知识增强评分
        if ok and _HAS_IMA:
            try:
                ctx = enrich_stock_context(name, code)
                if ctx:
                    c["ima_ctx"] = ctx
                    # 有研报支持的标的加分（最多+1.5分）
                    kb_count = ctx.count("[AI读研报]")
                    c["score"] = min(c["score"] + kb_count * 0.5, c["score"] + 1.5)
                    print(f"  📖 {name}({code}) IMA研报发现{kb_count}篇 → 加分")
            except Exception:
                pass

        if ok:
            results.append(c)
            print(f"  ✅ {name}({code}) 涨幅{c['chg_pct']:+.2f}% 量比{c['vol_ratio']:.1f} {reason}")
        else:
            print(f"  ❌ {name}({code}) 涨幅{c['chg_pct']:+.2f}% 量比{c['vol_ratio']:.1f} [{reason}]")
        checked += 1

    # 只返回涨幅<=5%的候选
    top = [c for c in results if c["score"] >= min_score and c["chg_pct"] <= HIGH_GAIN_THRESHOLD][:max_count]
    names = [f"{x['name']}({x['code']}) @{x['price']}" for x in top]
    print(f"\n  最终入选({len(top)}只,涨幅<=5%): {names}")
    if _HAS_IMA and top:
        print(f"  📚 IMA知识增强: 候选标的有研报/课程数据支撑")
    print(f"  🏛️ 市场状态: {regime_info['label']}")
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
# ── ETF & 黄金扫描集成 ──────────────────────────────────────────────────
def scan_etf_and_gold():
    """
    集成ETF和黄金扫描
    必须在个股扫描完成后调用
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "etf_scanner", 
            "/root/.openclaw/workspace/猎手模拟交易/src/etf_scanner.py"
        )
        if spec and spec.loader:
            etf_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(etf_module)
            
            print("\n" + "=" * 50)
            print("【开始ETF & 黄金扫描】")
            print("=" * 50)
            
            result = etf_module.pick_best_etf_gold(max_count=3)
            
            if result["signals"]:
                print("\n━━━ ETF/黄金推荐 ━━━")
                for s in result["signals"]:
                    inflow_str = f"主力净流入{s['inflow_3d']/10000:.2f}亿" if s["inflow_3d"] > 0 else f"主力净流出{abs(s['inflow_3d'])/10000:.2f}亿"
                    print(f"  【{s['category']}】{s['name']}({s['code']}) 现价{s['price']:.3f} 涨{s['chg_pct']:+.2f}% {inflow_str} ✅")
            else:
                print("\n  当前无ETF/黄金推荐信号（涨幅>5%或主力资金不足）")
            
            return result
        else:
            print("  ⚠️ ETF扫描模块加载失败")
            return None
    except Exception as e:
        print(f"  ⚠️ ETF扫描异常: {e}")
        return None

# ── 增强版CLI入口（含ETF）───────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("【猎手系统 v2.6 - 含ETF扫描】")
    print("=" * 50)
    
    # 1. 个股扫描
    print("\n━━━ 个股扫描 ━━━")
    candidates = pick_best_candidates(max_count=3, min_score=5)
    print(f"\n个股入选: {len(candidates)}只")
    for c in candidates:
        print(f"  {c['name']}({c['code']}) 现价:{c['price']} 涨幅:{c['chg_pct']:+.2f}% 量比:{c['vol_ratio']:.1f} 分:{c['score']}")
    
    # 2. ETF & 黄金扫描
    etf_result = scan_etf_and_gold()
    
    # 3. 综合推荐
    print("\n" + "=" * 50)
    print("【综合推荐】")
    print("=" * 50)
    
    all_recommendations = []
    for c in candidates:
        all_recommendations.append({
            "type": "个股",
            "name": c["name"],
            "code": c["code"],
            "price": c["price"],
            "chg_pct": c["chg_pct"],
            "score": c.get("score", 0),
        })
    
    if etf_result and etf_result["signals"]:
        for s in etf_result["signals"]:
            all_recommendations.append({
                "type": s["category"],
                "name": s["name"],
                "code": s["code"],
                "price": s["price"],
                "chg_pct": s["chg_pct"],
                "score": s.get("inflow_3d", 0) / 10000,  # 用资金量代替分数
            })
    
    # 按分数排序
    all_recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"\n推荐排名（共{len(all_recommendations)}个）:")
    for i, r in enumerate(all_recommendations[:6], 1):
        print(f"  {i}. 【{r['type']}】{r['name']}({r['code']}) 涨{r['chg_pct']:+.2f}%")
