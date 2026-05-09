#!/usr/bin/env python3
"""
策略描述生成器
给每个策略基因生成自然语言解读（JSON格式）
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from glm_helper import call_glm_json, save_output, OUTPUT_DIR


def generate_strategy_desc_json(gene: dict) -> dict:
    """
    为单个策略生成完整描述
    """
    gene_str = json.dumps(gene, ensure_ascii=False, indent=2)
    
    prompt = f"""你是量化策略专家。请为以下策略参数生成完整的策略描述。

【策略参数】
{gene_str}

请生成以下信息（直接输出JSON，不要其他内容）：
{{
    "name": "策略简称（10字内）",
    "trading_style": "交易风格（趋势/均值回归/突破/量价配合等）",
    "description": "用2-3句话描述这个策略的核心逻辑",
    "buy_condition": "具体描述买入条件（什么情况下买入，1句话）",
    "sell_condition": "具体描述卖出条件（什么情况下卖出，1句话）",
    "suitable_market": "适合的市场环境（1句话）",
    "risk": "最大风险点（1句话）"
}}

输出格式：必须是有效JSON，不要加markdown代码块标记。"""

    raw = call_glm_json(prompt, max_tokens=1500)
    
    try:
        desc = json.loads(raw)
        
        if 'ma_fast' in gene and 'rsi_period' in gene:
            sid = f"MA_RSI_{gene['ma_fast']}_{gene['ma_slow']}_{gene['rsi_period']}"
        elif 'ma_fast' in gene:
            sid = f"MA_{gene['ma_fast']}_{gene['ma_slow']}"
        elif 'rsi_period' in gene:
            sid = f"RSI_{gene['rsi_period']}"
        else:
            sid = f"STRAT_{abs(hash(json.dumps(gene, sort_keys=True))) % 10000}"
        
        desc['strategy_id'] = sid
        desc['params'] = gene
        return desc
        
    except json.JSONDecodeError:
        return {
            "strategy_id": f"ERR_{abs(hash(gene_str)) % 10000}",
            "name": "解析失败",
            "trading_style": "未知",
            "description": raw[:300],
            "params": gene,
        }


def generate_pool_descriptions(pool_size: int = 20) -> list:
    """为策略池生成描述"""
    from src.strategy_gene import StrategyGene
    
    strategies = []
    for i in range(pool_size):
        gene = StrategyGene.random_gene()
        strategies.append({
            "ma_fast": gene.ma_fast,
            "ma_slow": gene.ma_slow,
            "ma_signal": gene.ma_signal,
            "rsi_period": gene.rsi_period,
            "rsi_overbought": gene.rsi_overbought,
            "rsi_oversold": gene.rsi_oversold,
            "volume_ma_period": gene.volume_ma_period,
            "volume_multiplier": gene.volume_multiplier,
            "position_size": gene.position_size,
            "stop_loss_pct": gene.stop_loss_pct,
            "take_profit_pct": gene.take_profit_pct,
            "max_hold_days": gene.max_hold_days,
            "weight_ma_cross": gene.weight_ma_cross,
            "weight_rsi_signal": gene.weight_rsi_signal,
            "weight_volume": gene.weight_volume,
            "weight_trend": gene.weight_trend,
        })
    
    print(f"为 {len(strategies)} 个策略生成描述...")
    
    results = []
    for i, gene in enumerate(strategies):
        print(f"  [{i+1}/{len(strategies)}] 生成策略描述...", end=" ", flush=True)
        desc = generate_strategy_desc_json(gene)
        results.append(desc)
        print(f"✅ {desc.get('name', 'N/A')}")
    
    return results


def save_strategy_descriptions(descriptions: list) -> str:
    """保存策略描述到文件"""
    filepath = OUTPUT_DIR / f"strategy_descriptions_{len(descriptions)}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=2)
    print(f"已保存: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    print("=== 策略描述生成器（JSON版）===")
    
    results = generate_pool_descriptions(pool_size=3)
    save_strategy_descriptions(results)
    
    print("\n生成结果：")
    for r in results:
        print(f"\n{r['strategy_id']}: {r['name']}")
        print(f"  风格: {r.get('trading_style', 'N/A')}")
        print(f"  逻辑: {r.get('description', 'N/A')[:100]}")
