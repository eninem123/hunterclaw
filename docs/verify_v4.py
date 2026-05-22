#!/usr/bin/env python3
"""验证v4.0模块功能完整性"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/mcp-data-server')

# 1. auto_trade_v2.py 关键符号
from src.auto_trade_v2 import (
    execute_trading_cycle, calc_panic_index, calc_market_temperature,
    calc_position_size, should_buy_v4, check_market_confirmation,
    check_loss_graded, check_take_profit_graded,
    MAX_BUYS_PER_DAY, MAX_POSITION_PCT, MAX_STOCKS_TOTAL,
    LOSS_ALERT_PCT, LOSS_HALVE_PCT, LOSS_STOP_PCT, LOSS_FORCE_PCT,
    TEMPERATURE_MATRIX, __version__
)
assert MAX_BUYS_PER_DAY == 2, f"R05: 期望2次, 实际{MAX_BUYS_PER_DAY}"
assert MAX_POSITION_PCT == 20, f"R06: 期望20%, 实际{MAX_POSITION_PCT}"
assert MAX_STOCKS_TOTAL == 4, f"R21: 期望4只, 实际{MAX_STOCKS_TOTAL}"
assert len(TEMPERATURE_MATRIX) == 6, f"温度矩阵: 期望6档, 实际{len(TEMPERATURE_MATRIX)}"
assert __version__ == "4.0.0"
print("✅ auto_trade_v2.py: 关键常量验证通过")

# 2. 恐慌指数计算
indices = [{"name": "上证指数", "pct": -1.5}, {"name": "沪深300", "pct": -1.2}]
breadth = {"up_indices": 2, "down_indices": 4}
panic = calc_panic_index(indices, breadth, [])
assert "panic_index" in panic
assert 0 <= panic["panic_index"] <= 100
assert panic["level"] in ("SAFE", "CAUTION", "COLD", "FREEZE", "PANIC")
print(f"✅ 恐慌指数: {panic['panic_index']} ({panic['label']})")

# 3. 温度计算
temp, pidx, wchg = calc_market_temperature(indices)
assert 0 <= temp <= 100
assert 0 <= pidx <= 100
print(f"✅ 市场温度: {temp}℃ 恐慌:{pidx} 加权:{wchg:+.2f}%")

# 4. 仓位矩阵
state = {"market_temperature": 30, "panic_index": 40}
pos, label = calc_position_size(state, {"cash": 100000, "positions": []})
assert pos <= 30
print(f"✅ 温度30℃: 目标仓位{pos}% ({label})")

# 5. data_analyzer_v2.py 增强方法
from src.data_analyzer_v2 import DataAnalyzerV2, AnalysisResult, TechnicalIndicators, SignalStrength, MarketSentiment
analyzer = DataAnalyzerV2()
result = AnalysisResult(
    code="000001", name="测试", price=10, chg_pct=-2,
    trend=None, indicators=TechnicalIndicators(),
    signal=SignalStrength.STRONG_BUY, score=80
)
enhanced = analyzer.augment_with_market_context(result, market_temperature=20, panic_index=15)
assert enhanced.signal == SignalStrength.HOLD, f"冰封期信号应降级, 仍为{enhanced.signal}"
print(f"✅ 冰封期信号降级: STRONG_BUY → {enhanced.signal.value} (score={enhanced.score})")

# 6. market_scanner.py 新函数
sys.path.insert(0, '/root/.openclaw/workspace/hunter/scripts')
import importlib
scanner = importlib.import_module('market_scanner')
panic_data = scanner.calculate_panic_index({"indices": [{"pct": -2.5}]}, {"up_indices": 1, "down_indices": 5}, [])
assert "panic_index" in panic_data
v10_w = scanner.check_v10_panic_ban(15)
assert len(v10_w) > 0, "恐慌<25应有警告"
print(f"✅ V10恐慌禁止: {len(v10_w)}条警告")

# 7. MCP main.py 新工具
mcp_main = importlib.import_module('src.main', package=None)
mcp_src = importlib.import_module('mcp-data-server.src.main')
tools = mcp_main.create_mcp_tools()
tool_names = {t["name"] for t in tools}
assert "get_panic_index" in tool_names, f"缺少get_panic_index, 有{tool_names}"
assert "get_market_timing" in tool_names, f"缺少get_market_timing"
assert "get_v4_rules_summary" in tool_names, f"缺少get_v4_rules_summary"
print(f"✅ MCP新工具: panic/timing/rules三个就绪")

print(f"\n{'='*50}")
print("🎉 全部v4.0模块验证通过!")
print(f"{'='*50}")
