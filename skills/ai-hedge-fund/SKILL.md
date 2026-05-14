---
name: ai-hedge-fund
description: "AI对冲基金：14个投资大师Agent辩论框架，支持A股/美股多维度分析"
version: 1.0.0
---

# AI Hedge Fund

多Agent投资辩论框架，模拟14位投资大师视角，多轮辩论达成交易共识。

## 使用
```bash
cd /root/ai-hedge-fund
python -m src.main --ticker 300232 --start 2026-01-01 --end 2026-05-01
```

## Agents
Damodaran/Graham/Ackman/Wood/Munger/Burry/Pabrai/Taleb/Lynch/Fisher/Jhunjhunwala/Druckenmiller/Buffett + Valuation

## 注意
- 需OpenAI兼容API Key
- 与TradingAgents功能类似，建议用TradingAgents(更新更活跃)
