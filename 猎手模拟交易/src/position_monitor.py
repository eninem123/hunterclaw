#!/usr/bin/env python3
"""猎手持仓实时监控脚本 v1.1
【BUG修复】2026-05-13:
  - 添加持仓标签(tag)显示
"""
import json
import os
import uuid
import urllib.request
from datetime import datetime, date
from pathlib import Path

# ============ 配置 ============
PORTFOLIO_FILE = "/root/.openclaw/workspace/猎手模拟交易/持仓.json"
STATE_FILE = "/root/.openclaw/workspace/猎手模拟交易/trade_state.json"
DELIVERY_QUEUE = "/root/.openclaw/delivery-queue"
WECHAT_ID = "o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat"
ACCOUNT_ID = "665a0448707a-im-bot"

# 止损止盈参数
STOP_LOSS_PCT = 5.0
TAKE_PROFIT_1_PCT = 10.0
TAKE_PROFIT_2_PCT = 18.0

# ============ 微信通知 ============
def wechat_notify(msg):
    try:
        entry = {
            "id": str(uuid.uuid4()),
            "enqueuedAt": int(datetime.now().timestamp() * 1000),
            "channel": "openclaw-weixin",
            "to": WECHAT_ID,
            "accountId": ACCOUNT_ID,
            "payloads": [{"text": msg, "mediaUrls": [], "replyToTag": False,
                          "replyToCurrent": False, "audioAsVoice": False}],
            "retryCount": 0,
            "lastAttemptAt": None
        }
        path = Path(DELIVERY_QUEUE) / f"{entry['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[通知失败] {e}")
        return False

# ============ 时间校验 ============
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def is_trading_day():
    today = date.today()
    if today.weekday() >= 5:
        return False
    return True

def is_trading_hours():
    now = datetime.now()
    h, m = now.hour, now.minute
    morning = (h == 9 and m >= 30) or (10 <= h <= 11) or (h == 11 and m <= 30)
    afternoon = 13 <= h < 15
    return morning or afternoon

# ============ 获取实时价格 ============
def get_realtime_price(code):
    try:
        prefix = "sz" if code.startswith(("00", "30", "15", "16")) else "sh"
        url = f"https://qt.gtimg.cn/q={prefix}{code}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            text = r.read().decode("gbk")
            parts = text.split("~")
            if len(parts) > 4:
                price = float(parts[3])
                prev_close = float(parts[4])
                change_pct = (price / prev_close - 1) * 100 if prev_close > 0 else 0
                return price, prev_close, change_pct
    except Exception as e:
        print(f"[价格获取失败] {code}: {e}")
    return None, None, None

# ============ 标签转Emoji ============
def tag_to_emoji(tag):
    """【BUG修复】根据持仓标签返回对应emoji"""
    if tag == '主线投资':
        return '🟢'  # 主线投资用绿色
    elif tag == '观察候选':
        return '🟡'  # 观察候选用黄色
    elif tag == '短线投机':
        return '🔴'  # 短线投机组红色
    return ''  # 无标签返回空字符串

# ============ 核心监控逻辑 ============
def monitor_positions():
    if not is_trading_day():
        print(f"📴 非交易日，跳过监控")
        return []
    
    if not is_trading_hours():
        print(f"📴 非交易时段，跳过监控")
        return []
    
    if not os.path.exists(PORTFOLIO_FILE):
        print("[警告] 持仓.json不存在")
        return []
    
    with open(PORTFOLIO_FILE, encoding="utf-8") as f:
        portfolio = json.load(f)
    
    now_str = datetime.now().strftime("%H:%M")
    alerts = []
    urgent_alerts = []
    
    for pos in portfolio.get("positions", []):
        if pos.get("status") != "holding":
            continue
        
        code = pos["code"]
        name = pos["name"]
        entry = pos["entry_price"]
        shares = pos["shares"]
        # 【BUG修复】读取持仓标签
        tag = pos.get("tag", "")
        tag_emoji = tag_to_emoji(tag)
        tag_display = f"{tag_emoji}{tag}" if tag else ""
        
        stop_loss = pos.get("stop_loss", round(entry * (1 - STOP_LOSS_PCT / 100), 2))
        tp1_raw = pos.get("take_profit_1", pos.get("take_profit", round(entry * (1 + TAKE_PROFIT_1_PCT / 100), 2)))
        tp1 = float(re.match(r'^[\d.]+', str(tp1_raw)).group()) if tp1_raw else round(entry * (1 + TAKE_PROFIT_1_PCT / 100), 2)
        tp2_raw = pos.get("take_profit_2", round(entry * (1 + TAKE_PROFIT_2_PCT / 100), 2))
        tp2 = float(re.match(r'^[\d.]+', str(tp2_raw)).group()) if tp2_raw else round(entry * (1 + TAKE_PROFIT_2_PCT / 100), 2)
        
        current_price, prev_close, change_pct = get_realtime_price(code)
        if current_price is None:
            print(f"[跳过] {name}({code}) 价格获取失败")
            continue
        
        pnl_pct = (current_price / entry - 1) * 100
        pnl_val = (current_price - entry) * shares
        value = current_price * shares
        
        # 检查止损（最高优先级：绝对红线）
        if current_price <= stop_loss:
            urgent_msg = (
                f"🚨【止损警报】{now_str}\n"
                f"股票：{name}({code})\n"
                f"当前价：¥{current_price} 🔴 触及止损！\n"
                f"止损价：¥{stop_loss}\n"
                f"买入价：¥{entry} | 浮亏：{pnl_pct:.2f}%\n"
                f"持仓市值：¥{value:,.0f}\n"
                f"标签：{tag_display}\n\n"
                f"⚠️ 建议立即止损！"
            )
            urgent_alerts.append({"type": "STOP_LOSS", "message": urgent_msg, "priority": 1})
        
        # 检查止盈第二目标
        elif current_price >= tp2:
            profit_msg = (
                f"🎯【止盈警报-第二目标】{now_str}\n"
                f"股票：{name}({code})\n"
                f"当前价：¥{current_price} 🟢 触及第二止盈！\n"
                f"止盈2：¥{tp2} | 浮盈：{pnl_pct:.2f}%\n"
                f"买入价：¥{entry} | 浮盈：¥{pnl_val:,.0f}\n"
                f"标签：{tag_display}\n\n"
                f"💰 建议减仓止盈！"
            )
            alerts.append({"type": "TAKE_PROFIT_2", "message": profit_msg, "priority": 2})
        
        # 检查止盈第一目标
        elif current_price >= tp1:
            profit_msg = (
                f"💹【止盈警报-第一目标】{now_str}\n"
                f"股票：{name}({code})\n"
                f"当前价：¥{current_price} 🟡 触及第一止盈！\n"
                f"止盈1：¥{tp1} | 浮盈：{pnl_pct:.2f}%\n"
                f"买入价：¥{entry} | 浮盈：¥{pnl_val:,.0f}\n"
                f"标签：{tag_display}\n\n"
                f"📈 可考虑分批止盈"
            )
            alerts.append({"type": "TAKE_PROFIT_1", "message": profit_msg, "priority": 3})
        
        # 警戒线：距离止损10%以内
        elif current_price <= entry * 0.95:
            warn_pct = (entry - current_price) / entry * 100
            warn_msg = (
                f"⚠️【止损警戒】{now_str}\n"
                f"股票：{name}({code})\n"
                f"当前价：¥{current_price} | 距止损：{warn_pct:.2f}%\n"
                f"止损价：¥{stop_loss} | 浮亏：{pnl_pct:.2f}%\n"
                f"标签：{tag_display}\n\n"
                f"建议：密切监控，随时准备止损"
            )
            alerts.append({"type": "WARNING", "message": warn_msg, "priority": 4})
        
        # 正常状态：打印（使用标签emoji，如果无标签则用盈亏emoji）
        else:
            # 【BUG修复】优先使用标签emoji，否则用盈亏emoji
            if tag_emoji:
                emoji = tag_emoji
            else:
                emoji = "🟢" if pnl_pct >= 0 else "🔴"
            print(f"  {emoji} {name}: ¥{current_price} ({pnl_pct:+.2f}%) | 止损{stop_loss} | 止盈1 {tp1} / 止盈2 {tp2}")
            if tag_display:
                print(f"       标签: {tag_display}")
    
    return urgent_alerts + alerts

# ============ 主流程 ============
def main():
    now = datetime.now()
    weekday = WEEKDAY_NAMES[now.weekday()]
    now_str = now.strftime("%H:%M:%S")
    
    print(f"\n{'='*50}")
    print(f"【持仓监控】{now.strftime('%Y-%m-%d')} {weekday} {now_str}")
    print(f"{'='*50}")
    
    alerts = monitor_positions()
    
    if alerts:
        print(f"\n📬 发送 {len(alerts)} 条告警...")
        for alert in alerts:
            print(f"\n{'--'*20}")
            print(alert["message"])
            wechat_notify(alert["message"])
    else:
        print("\n✅ 持仓状态正常，无告警")
    
    print(f"\n{'='*50}")
    print(f"监控完成: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
