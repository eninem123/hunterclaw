#!/usr/bin/env python3
import sys
import json
from datetime import date

def is_trading_day(check_date=None):
    if check_date is None:
        target_date = date.today()
    elif isinstance(check_date, str):
        target_date = date.fromisoformat(check_date)
    else:
        target_date = check_date
    
    if target_date.weekday() >= 5:
        return False
    
    try:
        import akshare as ak
        import pandas as pd
        trade_cal = ak.tool_trade_date_hist_sina()
        trade_dates = set(pd.to_datetime(trade_cal['trade_date']).dt.date)
        return target_date in trade_dates
    except Exception as e:
        print(f"[WARN] Failed to fetch trade calendar: {e}", file=sys.stderr)
        return True

def main():
    if len(sys.argv) > 1:
        target_date_str = sys.argv[1]
    else:
        target_date_str = date.today().isoformat()
    
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        print(json.dumps({"success": False, "error": "Invalid date format"}))
        sys.exit(1)
    
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today_label = weekday_names[target_date.weekday()]
    is_trade = is_trading_day(target_date)
    
    result = {"success": True, "date": target_date_str, "weekday": today_label, "is_trading_day": is_trade}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
