"""
猎手系统 时间工具
用于定时任务调度、交易时段判断、下一个时间点计算
"""

import time
import datetime
from typing import Optional
from croniter import croniter


# ══════════════════════════════════════════════════════════
# 1. 交易时段判断
# ══════════════════════════════════════════════════════════

TRADING_RULES = {
    "open_auction": (9, 15, 9, 25),      # 开盘竞价 9:15-9:25
    "morning_session": (9, 30, 11, 30),   # 上午 9:30-11:30
    "lunch_break": (11, 30, 13, 0),      # 午休 11:30-13:00
    "afternoon_session": (13, 0, 15, 0), # 下午 13:00-15:00
    "closing_auction": (14, 54, 15, 0),   # 收盘竞价 14:54-15:00
}


def is_trading_day(date: datetime.date = None) -> bool:
    """判断是否为交易日（排除周末和节假日）"""
    if date is None:
        date = datetime.date.today()
    # 简单判断：周六/周日
    if date.weekday() >= 5:
        return False
    return True


def is_trading_time(dt: datetime.datetime = None) -> bool:
    """判断当前是否在交易时段内"""
    if dt is None:
        dt = datetime.datetime.now()
    if not is_trading_day(dt.date()):
        return False

    h, m = dt.hour, dt.minute
    # 9:30-11:30 上午
    if 9 <= h < 11 or (h == 11 and m <= 30):
        return True
    # 13:00-15:00 下午
    if 13 <= h < 15:
        return True
    return False


def get_trading_phase(dt: datetime.datetime = None) -> str:
    """获取当前交易阶段"""
    if dt is None:
        dt = datetime.datetime.now()
    if not is_trading_day(dt.date()):
        return "非交易日"

    h, m = dt.hour, dt.minute

    if h < 9:
        return "盘前"
    if h == 9 and m < 15:
        return "开盘竞价"
    if h == 9 and 15 <= m < 30:
        return "开盘竞价"
    if (h == 9 and m >= 30) or (h == 10) or (h == 11 and m <= 30):
        return "上午交易"
    if h == 11 and m > 30:
        return "午间休市"
    if h == 12:
        return "午间休市"
    if h == 13:
        return "下午交易"
    if h == 14 and m < 54:
        return "下午交易"
    if h == 14 and m >= 54:
        return "收盘竞价"
    if h == 15:
        return "收盘"
    if h > 15:
        return "盘后"

    return "未知"


def seconds_to_trading_time(target_h: int, target_m: int, dt: datetime.datetime = None) -> int:
    """计算距离目标时间还有多少秒（仅计算交易时段）"""
    if dt is None:
        dt = datetime.datetime.now()
    now = dt.replace(second=0, microsecond=0)
    target = now.replace(hour=target_h, minute=target_m)
    if target <= now:
        target += datetime.timedelta(days=1)
    return int((target - now).total_seconds())


def time_until_open(dt: datetime.datetime = None) -> str:
    """距离下次开盘还有多久"""
    if dt is None:
        dt = datetime.datetime.now()
    if is_trading_time(dt):
        return "已开盘"

    h = dt.hour
    if h < 9:
        return f"{9-dt.hour}小时{30-dt.minute}分后开盘"
    if h < 13:
        return f"{13-h}小时{30-m}分后下午开盘" if 'm' in dir() else f"{13-h}小时后开盘"
    # 已过下午开盘
    next_open = dt.replace(hour=9, minute=30, second=0)
    if h >= 15:
        next_open += datetime.timedelta(days=1)
        # 跳过周末
        while next_open.weekday() >= 5:
            next_open += datetime.timedelta(days=1)
    delta = next_open - dt
    hours = int(delta.total_seconds() / 3600)
    mins = int((delta.total_seconds() % 3600) / 60)
    return f"{hours}小时{mins}分后开盘"


# ══════════════════════════════════════════════════════════
# 2. Cron解析工具
# ══════════════════════════════════════════════════════════

def parse_cron_next(cron_expr: str, base_time: datetime.datetime = None) -> datetime.datetime:
    """解析cron表达式，返回下一个执行时间"""
    if base_time is None:
        base_time = datetime.datetime.now()
    iter = croniter(cron_expr, base_time)
    return iter.get_next(datetime.datetime)


def parse_cron_prev(cron_expr: str, base_time: datetime.datetime = None) -> datetime.datetime:
    """解析cron表达式，返回上一次执行时间"""
    if base_time is None:
        base_time = datetime.datetime.now()
    iter = croniter(cron_expr, base_time)
    return iter.get_prev(datetime.datetime)


def format_timedelta(delta: datetime.timedelta) -> str:
    """格式化时间差为可读字符串"""
    total = int(delta.total_seconds())
    if total < 60:
        return f"{total}秒"
    if total < 3600:
        return f"{total//60}分{total%60}秒"
    hours = total // 3600
    mins = (total % 3600) // 60
    return f"{hours}小时{mins}分"


# ══════════════════════════════════════════════════════════
# 3. 常用时间工具
# ══════════════════════════════════════════════════════════

def now(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """当前时间字符串"""
    return datetime.datetime.now().strftime(fmt)


def today_date() -> str:
    """今日日期字符串"""
    return datetime.date.today().isoformat()


def is_trading_day_check() -> dict:
    """交易日检查，返回状态字典"""
    today = datetime.date.today()
    now_dt = datetime.datetime.now()
    return {
        "date": today.isoformat(),
        "is_trading_day": is_trading_day(today),
        "weekday": today.strftime("%A"),
        "trading_phase": get_trading_phase(now_dt),
        "is_trading_time": is_trading_time(now_dt),
        "time_until_open": time_until_open(now_dt),
    }


if __name__ == "__main__":
    print("=== 猎手时间工具 ===")
    print()
    print("当前时间:", now())
    print("今日:", today_date())
    print()

    status = is_trading_day_check()
    for k, v in status.items():
        print(f"  {k}: {v}")

    print()
    print("=== Cron测试 ===")
    cron_tests = [
        "30 14 * * 1-5",    # 每周一至五14:30
        "0 9,14 * * 1-5",   # 每周一至五9:00和14:00
        "55 14 * * 1-5",    # 每天14:55
        "40 15 * * 1-5",    # 每天15:40
    ]
    for c in cron_tests:
        next_run = parse_cron_next(c)
        print(f"  {c} → 下次执行: {next_run.strftime('%Y-%m-%d %H:%M')}")