#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set working directory
os.chdir(os.path.dirname(__file__))

from main import EvolutionTrader
trader = EvolutionTrader()
trader.run_daily_evolution()
