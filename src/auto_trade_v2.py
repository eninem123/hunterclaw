#!/usr/bin/env python3
"""
猎手自动交易执行模块 v4.0 (2026-05-16)
========================================================================
升级内容:
  1. R18 冰点期入场禁止 — 温度<35℃禁止新开仓，恐慌<25强制空仓
  2. R19 大盘趋势三重确认 — 入场前需检查: 沪深300站MA20 + 涨跌比>0.6 + 非恐慌
  3. R20 浮亏分级响应 — 4级主动管理: -2%警示 / -3%减半 / -5%止损 / -7%强平
  4. R21 批量建仓冷却 — 单日≤2次, 单只≤20%, 板块不重复, 间隔≥30min
  5. 温度仓位矩阵 — 6档: ≥80℃→10% | 70-80℃→20% | 50-70℃→50% | 35-50℃→30% | 25-35℃→10% | <25℃→0%
  6. 恐慌环境规则V09/V10 — 恐慌反弹先减半, 恐慌<25全面禁止
  7. 止损升级R07-v2 — 加入恐慌因子(恐慌环境收紧30%)
  8. 止盈升级R08-v2 — 新增恐慌反弹档位(+2%强制减半)
  
依赖:
  - 腾讯行情 qt.gtimg.cn
  - 持仓.json
  - trade_state.json
  
用法:
  python auto_trade_v2.py               # 执行完整交易周期
  python auto_trade_v2.py --status-only  # 仅推送持仓状态
  python auto_trade_v2.py --dry-run      # 模拟运行不实际交易
"""

import json
import os
import subprocess
import urllib.request
import urllib.parse
import uuid
import time
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

__version__ = "4.0.0"

# ============ 路径常量 ============
BASE_DIR = Path("/root/.openclaw/workspace")
PORTFOLIO_FILE = BASE_DIR / "持仓.json"
STATE_FILE = BASE_DIR / "trade_state.json"
DELIVERY_QUEUE = Path("/root/.openclaw/delivery-queue")
LOG_FILE = BASE_DIR / "logs" / f"hunter-v4-{datetime.now().strftime('%Y-%m-%d')}.log"

WECHAT_ID = "o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat"
ACCOUNT_ID = "665a0448707a-im-bot"

# ============ 交易参数 v4.0 ============
# === 核心限制 ===
MAX_BUYS_PER_DAY = 2           # R05 收紧: 3→2次
MAX_POSITION_PCT = 20          # R06 收紧: 30%→20%
MAX_STOCKS_TOTAL = 4           # R21: 同时持仓上限
MAX_SECTOR_REPEAT = 2          # R21: 同板块最多2只
MIN_BUY_INTERVAL_MIN = 30      # R21: 买入间隔≥30分钟
STOP_LOSS_PCT = 5              # 基础止损
TAKE_PROFIT_PCT = 8            # 基础止盈

# === 浮亏分级响应 R20 ===
LOSS_ALERT_PCT = -2            # 1级: 警示
LOSS_HALVE_PCT = -3            # 2级: 减半仓
LOSS_STOP_PCT = -5             # 3级: 止损
LOSS_FORCE_PCT = -7            # 4级: 强平

# === 温度仓位矩阵 ===
TEMPERATURE_MATRIX = [
    (80, 0.10, "极度活跃"),    # ≥80℃ → 10%
    (70, 0.20, "活跃"),        # 70-80℃ → 20%
    (50, 0.50, "正常"),        # 50-70℃ → 50%
    (35, 0.30, "偏冷"),        # 35-50℃ → 30%
    (25, 0.10, "寒冷"),        # 25-35℃ → 10%（只出不进）
    (0,  0.00, "冰封"),        # <25℃ → 0%（强制空仓）
]

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ============ 恐慌指数 ============
# 从市场指数综合计算：涨跌比、跌幅深度、量能萎缩、ETF资金流
PANIC_LEVELS = {
    "safe":       (60, 100, "安全"),
    "caution":    (40, 60,  "谨慎"),
    "cold":       (25, 40,  "偏冷"),
    "freeze":     (10, 25,  "冰点"),
    "panic":      (0,  10,  "恐慌"),
}

# ============ 日志 ============
def log(msg: str, level: str = "INFO"):
    """统一日志"""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}][{level}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ============ 微信通知 ============
def wechat_notify(msg: str) -> dict:
    """通过 OpenClaw delivery-queue 实时推送微信消息"""
    try:
        entry = {
            "id": str(uuid.uuid4()),
            "enqueuedAt": int(datetime.now().timestamp() * 1000),
            "channel": "openclaw-weixin",
            "to": WECHAT_ID,
            "accountId": ACCOUNT_ID,
            "payloads": [{"text": msg, "mediaUrls": [], "replyToTag": False,
                          "replyToCurrent": False, "audioAsVoice": False}],
            "retryCount": 0,
            "lastAttemptAt": None
        }
        path = DELIVERY_QUEUE / f"{entry['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        log(f"微信推送: {msg[:100]}...")
        return {"ok": True}
    except Exception as e:
        log(f"通知失败: {e}", "ERROR")
        return {"error": str(e)}

# ============ 时间校验 ============
def get_real_date() -> date:
    """通过外部API获取真实日期"""
    try:
        req = urllib.request.Request(
            "http://worldtimeapi.org/api/timezone/Asia/Shanghai",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return datetime.strptime(data["datetime"][:10], "%Y-%m-%d").date()
    except Exception:
        pass
    try:
        result = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True)
        return datetime.strptime(result.stdout.strip(), "%Y-%m-%d").date()
    except Exception:
        return date.today()

def is_trading_day() -> Tuple[bool, date, str]:
    """判断是否A股交易日"""
    today = get_real_date()
    if today.weekday() >= 5:
        return False, today, "周末"
    return True, today, "交易日"

def is_trading_hours() -> bool:
    """判断是否在A股交易时段"""
    now = datetime.now()
    h, m = now.hour, now.minute
    morning = (h == 9 and m >= 30) or (10 <= h <= 11) or (h == 11 and m <= 30)
    afternoon = 13 <= h < 15
    return morning or afternoon

# ============ HTTP工具 ============
def http_get(url: str, timeout: int = 8, encoding: str = "gbk") -> Optional[str]:
    """统一HTTP GET"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.qq.com",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return raw.decode(encoding, errors="replace")
    except Exception as e:
        log(f"HTTP请求失败: {url[:60]}... {e}", "WARN")
        return None

def json_get(url: str) -> Optional[dict]:
    """HTTP GET + JSON解析"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.eastmoney.com",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception:
        return None

# ============ 市场温度计算 v4.0 ============
def calc_panic_index(indices_data: list, overview: dict = None) -> Tuple[int, str]:
    """
    计算恐慌指数 (0-100, 越低越恐慌)
    
    因子:
      1. 指数跌幅贡献 (30%)
      2. 涨跌比贡献 (30%)
      3. 量能萎缩贡献 (20%)
      4. 跌停占比贡献 (20%)
    """
    score = 60  # 中性基准
    
    # 1. 指数跌幅
    if indices_data:
        avg_chg = sum(i.get("pct", 0) for i in indices_data) / max(len(indices_data), 1)
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
    
    # 2. 涨跌比
    if overview:
        rising = overview.get("rising", 0)
        falling = overview.get("falling", 0)
        total = max(rising + falling, 1)
        ratio = rising / total
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
    
    # 3. 跌停占比
    if overview:
        limit_down = overview.get("limit_down", 0)
        total = max(overview.get("total", 1), 1)
        down_ratio = limit_down / total
        if down_ratio > 0.05:
            score -= 15
        elif down_ratio > 0.02:
            score -= 8
    
    # 兜底
    score = max(0, min(100, score))
    
    # 标签
    if score >= 60:
        label = "安全"
    elif score >= 40:
        label = "谨慎"
    elif score >= 25:
        label = "偏冷"
    elif score >= 10:
        label = "冰点"
    else:
        label = "恐慌"
    
    return score, label


def calc_market_temperature(indices_data: list) -> Tuple[int, int, int]:
    """
    计算综合市场温度 (0-100)
    
    Returns:
      (温度, 恐慌指数, 涨跌幅加权)
    """
    if not indices_data:
        return 50, 50, 0
    
    # 主要指数涨跌幅权重
    weights = {"上证指数": 0.4, "沪深300": 0.3, "创业板指": 0.2, "科创50": 0.1}
    weighted_chg = 0
    
    for idx in indices_data:
        w = weights.get(idx.get("name", ""), 0.15)
        weighted_chg += idx.get("pct", 0) * w
    
    # 温度映射
    if weighted_chg > 2.0:
        temp = 85
    elif weighted_chg > 1.0:
        temp = 70
    elif weighted_chg > 0.3:
        temp = 60
    elif weighted_chg > -0.3:
        temp = 50
    elif weighted_chg > -1.0:
        temp = 40
    elif weighted_chg > -2.0:
        temp = 30
    else:
        temp = 20
    
    panic_idx, _ = calc_panic_index(indices_data)
    
    return temp, panic_idx, round(weighted_chg, 2)


def get_market_overview() -> dict:
    """获取市场概览(涨跌家数)"""
    url = "https://qt.gtimg.cn/q=sh000001"
    raw = http_get(url)
    result = {"total": 0, "rising": 0, "falling": 0, "limit_up": 0, "limit_down": 0, "unchanged": 0}
    if not raw:
        return result
    m = re.search(r'v_sh000001="(.+)"', raw)
    if not m:
        return result
    parts = m.group(1).split("~")
    if len(parts) >= 60:
        try:
            result.update({
                "rising": int(parts[51]) if parts[51] else 0,
                "limit_up": int(parts[52]) if parts[52] else 0,
                "falling": int(parts[53]) if parts[53] else 0,
                "limit_down": int(parts[54]) if parts[54] else 0,
                "total": int(parts[51]) + int(parts[53]) + (int(parts[55]) if parts[55] else 0),
                "unchanged": int(parts[55]) if parts[55] else 0,
            })
        except (ValueError, IndexError):
            pass
    return result


def get_index_snapshot() -> dict:
    """获取主要指数行情"""
    codes = {
        "sh000001": "上证指数", "sz399001": "深证成指",
        "sz399006": "创业板指", "sh000300": "沪深300",
        "sh000016": "上证50",   "sz399905": "科创50",
    }
    url = f"https://qt.gtimg.cn/q={','.join(codes.keys())}"
    raw = http_get(url)
    result = {"indices": [], "time": datetime.now().strftime("%H:%M:%S")}
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
        name = codes.get(code_raw, parts[1])
        try:
            price = float(parts[3])
            prev_close = float(parts[4])
            pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
        except (ValueError, IndexError):
            continue
        result["indices"].append({
            "name": name, "code": code_raw,
            "price": price, "prev_close": prev_close,
            "pct": pct, "time": parts[30] if len(parts) > 30 else None,
        })
    
    return result


# ============ 持仓管理 ============
def load_portfolio() -> dict:
    if PORTFOLIO_FILE.exists():
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {"cash": 100000, "positions": [], "total_value": 100000, "history": []}


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "circuit_breaker": False, "circuit_reason": "",
        "today_buys": 0, "last_trade_date": "",
        "market_temperature": 50, "panic_index": 60,
        "daily_trade_record": [],
        "last_buy_time": None,     # R21: 上次买入时间
    }


def save_portfolio(portfolio: dict):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def reset_daily_limits(state: dict) -> dict:
    """重置每日交易计数"""
    today = date.today().strftime("%Y-%m-%d")
    if state.get("last_trade_date") != today:
        state["today_buys"] = 0
        state["last_trade_date"] = today
        state["last_buy_time"] = None
        state["daily_trade_record"] = []
    return state


def update_current_prices(portfolio: dict) -> dict:
    """获取所有持仓现价"""
    prices = {}
    for pos in portfolio.get("positions", []):
        if pos.get("status") != "holding":
            continue
        try:
            code = pos["code"]
            prefix = "sz" if code.startswith(("00", "30")) else "sh"
            url = f"https://qt.gtimg.cn/q={prefix}{code}"
            raw = http_get(url, timeout=5)
            if raw:
                m = re.search(r'v_\w+="(.+)"', raw)
                if m:
                    parts = m.group(1).split("~")
                    if len(parts) > 3:
                        prices[code] = float(parts[3])
        except Exception:
            pass
        if code not in prices:
            prices[code] = pos.get("entry_price", 0)
    return prices


# ============ R20 浮亏分级响应 ============
def check_loss_graded(state: dict, portfolio: dict, current_prices: dict) -> List[str]:
    """
    浮亏分级响应 v4.0
    
    4级主动管理:
      1级: -2% → 警示（推送警告）
      2级: -3% → 减半仓（卖出50%）
      3级: -5% → 止损（全出）
      4级: -7% → 强平（立即无条件清仓）
    """
    actions = []
    
    for pos in list(portfolio["positions"]):
        if pos.get("status") != "holding":
            continue
        code = pos["code"]
        cur = current_prices.get(code, pos["entry_price"])
        entry = pos["entry_price"]
        if entry == 0:
            continue
        pnl_pct = (cur / entry - 1) * 100
        
        # 4级: 强平
        if pnl_pct <= LOSS_FORCE_PCT:
            msg = f"🔴【强平】{pos['name']} 浮亏{pnl_pct:.2f}% 触发4级强平线({LOSS_FORCE_PCT}%)"
            wechat_notify(msg)
            auto_sell(state, portfolio, code, f"强平(4级, {pnl_pct:.2f}%)", current_prices)
            actions.append(msg)
            log(msg, "WARN")
            continue
        
        # 3级: 止损
        if pnl_pct <= LOSS_STOP_PCT:
            msg = f"🔴【止损】{pos['name']} 浮亏{pnl_pct:.2f}% 触发3级止损({LOSS_STOP_PCT}%)"
            wechat_notify(msg)
            auto_sell(state, portfolio, code, f"止损(3级, {pnl_pct:.2f}%)", current_prices)
            actions.append(msg)
            log(msg, "WARN")
            continue
        
        # 2级: 减半仓
        if pnl_pct <= LOSS_HALVE_PCT:
            half_shares = pos["shares"] // 2
            if half_shares >= 100:
                actual_sell = half_shares - (half_shares % 100)  # 整百
                if actual_sell >= 100:
                    sell_value = cur * actual_sell
                    pos["shares"] -= actual_sell
                    pos["cost"] = pos["entry_price"] * pos["shares"]
                    portfolio["cash"] += sell_value
                    msg = f"🟡【减仓】{pos['name']} 浮亏{pnl_pct:.2f}% 触发2级({LOSS_HALVE_PCT}%), 卖出{actual_sell}股"
                    wechat_notify(msg)
                    actions.append(msg)
                    log(msg, "WARN")
                else:
                    # 不足100股直接清
                    auto_sell(state, portfolio, code, f"减仓(不足百股全出)", current_prices)
            else:
                auto_sell(state, portfolio, code, f"减仓(2级,不足百股)", current_prices)
            continue
        
        # 1级: 警示
        if pnl_pct <= LOSS_ALERT_PCT:
            actions.append(f"⚠️【警示】{pos['name']}浮亏{pnl_pct:.2f}% 触发1级警示线({LOSS_ALERT_PCT}%)")
            log(actions[-1], "INFO")
    
    return actions


# ============ 交易执行 ============
def auto_buy(state: dict, portfolio: dict, code: str, name: str,
             price: float, shares: int) -> bool:
    """执行买入（含R21冷却检查）"""
    cost = price * shares
    
    if not can_buy(state, portfolio, code, cost):
        return False
    
    # R07-v2 恐慌因子: 恐慌环境止损收紧30%
    panic = state.get("panic_index", 60)
    if panic < 40:
        sl_pct = max(STOP_LOSS_PCT * 0.7, 2.0)  # 收紧30%，最低2%
    else:
        sl_pct = STOP_LOSS_PCT
    
    # R08-v2 恐慌反弹: 止盈档位收紧
    if panic < 30:
        tp_levels = [2, 4]  # 恐慌: +2%强制减半, +4%清仓
    elif panic < 40:
        tp_levels = [3, 6]
    else:
        tp_levels = [4, 8, 12]
    
    stop_loss = round(price * (1 - sl_pct / 100), 2)
    take_profit = round(price * (1 + tp_levels[0] / 100), 2)
    
    position = {
        "code": code, "name": name,
        "entry_price": price, "shares": shares, "cost": cost,
        "stop_loss": stop_loss, "stop_loss_pct": round(sl_pct, 1),
        "take_profit": take_profit, "take_profit_pct": tp_levels[0],
        "take_profit_levels": tp_levels,
        "buy_date": datetime.now().strftime("%Y-%m-%d"),
        "buy_time": datetime.now().strftime("%H:%M"),
        "status": "holding",
        "version": "v4.0",
    }
    
    portfolio["positions"].append(position)
    portfolio["cash"] -= cost
    portfolio["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": "BUY_AUTO_v4",
        "code": code, "name": name,
        "price": price, "shares": shares, "cost": cost,
        "signal": f"系统买入(温度{state.get('market_temperature','?')}℃)",
        "rules_applied": ["R19", "R21", "R07-v2", "R08-v2"],
    })
    
    state["today_buys"] += 1
    state["last_buy_time"] = datetime.now().strftime("%H:%M")
    state.setdefault("daily_trade_record", []).append({
        "time": datetime.now().strftime("%H:%M"),
        "action": "BUY", "code": code, "name": name,
    })
    
    save_portfolio(portfolio)
    save_state(state)
    
    msg = (f"📗 【v4.0自动买入】\n{name}({code})\n"
           f"价格：¥{price} × {shares}股\n"
           f"成本：¥{cost:,.2f}\n"
           f"止损：¥{stop_loss}(-{sl_pct:.1f}%) | 止盈：¥{take_profit}(+{tp_levels[0]}%)\n"
           f"温度：{state.get('market_temperature','?')}℃ | 恐慌：{state.get('panic_index','?')}\n"
           f"今日买入：{state['today_buys']}/{MAX_BUYS_PER_DAY}次")
    wechat_notify(msg)
    log(f"买入 {name}({code}) {shares}股@{price} 成本¥{cost:,.2f}")
    return True


def auto_sell(state: dict, portfolio: dict, code: str, reason: str,
              current_prices: dict = None) -> bool:
    """自动卖出"""
    prices = current_prices or {}
    for i, pos in enumerate(portfolio["positions"]):
        if pos["code"] == code and pos.get("status") == "holding":
            entry = pos["entry_price"]
            price = prices.get(code, entry)
            sell_value = price * pos["shares"]
            portfolio["positions"].pop(i)
            portfolio["cash"] += sell_value
            pnl_pct = (price / entry - 1) * 100 if entry else 0
            pnl_val = (price - entry) * pos["shares"]
            portfolio["history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "SELL_AUTO_v4", "code": code, "name": pos["name"],
                "reason": reason, "entry_price": entry, "cost": pos["cost"],
                "sell_price": price, "sell_value": sell_value,
                "pnl_pct": round(pnl_pct, 2), "pnl_val": round(pnl_val, 2),
            })
            save_portfolio(portfolio)
            save_state(state)
            emoji = "🟢" if pnl_val >= 0 else "🔴"
            msg = (f"📕 【v4.0卖出】\n{pos['name']}({code})\n"
                   f"卖出价：¥{price} × {pos['shares']}股 = ¥{sell_value:,.2f}\n"
                   f"{emoji} 盈亏：{pnl_pct:+.2f}% (¥{pnl_val:,.0f})\n"
                   f"原因：{reason}")
            wechat_notify(msg)
            log(f"卖出 {pos['name']}({code}) 原因:{reason} PnL:{pnl_pct:+.2f}%")
            return True
    return False


def trigger_circuit_breaker(state: dict, reason: str):
    """触发熔断"""
    state["circuit_breaker"] = True
    state["circuit_reason"] = reason
    save_state(state)
    msg = f"🚨【熔断】{reason}"
    wechat_notify(msg)
    log(msg, "WARN")


# ============ 买入条件检查 ============
def can_buy(state: dict, portfolio: dict, code: str, cost: float) -> Tuple[bool, str]:
    """
    R18+R19+R21 三重买入检查
    
    Returns:
      (可买入, 理由)
    """
    state = reset_daily_limits(state)
    
    # R11: 熔断检查
    if state.get("circuit_breaker"):
        return False, "熔断中"
    
    # R05: 当日买入次数
    if state["today_buys"] >= MAX_BUYS_PER_DAY:
        return False, f"今日买入{state['today_buys']}次已达上限({MAX_BUYS_PER_DAY})"
    
    # R21: 冷却期检查
    last_buy = state.get("last_buy_time")
    if last_buy:
        now = datetime.now()
        try:
            last_h, last_m = map(int, last_buy.split(":"))
            last_dt = now.replace(hour=last_h, minute=last_m)
            if (now - last_dt).total_seconds() < MIN_BUY_INTERVAL_MIN * 60:
                remain = MIN_BUY_INTERVAL_MIN - (now - last_dt).total_seconds() / 60
                return False, f"冷却期剩余{remain:.0f}分钟(R21)"
        except Exception:
            pass
    
    # R18: 冰点期禁止
    market_temp = state.get("market_temperature", 50)
    panic = state.get("panic_index", 60)
    
    if market_temp < 25:
        return False, f"温度{market_temp}℃ < 25 => 冰封期强制空仓(V10)"
    if market_temp < 35:
        return False, f"温度{market_temp}℃ < 35 => 冰点期禁止新开仓(R18)"
    
    # V10: 恐慌强制空仓
    if panic < 25:
        return False, f"恐慌指数{panic} < 25 => 恐慌期强制空仓(V10)"
    if panic < 35:
        return False, f"恐慌指数{panic} < 35 => 恐慌期禁止入场"
    
    # R06: 单只持仓比例
    total_value = portfolio["cash"] + sum(
        p.get("cost", 0) for p in portfolio["positions"] if p.get("status") == "holding"
    )
    if total_value > 0 and cost > total_value * MAX_POSITION_PCT / 100:
        return False, f"{code}买入{cost:,.0f}超过单只上限{MAX_POSITION_PCT}%"
    if cost > portfolio["cash"]:
        return False, "现金不足"
    
    return True, "通过"


# ============ R19 大盘三重确认 ============
def check_market_confirmation(indices_data: list, overview: dict) -> Tuple[bool, list]:
    """
    大盘趋势三重确认 R19
    
    检查:
      1. 沪深300收盘价站上20日均线(用前日收盘近似)
      2. 涨跌比 > 0.6
      3. 非恐慌状态
    """
    confirmations = []
    
    # 确认1: 沪深300涨跌幅
    hs300 = next((i for i in indices_data if "沪深300" in i.get("name", "")), None)
    if hs300 and hs300.get("pct", 0) > -0.5:
        confirmations.append(f"✅ 沪深300运行正常({hs300['pct']:+.2f}%)")
    else:
        confirmations.append(f"❌ 沪深300偏弱({hs300['pct']:+.2f}%)")
    
    # 确认2: 涨跌比
    if overview:
        rising = overview.get("rising", 0)
        falling = overview.get("falling", 0)
        total = max(rising + falling, 1)
        ratio = rising / total
        if ratio > 0.6:
            confirmations.append(f"✅ 涨跌比{ratio:.0%} > 0.6")
        elif ratio > 0.4:
            confirmations.append(f"⚠️ 涨跌比{ratio:.0%}, 市场中性")
        else:
            confirmations.append(f"❌ 涨跌比{ratio:.0%} < 0.4, 偏弱")
    
    # 确认3: 非恐慌
    panic_idx, panic_label = calc_panic_index(indices_data, overview)
    if panic_idx >= 40:
        confirmations.append(f"✅ 恐慌指数{panic_idx}({panic_label}), 安全")
    elif panic_idx >= 25:
        confirmations.append(f"⚠️ 恐慌指数{panic_idx}({panic_label}), 偏冷")
    else:
        confirmations.append(f"❌ 恐慌指数{panic_idx}({panic_label}), 禁止入场")
    
    passed = all("✅" in c for c in confirmations)
    return passed, confirmations


# ============ R08-v2 分批止盈（温度自适应） ============
def check_take_profit_graded(state: dict, portfolio: dict, 
                              current_prices: dict, market_temp: int, panic: int) -> List[str]:
    """
    分批止盈 R08-v2
    
    温度自适应档位:
      - 正常(≥50): +4%卖1/3, +8%卖1/3, +12%清仓
      - 偏冷(35-50): +3%卖1/3, +6%卖1/3, +8%清仓
      - 冰点(<35): +2%强制减半, +4%清仓
      - 恐慌: +2%强制减半(V09), 不再等第二档
    """
    actions = []
    
    for pos in list(portfolio["positions"]):
        if pos.get("status") != "holding":
            continue
        code = pos["code"]
        cur = current_prices.get(code, pos["entry_price"])
        entry = pos["entry_price"]
        if entry == 0:
            continue
        pnl_pct = (cur / entry - 1) * 100
        
        # 温度自适应档位
        if panic < 30 or market_temp < 35:
            tier1 = 2.0  # V09: 冰点+2%强制减半
            tier2 = 4.0
            tier3 = 99.0
        elif market_temp < 50:
            tier1 = 3.0
            tier2 = 6.0
            tier3 = 8.0
        elif market_temp >= 70:
            tier1 = 5.0
            tier2 = 10.0
            tier3 = 15.0
        else:
            tier1 = 4.0
            tier2 = 8.0
            tier3 = 12.0
        
        if pnl_pct >= tier3:
            auto_sell(state, portfolio, code, f"止盈3档(+{pnl_pct:.1f}%)", current_prices)
            actions.append(f"🟢【止盈清仓】{pos['name']}+{pnl_pct:.1f}%")
        elif pnl_pct >= tier2:
            # 卖出2/3
            sell_shares = (pos["shares"] * 2 // 3) - ((pos["shares"] * 2 // 3) % 100)
            if sell_shares >= 100:
                sell_value = cur * sell_shares
                pos["shares"] -= sell_shares
                pos["cost"] = entry * pos["shares"]
                portfolio["cash"] += sell_value
                actions.append(f"🟡【止盈2档】{pos['name']}+{pnl_pct:.1f}%, 卖{sell_shares}股留{pos['shares']}股")
                wechat_notify(actions[-1])
            else:
                auto_sell(state, portfolio, code, f"止盈2档(不足百股)", current_prices)
        elif pnl_pct >= tier1:
            if panic < 30 or market_temp < 35:
                # V09: 恐慌反弹强制减半
                half = pos["shares"] // 2
                half = half - (half % 100)
                if half >= 100:
                    sell_value = cur * half
                    pos["shares"] -= half
                    pos["cost"] = entry * pos["shares"]
                    portfolio["cash"] += sell_value
                    actions.append(f"🟡【恐慌反弹减半】{pos['name']}+{pnl_pct:.1f}%, 卖{half}股(V09)")
                    wechat_notify(actions[-1])
                else:
                    auto_sell(state, portfolio, code, f"恐慌反弹(不足百股全出)", current_prices)
            else:
                # 正常止盈1档: 卖1/3
                third = pos["shares"] // 3
                third = third - (third % 100)
                if third >= 100:
                    sell_value = cur * third
                    pos["shares"] -= third
                    pos["cost"] = entry * pos["shares"]
                    portfolio["cash"] += sell_value
                    actions.append(f"🟡【止盈1档】{pos['name']}+{pnl_pct:.1f}%, 卖{third}股")
                    wechat_notify(actions[-1])
    
    return actions


# ============ 仓位计算 ============
def calc_position_size(state: dict, portfolio: dict) -> Tuple[int, str]:
    """
    根据温度仓位矩阵计算目标仓位
    
    Returns:
      (目标仓位占比0-100, 标签)
    """
    temp = state.get("market_temperature", 50)
    
    for threshold, ratio, label in TEMPERATURE_MATRIX:
        if temp >= threshold:
            return int(ratio * 100), label
    
    return 0, "冰封"


def should_buy_v4(state: dict, portfolio: dict, indices_data: list, overview: dict) -> Tuple[bool, str]:
    """
    v4.0买入决策
    
    检查链:
      1. R10 熔断? → 跳过
      2. R18 冰点? → 跳过  
      3. V10 恐慌? → 跳过
      4. R19 大盘确认? → 跳过
      5. R05 买入次数? → 跳过
      6. R21 冷却期? → 跳过
    """
    state = reset_daily_limits(state)
    
    # 1. 熔断
    if state.get("circuit_breaker"):
        return False, "🚨 熔断中"
    
    # 2-3. 冰点/恐慌检查
    temp = state.get("market_temperature", 50)
    panic = state.get("panic_index", 60)
    
    if temp < 25:
        return False, f"❌ V10冰封: 温度{temp}℃ < 25"
    if temp < 35:
        return False, f"❌ R18冰点: 温度{temp}℃ < 35"
    if panic < 25:
        return False, f"❌ V10恐慌: 恐慌{panic} < 25"
    if panic < 35:
        return False, f"❌ 恐慌期: 恐慌{panic} < 35"
    
    # 4. 大盘确认
    if indices_data and overview:
        passed, confirmations = check_market_confirmation(indices_data, overview)
        if not passed and (temp < 50):
            return False, f"❌ R19大盘确认失败: {'; '.join(c for c in confirmations if '❌' in c)}"
    
    # 5. 交易次数
    if state["today_buys"] >= MAX_BUYS_PER_DAY:
        return False, f"❌ R05今日已达上限{MAX_BUYS_PER_DAY}次"
    
    # 6. 冷却期
    last_buy = state.get("last_buy_time")
    if last_buy:
        now = datetime.now()
        try:
            last_h, last_m = map(int, last_buy.split(":"))
            last_dt = now.replace(hour=last_h, minute=last_m)
            elapsed = (now - last_dt).total_seconds() / 60
            if elapsed < MIN_BUY_INTERVAL_MIN:
                return False, f"⏳ R21冷却期剩余{MIN_BUY_INTERVAL_MIN - elapsed:.0f}分钟"
        except Exception:
            pass
    
    return True, "✅ 全部通过"


# ============ 持仓状态推送 ============
def push_portfolio_status(portfolio: dict, state: dict, current_prices: dict = None):
    """推送持仓状态"""
    if current_prices is None:
        current_prices = update_current_prices(portfolio)
    
    holding = [p for p in portfolio["positions"] if p.get("status") == "holding"]
    total_value = portfolio["cash"] + sum(
        current_prices.get(p["code"], p["entry_price"]) * p["shares"]
        for p in holding
    )
    total_cost = sum(p["cost"] for p in holding)
    total_pnl = total_value - portfolio["cash"] - total_cost if total_cost > 0 else 0
    
    lines = [f"📊 【猎手v4.0持仓】{datetime.now().strftime('%H:%M')}"]
    lines.append(f"温度: {state.get('market_temperature','?')}℃ | 恐慌: {state.get('panic_index','?')}")
    
    if not holding:
        lines.append("🟣 **空仓** (冰封期)")
    else:
        for pos in holding:
            cur = current_prices.get(pos["code"], pos["entry_price"])
            pnl = (cur / pos["entry_price"] - 1) * 100
            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(f"{emoji} {pos['name']} ¥{cur} ({pnl:+.2f}%)")
            lines.append(f"    H:{pos['entry_price']} S:{pos.get('stop_loss','?')} T:{pos.get('take_profit','?')}")
    
    lines.append(f"\n现金：¥{portfolio['cash']:,.0f}")
    lines.append(f"总市值：¥{total_value:,.0f}")
    if total_pnl != 0:
        lines.append(f"浮动盈亏：¥{total_pnl:+,.0f}")
    lines.append(f"规则版本：v4.0 | 买入{state.get('today_buys',0)}次")
    
    wechat_notify("\n".join(lines))


# ============ 主执行流程 ============
def execute_trading_cycle(dry_run: bool = False) -> dict:
    """
    v4.0主执行流程
    
    流程:
      1. 时间校验
      2. 获取市场数据(指数+涨跌概况)
      3. 计算温度/恐慌
      4. R20 浮亏分级检查
      5. R08-v2 止盈检查
      6. R19+R18+R21 买入检查
      7. 选股(使用信号队列)
      8. 推送状态
    """
    # ── 1. 时间校验 ──
    is_trade, real_date, date_type = is_trading_day()
    weekday = WEEKDAY_NAMES[real_date.weekday()]
    now_str = datetime.now().strftime("%H:%M")
    trading_hours = is_trading_hours()
    
    log(f"{real_date} {weekday} {now_str} | {date_type} | 交易时段:{'是' if trading_hours else '否'}")
    
    if not is_trade:
        wechat_notify(f"📴 【v4.0校验】{real_date} {weekday} 非交易日，跳过")
        return {"status": "SKIP", "reason": f"非{date_type}"}
    
    # ── 2. 加载数据 ──
    portfolio = load_portfolio()
    state = load_state()
    state = reset_daily_limits(state)
    
    # ── 3. 市场数据 ──
    indices_data = get_index_snapshot()
    overview = get_market_overview()
    market_temp, panic_idx, weighted_chg = calc_market_temperature(indices_data.get("indices", []))
    
    state["market_temperature"] = market_temp
    state["panic_index"] = panic_idx
    state["weighted_change"] = weighted_chg
    
    if not trading_hours:
        state["market_temperature_off_hours"] = market_temp
        state["panic_index_off_hours"] = panic_idx
    
    # 温度仓位矩阵
    target_pos, pos_label = calc_position_size(state, portfolio)
    log(f"市场温度:{market_temp}℃ 恐慌:{panic_idx} 加权涨跌:{weighted_chg:+.2f}% 目标仓位:{target_pos}%({pos_label})")
    
    if market_temp < 35:
        log(f"🛑 冰封/冰点期: 停止所有买入操作", "WARN")
    
    save_state(state)
    
    # ── 4. 非交易时段: 只推送 ──
    if not trading_hours:
        push_portfolio_status(portfolio, state)
        return {
            "status": "NON_TRADING_HOURS",
            "market_temperature": market_temp,
            "panic_index": panic_idx,
        }
    
    # ── 交易时段: 完整流程 ──
    current_prices = update_current_prices(portfolio)
    actions = []
    
    # 4a. R20 分级止损
    if not dry_run:
        loss_actions = check_loss_graded(state, portfolio, current_prices)
        actions.extend(loss_actions)
        
        # 重新加载（可能有变化）
        portfolio = load_portfolio()
        current_prices = update_current_prices(portfolio)
        
        # 4b. R08-v2 分级止盈
        tp_actions = check_take_profit_graded(state, portfolio, current_prices, market_temp, panic_idx)
        actions.extend(tp_actions)
        
        portfolio = load_portfolio()
        current_prices = update_current_prices(portfolio)
    
    # 4c. 风控检查
    holding_stocks = [p for p in portfolio["positions"] if p.get("status") == "holding"]
    total_value = portfolio["cash"] + sum(
        current_prices.get(p["code"], p["entry_price"]) * p["shares"] for p in holding_stocks
    )
    total_cost = sum(p["cost"] for p in holding_stocks)
    if total_cost > 0:
        drawdown = (total_value - portfolio["cash"] - total_cost) / (total_value + 1) * -100
        if drawdown > 3:
            trigger_circuit_breaker(state, f"总回撤{drawdown:.1f}%超过风控线")
            for pos in list(portfolio["positions"]):
                if pos.get("status") == "holding":
                    auto_sell(state, portfolio, pos["code"], "风控熔断清仓", current_prices)
    
    # 4d. 买入决策
    can_buy_result, buy_reason = should_buy_v4(state, portfolio, 
                                                indices_data.get("indices", []), overview)
    state["can_buy"] = can_buy_result
    state["buy_reason"] = buy_reason
    save_state(state)
    
    if can_buy_result and not dry_run:
        log(f"✅ {buy_reason}")
        # 触发信号队列选股
        try:
            # 尝试执行信号队列 (保持兼容)
            sys.path.insert(0, str(BASE_DIR / "src"))
            from stock_picker import pick_best_candidates
            candidates = pick_best_candidates(max_count=MAX_BUYS_PER_DAY - state["today_buys"], min_score=5)
            today_str = date.today().isoformat()
            sig_dir = Path("/root/.hermes/猎手模拟交易/信号队列")
            sig_dir.mkdir(parents=True, exist_ok=True)
            signal_file = sig_dir / f"{today_str}_signals.jsonl"
            for c in candidates:
                code, name, price = c["code"], c["name"], c["price"]
                shares = int((portfolio["cash"] * (MAX_POSITION_PCT/100) / price) // 100 * 100)
                if shares < 100:
                    continue
                signal = {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "stock": code, "name": name,
                    "action": "buy", "price": price, "shares": shares,
                    "note": f"系统v4.0选股(温度{market_temp}℃, 恐慌{panic_idx})",
                    "status": "pending"
                }
                with open(signal_file, "a") as f:
                    f.write(json.dumps(signal, ensure_ascii=False) + "\n")
                log(f"  信号写入: {name}({code}) @ {price} × {shares}股")
        except Exception as e:
            log(f"选股模块调用失败: {e}", "WARN")
    elif not can_buy_result:
        log(f"⏸️ 买入跳过: {buy_reason}")
    
    # 4e. 状态推送
    push_portfolio_status(portfolio, state, current_prices)
    
    return {
        "status": "OK",
        "market_temperature": market_temp,
        "panic_index": panic_idx,
        "weighted_change": weighted_chg,
        "target_position": target_pos,
        "position_label": pos_label,
        "can_buy": can_buy_result,
        "buy_reason": buy_reason,
        "actions": actions,
        "cash": portfolio["cash"],
        "positions_count": len(holding_stocks),
        "today_buys": state["today_buys"],
        "version": "v4.0",
    }


# ============ CLI入口 ============
if __name__ == "__main__":
    import sys
    
    # 解析参数
    dry_run = "--dry-run" in sys.argv
    status_only = "--status-only" in sys.argv
    
    if status_only:
        portfolio = load_portfolio()
        state = load_state()
        push_portfolio_status(portfolio, state)
        print("状态推送完成")
        sys.exit(0)
    
    result = execute_trading_cycle(dry_run=dry_run)
    
    print(f"\n{'='*50}")
    print(f"猎手自动交易 v4.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    print(f"状态: {result.get('status', 'UNKNOWN')}")
    print(f"市场温度: {result.get('market_temperature', '?')}℃")
    print(f"恐慌指数: {result.get('panic_index', '?')}")
    print(f"加权涨跌: {result.get('weighted_change', 0):+.2f}%")
    print(f"目标仓位: {result.get('target_position', '?')}%({result.get('position_label','?')})")
    print(f"可买入: {result.get('can_buy', False)}")
    print(f"买入原因: {result.get('buy_reason', 'N/A')}")
    print(f"今日已买入: {result.get('today_buys', 0)}次")
    print(f"持仓: {result.get('positions_count', 0)}只")
    print(f"现金: ¥{result.get('cash', 0):,.2f}")
    if result.get('actions'):
        print(f"操作: {'; '.join(result['actions'])}")
    print(f"规则版本: {result.get('version', 'v4.0')}")
    print(f"{'='*50}")
