#!/usr/bin/env python3
import sys, json
from datetime import datetime, date
try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed"}, ensure_ascii=False))
    sys.exit(1)
def check(target_date=None):
    if target_date is None:
        target_date = date.today()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    try:
        df = ak.tool_trade_date_hist_sina()
        df['trade_date'] = __import__('pandas').to_datetime(df['trade_date'])
        dates = set(df['trade_date'].dt.date.tolist())
        is_t = target_date in dates
        past = [d for d in dates if d < target_date]
        fut = [d for d in dates if d > target_date]
        return {"date": str(target_date), "is_trading_day": is_t, "previous_trading_day": str(max(past)) if past else None, "next_trading_day": str(min(fut)) if fut else None}
    except Exception as e:
        return {"error": str(e)}
if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(check(t), ensure_ascii=False, indent=2))
