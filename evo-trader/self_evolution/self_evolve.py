#!/usr/bin/env python3
"""
进化交易系统 - 自我进化引擎
使用大模型分析市场数据、策略表现，自动优化参数和规则
数据源：公开市场数据，不涉及隐私
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

DEEPSEEK_API = "https://api.deepseek.com/v1"
DEEPSEEK_KEY = "sk-99fbf83aa6704057b2eae88dba14e88b"
MODEL = "deepseek-v4-flash"

EVO_DIR = Path(__file__).parent.parent
STATE_FILE = EVO_DIR / "data" / "evolution_state.json"
TRADE_LOG = EVO_DIR / "data" / "trade_log.json"
OUTPUT_DIR = EVO_DIR / "self_evolution"
OUTPUT_DIR.mkdir(exist_ok=True)


def call_model(prompt: str, max_tokens: int = 8000) -> str:
    """调用DeepSeek大模型（使用curl，OpenAI兼容格式）"""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一位专业的量化交易策略师，帮助分析市场和优化交易策略。回答尽量详细。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    cmd = [
        "curl", "-s", "-X", "POST",
        f"{DEEPSEEK_API}/chat/completions",
        "-H", f"Authorization: Bearer {DEEPSEEK_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        resp = json.loads(result.stdout)
        msg = resp["choices"][0]["message"]
        # GLM模型返回在reasoning_content，OpenAI兼容格式返回在content
        content = msg.get("content") or msg.get("reasoning_content") or ""
        return content
    except Exception as e:
        return f"API调用失败: {e}\nstdout: {result.stdout[:500]}"


def gather_market_data() -> str:
    """收集今日市场数据（公开数据）"""
    import urllib.request, re

    indices = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
        ("sh000300", "沪深300"),
    ]

    lines = []
    codes_batch = ",".join([f"sh{code[2:]}" if len(code) == 8 else code for code, _ in indices])
    try:
        url = f"https://qt.gtimg.cn/q={codes_batch}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode("gbk")

        for line in raw.strip().split("\n"):
            if "~" not in line:
                continue
            parts = line.split('"')[1].split("~")
            if len(parts) < 35:
                continue
            name = parts[1]
            price = parts[3]
            chg = parts[32]
            vol_ratio = parts[49] if parts[49] else "N/A"
            high = parts[33]
            low = parts[34]
            lines.append(f"{name}: 现价{price} | 涨跌{chg}% | 量比{vol_ratio} | 最高{high} | 最低{low}")
    except Exception as e:
        lines.append(f"市场数据获取失败: {e}")

    return "\n".join(lines)


def gather_strategy_data() -> dict:
    """收集策略数据"""
    data = {"trade_log": [], "strategy_state": {}}

    try:
        if TRADE_LOG.exists():
            with open(TRADE_LOG) as f:
                data["trade_log"] = json.load(f)
    except:
        pass

    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                data["strategy_state"] = json.load(f)
    except:
        pass

    return data


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始自我进化分析...")

    # 1. 市场数据
    print("📊 收集市场数据...")
    market = gather_market_data()
    print(f"  {market.split(chr(10))[0]}")

    # 2. 策略数据
    print("🧬 收集策略数据...")
    strat = gather_strategy_data()
    print(f"  交易记录: {len(strat['trade_log'])}条")

    # 3. 构建提示词
    prompt = f"""你是量化交易策略专家。当前日期{datetime.now().strftime('%Y-%m-%d')}

## 今日市场数据（公开）
{market}

## 策略状态
策略池: 20个策略
交易记录: {json.dumps(strat['trade_log'], ensure_ascii=False, indent=2)}

## 当前持仓
中信证券(600030): 买入价27.18元，止损26.23，止盈29.35，试探仓300股

## 请输出以下分析（JSON格式，尽量详细）：

```json
{{
  "市场环境": {{
    "温度评估": "冰点/暖意/强势",
    "风险点": ["具体风险"],
    "建议仓位": "0-100%",
    "说明": "分析依据"
  }},
  "策略优化": {{
    "止损优化": "建议值和理由",
    "止盈优化": "建议值和理由", 
    "仓位优化": "建议值和理由"
  }},
  "选股规则优化": {{
    "规则调整": "具体修改建议",
    "新增条件": "建议增加的条件",
    "删除条件": "建议删除的条件"
  }},
  "下一步行动": {{
    "关注标的": ["具体股票代码和理由"],
    "注意事项": ["具体风险提示"],
    "是否加仓": "是/否/观望"
  }}
}}
```"""

    # 4. 大模型分析
    print("🤖 大模型深度分析中（deepseek-v4-flash，8000 token）...")
    response = call_model(prompt, max_tokens=8000)

    # 5. 保存报告
    report_file = OUTPUT_DIR / f"evolution_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# 自我进化报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## 市场数据\n{market}\n\n")
        f.write(f"## 策略数据\n{json.dumps(strat, ensure_ascii=False, indent=2)}\n\n")
        f.write(f"## 大模型分析\n{response}\n")

    # 6. 保存JSON建议
    try:
        import re
        json_match = re.search(r'\{{.*\}}', response, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
        else:
            suggestions = {"analysis": response}
    except:
        suggestions = {"analysis": response}

    with open(OUTPUT_DIR / "latest_suggestions.json", "w", encoding="utf-8") as f:
        json.dump(suggestions, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 进化完成 | 报告: {report_file.name}")
    print(f"\n=== 分析结果 ===")
    print(response[:4000])

    return response


if __name__ == "__main__":
    main()
