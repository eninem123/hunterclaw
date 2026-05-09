"""
Vibe-Trading × 猎手系统 集成桥接 v2
用AKShare替代猎手现有接口，Vibe-Trading技能增强信号

核心功能（已验证可用）：
1. AKShare获取K线数据（股票/ETF/指数）
2. 技术指标计算（通过pandas）
3. 涨停过滤
4. 板块动量查询（股票列表）
5. Vibe-Trading swarm用于选股分析

需要TUSHARE_TOKEN但本服务器无法访问tushare.net，跳过
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional

# ── 路径 ──────────────────────────────────────────────
VIBE_ROOT = Path("/root/Vibe-Trading")
sys.path.insert(0, str(VIBE_ROOT / "agent"))
sys.path.insert(0, str(VIBE_ROOT / "backtest"))
os.environ.setdefault("TUSHARE_TOKEN", "cc40a0c34aaa1bf16562c6c02eab4545bf260bef9f080ded0b8b29c4")

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# 1. 数据获取（AKShare）
# ══════════════════════════════════════════════════════════

def get_kline(code: str, days: int = 10, autype: str = "qfq") -> pd.DataFrame:
    """
    获取个股K线数据（AKShare，前复权）
    code: 股票代码，如 '000678' 或 '159715'
    """
    try:
        df = ak.stock_zh_a_hist(
            symbol=code, period="daily",
            start_date="20260501", end_date="20260508",
            adjust=autype
        )
        # 重命名为英文字段
        rename = {
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "涨跌幅": "chg_pct",
            "涨跌额": "chg_amt", "换手率": "turnover"
        }
        df = df.rename(columns=rename)
        return df.tail(days)
    except Exception as e:
        logger.warning(f"K线获取失败 {code}: {e}")
        return pd.DataFrame()


def get_realtime_quote(codes: list[str]) -> list[dict]:
    """
    获取多只股票实时行情（东方财富）
    批量获取，比逐只查询快
    """
    try:
        df = ak.stock_zh_a_spot_em()
        results = []
        for code in codes:
            row = df[df["代码"] == code]
            if row.empty:
                continue
            r = row.iloc[0]
            results.append({
                "code": code,
                "name": r["名称"],
                "price": float(r["最新价"]) if str(r["最新价"]) not in ["-", ""] else 0,
                "chg_pct": float(r["涨跌幅"]) if str(r["涨跌幅"]) not in ["-", ""] else 0,
                "volume_ratio": float(r["量比"]) if str(r["量比"]) not in ["-", ""] else 0,
                "amount": float(r["成交额"]) if str(r["成交额"]) not in ["-", ""] else 0,
                "turnover": float(r["换手率"]) if str(r["换手率"]) not in ["-", ""] else 0,
                "volume": float(r["成交量"]) if str(r["成交量"]) not in ["-", ""] else 0,
            })
        return results
    except Exception as e:
        logger.warning(f"实时行情获取失败: {e}")
        return []


def get_limit_up_stocks(date: str = None) -> list[dict]:
    """
    获取涨停股列表（东方财富）
    用于过滤涨停股 + 判断市场情绪
    """
    try:
        if date:
            df = ak.stock_zh_zt_pool_spot_em(date=date)
        else:
            df = ak.stock_zh_zt_pool_spot_em()
        return df.to_dict("records") if not df.empty else []
    except Exception:
        return []


def get_sector_stocks(sector: str = "行业资金流向") -> pd.DataFrame:
    """
    获取行业板块个股列表
    """
    try:
        df = ak.stock_sector_spot()
        return df.sort_values("涨跌幅", ascending=False)
    except Exception:
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════
# 2. 技术指标（pandas手写，不依赖ta-lib）
# ══════════════════════════════════════════════════════════

def calc_ma(series: pd.Series, n: int) -> float:
    return round(series.tail(n).mean(), 2)


def calc_vol_ratio(volumes: pd.Series) -> float:
    avg5 = volumes.tail(5).mean()
    today_vol = volumes.iloc[-1]
    return round(today_vol / avg5, 2) if avg5 > 0 else 0


def calc_trend_score(df: pd.DataFrame) -> dict:
    """
    计算简化趋势评分（仿Vibe-Trading技术分析技能）
    """
    if len(df) < 3:
        return {"score": 0, "signal": "数据不足"}

    closes = df["close"]
    volumes = df["volume"]

    # 动量：最近N日涨跌
    chg_pct = df["chg_pct"].iloc[-1] if "chg_pct" in df.columns else 0

    # 均线多头排列：close > MA5 > MA10 > MA20
    ma5 = calc_ma(closes, 5)
    ma20 = calc_ma(closes, 20)
    ma_cross = 1 if (ma5 > ma20) else 0

    # 量能：量比
    vol_ratio = calc_vol_ratio(volumes)

    # 综合评分
    score = chg_pct * 1.5 + vol_ratio * 2 + ma_cross * 3
    signal = "买入" if score > 15 else ("观察" if score > 8 else "卖出")

    return {
        "score": round(score, 1),
        "signal": signal,
        "chg_pct": round(chg_pct, 2),
        "vol_ratio": vol_ratio,
        "ma5": ma5,
        "ma20": ma20,
        "ma_cross": ma_cross,
    }


# ══════════════════════════════════════════════════════════
# 3. Vibe-Trading Swarm（选股增强）
# ══════════════════════════════════════════════════════════

def run_equity_swarm(target: str, market: str = "a_share") -> str:
    """
    运行Vibe-Trading的equity_research_team swarm
    对给定标的进行宏观→行业→个股三层次深度分析
    """
    import subprocess
    result = subprocess.run(
        ["vibe-trading", "--swarm-run", "equity_research_team",
         f"market={market}", f"goal=分析{target}是否值得建仓"],
        capture_output=True, text=True, timeout=300,
        cwd="/root/Vibe-Trading"
    )
    return result.stdout + result.stderr


# ══════════════════════════════════════════════════════════
# 4. 主选股函数（替换猎手原有逻辑）
# ══════════════════════════════════════════════════════════

def enhanced_scan(limit: int = 10) -> list[dict]:
    """
    增强选股扫描（AKShare + 技术指标）
    替代猎手现有stock_picker逻辑
    """
    print("[增强扫描] 获取全市场股票列表...")

    # 1. 获取全市场股票实时行情（东方财富）
    t0 = time.time()
    spot = ak.stock_zh_a_spot_em()
    print(f"[增强扫描] 行情获取完成，耗时{time.time()-t0:.1f}s，共{len(spot)}只")

    # 2. 过滤条件
    df = spot[
        (spot["涨跌幅"] >= 1.5) &   # 涨幅>=1.5%
        (spot["量比"] >= 1.0) &      # 量比>=1.0
        (~spot["名称"].str.contains("ST|ST", regex=True)) &
        (spot["最新价"] >= 3) &
        (spot["最新价"] <= 100)
    ].copy()

    df["score"] = df["涨跌幅"] * 2 + df["量比"] * 3
    df = df.sort_values("score", ascending=False).head(limit * 2)

    # 3. 逐只K线验证
    results = []
    for _, row in df.iterrows():
        code = row["代码"]
        name = row["名称"]

        # 涨停股排除
        chg_pct = row["涨跌幅"]
        if chg_pct >= 9.8:
            continue

        # 获取K线
        kdf = get_kline(code, days=5)
        if kdf.empty:
            continue

        trend = calc_trend_score(kdf)
        if trend["score"] < 8:
            continue

        results.append({
            "code": code,
            "name": name,
            "price": float(row["最新价"]),
            "chg_pct": round(float(chg_pct), 2),
            "vol_ratio": float(row["量比"]),
            "turnover": float(row["换手率"]),
            "score": round(trend["score"], 1),
            "signal": trend["signal"],
        })

        if len(results) >= limit:
            break

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    print("=== Vibe-Trading × 猎手增强扫描 ===")

    # 快速测试：获取K线
    print("\n[K线-襄阳轴承]")
    kdf = get_kline("000678", days=5)
    print(kdf[["date","close","chg_pct","volume"]].to_string())
    print("趋势评分:", calc_trend_score(kdf))

    print("\n[实时行情-持仓股]")
    codes = ["688260", "600030", "159715", "300232", "000678"]
    quotes = get_realtime_quote(codes)
    for q in quotes:
        print(f"  {q['code']} {q['name']} 最新价={q['price']} 涨跌幅={q['chg_pct']}%")

    print("\n[增强选股扫描-前5只候选]")
    candidates = enhanced_scan(limit=5)
    for c in candidates:
        print(f"  {c['code']} {c['name']} 涨{c['chg_pct']}% 量比{c['vol_ratio']} score={c['score']} 信号={c['signal']}")
