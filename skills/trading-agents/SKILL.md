---
name: trading-agents
description: "Multi-Agent交易决策：14个投资大师Agent多轮辩论生成综合交易信号，支持A股/美股"
version: 0.2.4
---

# TradingAgents

14个投资大师Agent多轮辩论，从价值/成长/风险/宏观多维度分析个股。

## 使用
```python
import sys; sys.path.insert(0, '/root/TradingAgents')
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
config = DEFAULT_CONFIG.copy()
config["deep_think_llm"] = "MiniMax-M2.7"
config["quick_think_llm"] = "MiniMax-M2.7"
ta = TradingAgentsGraph(debug=False, config=config)
_, decision = ta.propagate("300232", "2026-05-01")
```

## Agents
Buffett/Munger/Ackman/Wood/Burry/Lynch/Damodaran/Taleb/Druckenmiller/Fisher/Graham/Pabrai/Jhunjhunwala + Valuation

## 注意
- 需OpenAI兼容API Key
- A股需Tushare token
- 单次分析2-5分钟
