"""
猎手 × 进化系统 桥接模块
方案A：猎手选出候选 → 进化最优策略参数验证 → 通过才买

用法：
  from hunter_evo_bridge import validate_with_evo
  candidates = pick_best_candidates()  # 猎手选股
  validated = validate_with_evo(candidates)  # 进化策略验证
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta

# ── 路径设置 ────────────────────────────────────────────
HUNTER_ROOT = Path("/root/.openclaw/workspace/猎手模拟交易")
EVO_ROOT = HUNTER_ROOT / "evo-trader"
sys.path.insert(0, str(EVO_ROOT / "src"))

from backtest import BacktestEngine
from data_fetcher import DataFetcher
from strategy_gene import StrategyGene
import pandas as pd


# ══════════════════════════════════════════════════════════
# 1. 加载进化系统最优策略
# ══════════════════════════════════════════════════════════

def load_best_gene() -> StrategyGene:
    """从最新进化报告中加载最优策略参数"""
    import json
    results_dir = EVO_ROOT / "data" / "results"

    # 找最新报告
    reports = sorted(results_dir.glob("report_*.json"), reverse=True)
    if not reports:
        print("[警告] 无进化报告，使用默认策略参数")
        return default_gene()

    latest = reports[0]
    report = json.loads(latest.read_text())
    params = report["best_strategy"]["gene_params"]

    gene = StrategyGene()
    gene.ma_fast = int(params["ma_fast"])
    gene.ma_slow = int(params["ma_slow"])
    gene.ma_signal = int(params.get("ma_signal", 11))
    gene.rsi_period = int(params["rsi_period"])
    gene.rsi_overbought = float(params["rsi_overbought"])
    gene.rsi_oversold = float(params["rsi_oversold"])
    gene.volume_ma_period = int(params.get("volume_ma_period", 11))
    gene.volume_multiplier = float(params.get("volume_multiplier", 1.1))
    gene.position_size = float(params["position_size"])
    gene.stop_loss_pct = float(params["stop_loss_pct"])
    gene.take_profit_pct = float(params["take_profit_pct"])
    gene.max_hold_days = int(params.get("max_hold_days", 5))
    gene.weight_ma_cross = float(params.get("weight_ma_cross", 0.3))
    gene.weight_rsi_signal = float(params.get("weight_rsi_signal", 0.3))
    gene.weight_volume = float(params.get("weight_volume", 0.2))
    gene.weight_trend = float(params.get("weight_trend", 0.2))
    gene.normalize_weights()

    print(f"[进化桥] 加载最优策略 from {latest.name}: "
          f"MA({gene.ma_fast},{gene.ma_slow}) RSI({gene.rsi_period},{gene.rsi_overbought:.0f},{gene.rsi_oversold:.0f})")
    return gene


def default_gene() -> StrategyGene:
    """默认策略参数（当无进化报告时）"""
    gene = StrategyGene.random_gene()
    return gene


# ══════════════════════════════════════════════════════════
# 2. 进化策略验证
# ══════════════════════════════════════════════════════════

def validate_with_evo(candidates: List[Dict], lookback_days: int = 60) -> List[Dict]:
    """
    用进化最优策略参数验证猎手候选股

    策略：
      1. 加载最优策略参数
      2. 获取候选最近N日K线
      3. 计算技术指标（MA金叉/RSI/量价）
      4. 生成综合评分
      5. 返回通过验证的候选（含策略信号）

    参数：
      candidates: 猎手候选股列表 [{code, name, price, chg_pct, vol_ratio, score}, ...]
      lookback_days: 回测天数（默认60日）

    返回：
      通过验证的候选列表，含 evo_score 字段
    """
    gene = load_best_gene()
    fetcher = DataFetcher(str(EVO_ROOT / "data"))
    engine = BacktestEngine()

    validated = []

    print(f"\n[进化验证] 验证 {len(candidates)} 只候选股...")

    for cand in candidates:
        code = cand["code"]
        name = cand["name"]

        # 获取K线数据
        df = fetcher.get_daily_data(code, days=lookback_days)
        if df is None or len(df) < 30:
            print(f"  {code} {name}: 数据不足，跳过")
            continue

        # 计算技术指标（用进化策略参数）
        df = engine.calculate_technical_indicators(df, gene)

        # 生成综合评分
        score = calc_evo_score(df, gene)

        # 综合信号：进化评分 + 猎手原始评分
        combined_score = score * 0.6 + cand.get("score", 0) * 0.4

        result = {
            **cand,
            "evo_score": round(score, 2),
            "combined_score": round(combined_score, 2),
            "signal": "买入" if combined_score > 15 else ("观察" if combined_score > 8 else "放弃"),
        }

        # MA计算
        ma_fast_col = "ma_fast_val"
        ma_slow_col = "ma_slow_val"
        if "ma_fast" in df.columns and "ma_slow" in df.columns:
            ma_fast_val = df["ma_fast"].iloc[-1]
            ma_slow_val = df["ma_slow"].iloc[-1]
            result["ma_fast"] = round(ma_fast_val, 2) if pd.notna(ma_fast_val) else None
            result["ma_slow"] = round(ma_slow_val, 2) if pd.notna(ma_slow_val) else None
            result["ma_bullish"] = (ma_fast_val > ma_slow_val) if pd.notna(ma_fast_val) else False

        if pd.notna(df["rsi"].iloc[-1]):
            result["rsi"] = round(df["rsi"].iloc[-1], 1)

        print(f"  {code} {name}: 进化score={score:.1f} 猎手score={cand.get('score',0):.1f} 综合={combined_score:.1f} → {result['signal']}")

        validated.append(result)

    # 按综合评分排序
    validated.sort(key=lambda x: x["combined_score"], reverse=True)
    return validated


def calc_evo_score(df: pd.DataFrame, gene) -> float:
    """
    用进化策略权重计算综合评分
    """
    if len(df) < 5:
        return 0

    last = df.iloc[-1]

    # MA多头信号
    ma_bullish = 1 if (pd.notna(last["ma_fast"]) and pd.notna(last["ma_slow"])
                        and last["ma_fast"] > last["ma_slow"]) else 0

    # RSI信号（处于中性区域，不过热不过冷）
    rsi = last["rsi"] if pd.notna(last.get("rsi")) else 50
    if gene.rsi_oversold < rsi < gene.rsi_overbought:
        rsi_signal = 1
    elif rsi <= gene.rsi_oversold:
        rsi_signal = 2  # 超卖，强买入信号
    elif rsi >= gene.rsi_overbought:
        rsi_signal = 0  # 超买，弱信号
    else:
        rsi_signal = 1

    # 趋势信号（收盘价在均线上方）
    trend_signal = 1 if (pd.notna(last["ma_signal"]) and last["close"] > last["ma_signal"]) else 0

    # 量能信号
    vol_signal = 1 if last.get("volume_ratio", 1) > gene.volume_multiplier else 0

    # 加权综合评分
    score = (
        gene.weight_ma_cross * ma_bullish * 10 +
        gene.weight_rsi_signal * rsi_signal * 5 +
        gene.weight_volume * vol_signal * 5 +
        gene.weight_trend * trend_signal * 8
    )

    return max(0, score)


# ══════════════════════════════════════════════════════════
# 3. 集成到猎手选股流程
# ══════════════════════════════════════════════════════════

def scan_with_evo_validation(max_count: int = 5) -> List[Dict]:
    """
    完整流程：猎手选股 → 进化策略验证 → 返回最终候选
    替换猎手原有的 pick_best_candidates()
    """
    # Step 1: 猎手初筛
    from stock_picker import pick_best_candidates
    print("[猎手×进化] Step1: 猎手初筛候选股...")
    candidates = pick_best_candidates(max_count=max_count * 3)  # 多选一些，留足淘汰空间

    if not candidates:
        print("[猎手×进化] 无候选股")
        return []

    # Step 2: 进化策略验证
    print("[猎手×进化] Step2: 进化最优策略验证...")
    validated = validate_with_evo(candidates)

    # Step 3: 过滤，保留信号为"买入"的
    final = [v for v in validated if v["signal"] == "买入"]

    print(f"\n[猎手×进化] 最终候选: {len(final)} 只")
    for v in final:
        print(f"  {v['code']} {v['name']} 综合score={v['combined_score']:.1f}")

    return final


if __name__ == "__main__":
    print("=== 猎手×进化系统集成测试 ===\n")

    # 加载最优策略
    gene = load_best_gene()
    print(f"最优策略: MA({gene.ma_fast},{gene.ma_slow}) RSI({gene.rsi_period},{gene.rsi_overbought:.0f},{gene.rsi_oversold:.0f})")
    print(f"权重: MA交叉={gene.weight_ma_cross:.2f} RSI={gene.weight_rsi_signal:.2f} 量能={gene.weight_volume:.2f} 趋势={gene.weight_trend:.2f}")
