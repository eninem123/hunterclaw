#!/bin/bash
cd /root/.openclaw/workspace/evo-trader
python3 src/main.py --daily >> logs/evolution/$(date +\%Y\%m\%d).log 2>&1
