#!/usr/bin/env python3
"""
猎手系统 - 复盘脚本
用法: python3 review.py [日期]  # 不传参默认昨天
"""
import json
import sys
import re
from datetime import datetime, date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
REVIEW_DIR = DATA_DIR / "reviews"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────
def http_get(url, headers=None, timeout=5):
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
            return resp.read().decode("gbk", errors="replace")
    except Exception:
        return None


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pct(v):
    return f"{v:+.2f}%" if v is not None else "N/A"


# ─────────────────────────────────────────────
# 获取昨日收盘数据
# ─────────────────────────────────────────────
def get_actual_data(target_date_str):
    """
    获取指定日期的收盘数据
    返回: dict { sh000001: {...}, ... }
    """
    result = {}
    # 腾讯接口代码格式: sh=上交所 sz=深交所
    codes_map = {
        "000001": ("sh", "上证指数"),
        "399001": ("sz", "深证成指"),
        "399006": ("sz", "创业板指"),
        "000300": ("sh", "沪深300"),
        "000016": ("sh", "上证50"),
        "399905": ("sz", "科创50"),
    }
    # URL需要 sh/sz 前缀
    codes_url = ",".join(p + c for c, (p, _) in codes_map.items())
    url = f"https://qt.gtimg.cn/q={codes_url}"
    raw = http_get(url)
    if not raw:
        return result

    for line in raw.strip().split("\n"):
        m = re.match(r'v_\w+="(.+)"', line)
        if not m:
            continue
        parts = m.group(1).split("~")
        if len(parts) < 35:
            continue
        code_raw = parts[2]
        info = codes_map.get(code_raw)
        if not info:
            continue
        prefix, name = info
        try:
            price = float(parts[3])
            prev_close = float(parts[4])
            pct_val = round((price - prev_close) / prev_close * 100, 2)
            result[code_raw] = {
                "name": name,
                "close": price,
                "prev_close": prev_close,
                "pct": pct_val,
                "high": float(parts[33]) if parts[33] else None,
                "low": float(parts[34]) if parts[34] else None,
                "date": target_date_str,
            }
        except (ValueError, IndexError):
            continue
    return result


# ─────────────────────────────────────────────
# 加载昨日扫描日志
# ─────────────────────────────────────────────
def get_scan_log(target_date):
    log_file = LOG_DIR / f"{target_date.isoformat()}.json"
    if log_file.exists():
        return load_json(log_file)
    return None


# ─────────────────────────────────────────────
# 核心复盘逻辑
# ─────────────────────────────────────────────
def run_review(target_date):
    target_str = target_date.isoformat()
    review_file = REVIEW_DIR / f"{target_str}.json"

    print(f"\n{'='*50}")
    print(f"  猎手系统 · 复盘  {target_str}")
    print(f"{'='*50}")

    # 1. 获取昨日收盘数据（今日数据中包含昨收价，即为昨日收盘数据）
    print("\n📥 获取收盘数据...")
    actual = get_actual_data(target_str)

    if not actual:
        print("⚠️ 收盘数据获取失败，跳过详细复盘")
        actual = {}

    # 2. 加载昨日扫描日志
    print("📂 加载昨日扫描日志...")
    scan_log = get_scan_log(target_date)

    # 3. 构建复盘记录
    review = {
        "date": target_str,
        "weekday": ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][target_date.weekday()],
        "market": {
            "indices": {},
            "verdict": "",
            "warnings": [],
        },
        "scanLog": scan_log,
        "actual": actual,
        "comparisons": [],
        "warningsAccuracy": {"total": 0, "valid": 0, "match": 0},
        "summary": "",
        "nextDayFocus": [],
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 4. 对比预测 vs 实际
    if actual and scan_log:
        indices_pred = scan_log.get("index", {}).get("indices", [])
        verdict = scan_log.get("verdict", "")

        verdict_map = {
            "RISK_HIGH": "偏空",
            "RISK_MEDIUM": "中性",
            "MARKET_NORMAL": "偏多",
        }

        # 指数对比
        for idx_pred in indices_pred:
            code = idx_pred.get("code", "")
            actual_idx = actual.get(code)
            if actual_idx:
                pred_pct = idx_pred.get("pct", 0)
                actual_pct = actual_idx.get("pct", 0)
                diff = actual_pct - pred_pct
                direction_correct = (pred_pct > 0) == (actual_pct > 0) or abs(actual_pct) < 0.3

                review["comparisons"].append({
                    "name": idx_pred.get("name", ""),
                    "code": code,
                    "predicted_pct": pred_pct,
                    "actual_pct": actual_pct,
                    "diff": round(diff, 2),
                    "direction_correct": direction_correct,
                    "accuracy": "✅ 方向正确" if direction_correct else "❌ 方向错误",
                })

        # 预警准确率
        warnings = scan_log.get("warnings", [])
        review["warningsAccuracy"]["total"] = len(warnings)
        for w in warnings:
            level = w.get("level", "")
            w_type = w.get("type", "")
            # 简化判断：只要有预警标记就算"有效预警"
            if level in ["🔴 高危", "🔴 危险", "🟡 注意"]:
                review["warningsAccuracy"]["valid"] += 1

        # 根据对比计算预警命中
        for comp in review["comparisons"]:
            if not comp["direction_correct"] and review["warningsAccuracy"]["valid"] > 0:
                review["warningsAccuracy"]["match"] += 1

    # 5. 生成综合评分（简单逻辑）
    score = 0
    total_checks = len(review["comparisons"]) + review["warningsAccuracy"]["valid"]
    if total_checks > 0:
        correct_dir = sum(1 for c in review["comparisons"] if c["direction_correct"])
        score = round((correct_dir + review["warningsAccuracy"]["match"]) / total_checks * 100)

    review["score"] = score

    # 6. 保存复盘记录
    save_json(review_file, review)

    # ─────────────────────────────────────────────
    # 输出格式化报告
    # ─────────────────────────────────────────────
    print(f"\n📊 指数预测对比")
    print("-" * 60)
    for comp in review["comparisons"]:
        print(f"  {comp['name']}: 预测{comp['predicted_pct']:+.2f}% | "
              f"实际{comp['actual_pct']:+.2f}% | {comp['accuracy']} "
              f"(差{comp['diff']:+.2f}%)")

    if review["warningsAccuracy"]["total"] > 0:
        print(f"\n⚠️ 预警统计: 共{review['warningsAccuracy']['total']}条预警，"
              f"其中{review['warningsAccuracy']['valid']}条有效")

    print(f"\n🏆 复盘评分: {score}/100")

    # 综合判断
    if score >= 80:
        verdict_text = "🟢 优秀 · 系统判断基本准确"
    elif score >= 60:
        verdict_text = "🟡 良好 · 方向判断OK，需微调"
    elif score >= 40:
        verdict_text = "🟠 需改进 · 错误较多，需复盘逻辑优化"
    else:
        verdict_text = "🔴 不及格 · 系统预警与实际严重偏离，需重大调整"

    review["summary"] = verdict_text
    save_json(review_file, review)

    print(f"\n{'='*50}")
    print(f"  综合评定: {verdict_text}")
    print(f"{'='*50}")
    print(f"\n📝 复盘记录已保存: {review_file}")

    return review


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    else:
        target = date.today() - timedelta(days=1)

    result = run_review(target)
    sys.exit(0)
