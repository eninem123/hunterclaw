#!/usr/bin/env python3
import sys
import os
os.chdir('/root/.openclaw/workspace/猎手模拟交易/evo-trader')
sys.path.insert(0, '/root/.openclaw/workspace/猎手模拟交易/evo-trader/src')

from main import EvolutionTrader

trader = EvolutionTrader()
report = trader.run_daily_cycle()
print("\n" + report)
