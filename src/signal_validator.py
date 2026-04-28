#!/root/mem0_venv/bin/python3
"""
猎手信号校验器 - 买入前强制检查清单 v2.0
基于MEMORY.md实战教训：
- 航天电子教训：追涨停板+主力出货 → 必须查主力流向
- 买入位置检查：不在高位追
- 事件催化时机：事件当天不追
"""

import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

# ── HTTP工具 ──
def http_get_gbk(url, referer="https://finance.qq.com"):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.read().decode("gbk", errors="replace")
    except Exception:
        return None

def http_get_utf8(url, referer="https://finance.eastmoney.com"):
    try:
        req = urllib.request.Request(url, headers={
            "Referer": referer,
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None

def get_tencent_quote(code):
    """获取腾讯实时行情"""
    prefix = "sz" if code.startswith(("00", "30")) else "sh"
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    raw = http_get_gbk(url)
    if not raw:
        return None
    try:
        m = re.search(r'v_[a-z0-9]+="([^"]*)"', raw)
        if not m:
            return None
        parts = m.group(1).split("~")
        if len(parts) < 10:
            return None
        return {
            "name": parts[1],
            "price": float(parts[3]) if parts[3] else 0,
            "prev_close": float(parts[4]) if parts[4] else 0,
            "open": float(parts[5]) if parts[5] else 0,
            "high": float(parts[33]) if parts[33] else 0,
            "low": float(parts[34]) if parts[34] else 0,
            "volume": int(parts[6]) if parts[6] else 0,  # 手
            "buy1": float(parts[9]) if parts[9] else 0,
            "sell1": float(parts[19]) if parts[19] else 0,
            "time": f"{parts[30]} {parts[31]}" if len(parts) > 31 else "",
        }
    except Exception:
        return None

def get_main_money_flow_tencent(code):
    """腾讯财经-主力资金流向（单只）"""
    url = f"https://qt.gtimg.cn/q=mx_{code}"
    raw = http_get_gbk(url)
    if not raw:
        return None
    try:
        # 格式: var mx_600961="1~的主力净流入~...~"
        m = re.search(r'"([^"]*)"', raw)
        if not m:
            return None
        parts = m.group(1).split("~")
        if len(parts) < 15:
            return None
        main_inflow = float(parts[8]) if parts[8] else 0  # 万元，正=流入，负=流出
        retail_inflow = float(parts[9]) if parts[9] else 0
        return {
            "main_inflow_wan": main_inflow,   # 万元
            "retail_inflow_wan": retail_inflow,
            "main_inflow_yi": round(main_inflow / 10000, 2),  # 亿元
        }
    except Exception:
        return None

def get_main_money_flow_eastmoney(code):
    """东方财富-主力资金流向（更准确）"""
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"
    url = (f"https://push2.eastmoney.com/api/qt/stock/get?fltt=2&invt=2&ut="
           f"b2884a393a59ad64002292a3e90d46a&fields=f62,f184,f66,f69,f72,f75,f78,f81,f84,f87&secid={secid}")
    raw = http_get_utf8(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        fields = data.get("data", {})
        main_net = fields.get("f62", 0) or 0   # 主力净流入（元）
        main_net_yi = round(main_net / 100000000, 2)  # 亿元
        return {
            "main_inflow_yi": main_net_yi,
            "main_inflow_wan": main_net / 10000,
        }
    except Exception:
        return None

def get_kline_data(code, days=5):
    """获取日K线数据（腾讯财经）"""
    prefix = "sz" if code.startswith(("00", "30")) else "sh"
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayhfq"
           f"&param={prefix}{code},day,,,{days},qfq")
    raw = http_get_utf8(url, referer="https://finance.qq.com")
    if not raw:
        return []
    try:
        m = re.search(r'kline_dayhfq=({.*})', raw)
        if not m:
            return []
        json_data = json.loads(m.group(1))
        symbol_key = f"{prefix}{code}"
        bars = json_data.get("data", {}).get(symbol_key, {})
        klines = bars.get("qfqday", bars.get("day", []))
        return klines  # [date, open, close, high, low, vol]
    except Exception:
        return []

def check_buy_signal(code, name=None, price=None):
    """
    买入前强制检查清单
    返回: {
        "pass": bool,          # 是否通过所有检查
        "checks": [...],      # 每项检查结果
        "score": int,         # 综合评分 0-100
        "verdict": str,       # 最终结论
        "warnings": [...],    # 警告信息
    }
    """
    checks = []
    warnings = []
    score = 100
    score_deduct = 0

    q = get_tencent_quote(code)
    if not q or q["price"] <= 0:
        return {
            "pass": False,
            "checks": [{"name": "行情获取", "result": "FAIL", "detail": "无法获取实时行情"}],
            "score": 0,
            "verdict": "无法获取行情，跳过",
            "warnings": ["行情接口失败"],
        }

    current_price = price or q["price"]
    prev_close = q["prev_close"]
    today_open = q["open"]
    high = q["high"]
    low = q["low"]
    day_chg_pct = (current_price / prev_close - 1) * 100 if prev_close > 0 else 0

    # ── 检查1：涨停板检查 ──
    # 前一日涨幅>9%视为涨停
    klines = get_kline_data(code, days=5)
    prev_chg_pct = 0
    if len(klines) >= 2:
        try:
            prev_close_kl = float(klines[-2][1])
            prev_price_kl = float(klines[-2][2])
            if prev_close_kl > 0:
                prev_chg_pct = (prev_price_kl / prev_close_kl - 1) * 100
        except Exception:
            pass

    if prev_chg_pct >= 9:
        checks.append({
            "name": "涨停板检查",
            "result": "FAIL",
            "detail": f"前一日涨停(+{prev_chg_pct:.1f}%)，今日不追"
        })
        score_deduct += 40
        warnings.append(f"前一日涨停板，今日不追高")
    elif day_chg_pct >= 5:
        checks.append({
            "name": "涨幅检查",
            "result": "WARN",
            "detail": f"今日涨幅+{day_chg_pct:.2f}%，偏高，注意回调"
        })
        score_deduct += 15
    else:
        checks.append({
            "name": "涨幅检查",
            "result": "PASS",
            "detail": f"今日涨幅{day_chg_pct:+.2f}%，正常范围"
        })

    # ── 检查2：买入位置检查 ──
    # 当前价 vs 当日均价 vs 最高价
    day_avg = (high + low + current_price) / 3 if high > 0 else current_price
    if high > 0 and current_price > high * 0.99:
        checks.append({
            "name": "买入位置",
            "result": "FAIL",
            "detail": f"现价{current_price}接近今日最高{high}，高位追入"
        })
        score_deduct += 30
        warnings.append("价格在高位，不建议追入")
    elif current_price > day_avg * 1.02:
        checks.append({
            "name": "买入位置",
            "result": "WARN",
            "detail": f"现价>{均价}{day_avg:.2f}，偏高"
        })
        score_deduct += 10
    else:
        checks.append({
            "name": "买入位置",
            "result": "PASS",
            "detail": f"价格{current_price:.2f}在合理区间(均价{day_avg:.2f})"
        })

    # ── 检查3：主力资金流向 ──
    mf = get_main_money_flow_eastmoney(code)
    if mf is None:
        mf = get_main_money_flow_tencent(code)

    if mf:
        main_yi = mf.get("main_inflow_yi", 0)
        if main_yi < -1:
            checks.append({
                "name": "主力资金",
                "result": "FAIL",
                "detail": f"主力净流出{main_yi:.2f}亿 (>1亿)，主力在出货！"
            })
            score_deduct += 35
            warnings.append(f"⚠️ 主力净流出{main_yi:.2f}亿，禁止买入！")
        elif main_yi < 0:
            checks.append({
                "name": "主力资金",
                "result": "WARN",
                "detail": f"主力净流出{-main_yi:.2f}亿，轻微流出"
            })
            score_deduct += 10
        else:
            checks.append({
                "name": "主力资金",
                "result": "PASS",
                "detail": f"主力净流入{main_yi:.2f}亿，{'积极' if main_yi > 1 else '少量'}流入"
            })
    else:
        checks.append({
            "name": "主力资金",
            "result": "WARN",
            "detail": "无法获取资金流向数据，跳过此项"
        })
        score_deduct += 5

    # ── 检查4：量价配合 ──
    if len(klines) >= 3:
        try:
            vol_today = float(klines[-1][5]) if klines[-1][5] else 0
            vol_avg = sum(float(k[5] or 0) for k in klines[-4:-1]) / 3
            if vol_today > 0:
                vol_ratio = vol_today / vol_avg if vol_avg > 0 else 0
                if vol_ratio < 0.5:
                    checks.append({
                        "name": "量价配合",
                        "result": "WARN",
                        "detail": f"今日缩量(量比{vol_ratio:.2f})，观望"
                    })
                    score_deduct += 5
                elif vol_ratio > 2:
                    checks.append({
                        "name": "量价配合",
                        "result": "PASS",
                        "detail": f"今日放量(量比{vol_ratio:.1f}x)，资金活跃"
                    })
                else:
                    checks.append({
                        "name": "量价配合",
                        "result": "PASS",
                        "detail": f"量比{vol_ratio:.2f}，正常"
                    })
            else:
                checks.append({
                    "name": "量价配合",
                    "result": "WARN",
                    "detail": "成交量数据异常"
                })
        except Exception:
            pass

    # ── 综合评分 ──
    score = max(0, score - score_deduct)

    # ── 最终结论 ──
    if score >= 80 and not any(c["result"] == "FAIL" for c in checks):
        verdict = f"✅ 通过检查（评分{score}/100）"
        is_pass = True
    elif score >= 50 and not any(c["result"] == "FAIL" for c in checks):
        verdict = f"⚠️ 谨慎通过（评分{score}/100），注意风险"
        is_pass = True
    else:
        verdict = f"❌ 不通过（评分{score}/100），{warnings[0] if warnings else '不符合买入条件'}"
        is_pass = False

    return {
        "pass": is_pass,
        "checks": checks,
        "score": score,
        "verdict": verdict,
        "warnings": warnings,
        "quote": q,
        "money_flow": mf,
        "klines": klines,
    }

def format_check_report(code, result):
    """格式化检查报告为易读字符串"""
    lines = []
    lines.append(f"\n🔍 【买入信号校验】{result.get('quote', {}).get('name', code)}({code})")
    lines.append(f"   评分：{result['score']}/100 | {result['verdict']}")
    for c in result["checks"]:
        icon = "✅" if c["result"] == "PASS" else ("⚠️" if c["result"] == "WARN" else "❌")
        lines.append(f"  {icon} {c['name']}：{c['detail']}")
    if result["warnings"]:
        lines.append(f"\n  警告：{' | '.join(result['warnings'])}")
    return "\n".join(lines)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 signal_validator.py <股票代码>")
        exit(1)
    code = sys.argv[1]
    result = check_buy_signal(code)
    print(format_check_report(code, result))
    print(f"\n结论: {'通过' if result['pass'] else '不通过'}")
