#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/.openclaw/workspace/hunter/scripts')
from market_scanner import full_scan, format_report
report = full_scan(closing_mode=False)
report["section"] = "下午开盘"
output = format_report(report)
print(output)
sys.exit(0 if report["verdict"] != "RISK_HIGH" else 1)
