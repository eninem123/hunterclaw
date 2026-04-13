#!/bin/bash
# 猎手模拟交易 - 每日多时报 + 收盘触发Hermes策略优化
# 每个交易日 09:30 / 11:30 / 15:05 / 21:00 自动运行

WORKSPACE="/root/.openclaw/workspace"
HUNTER_DIR="$WORKSPACE/猎手模拟交易"
REPORT_FILE="$HUNTER_DIR/持仓报告.md"
SCRIPT="$HUNTER_DIR/持仓报告_心跳.py"
LOG="$HUNTER_DIR/logs/cron-report.log"
PENDING_DIR="$WORKSPACE/pending-summaries"

# 根据时段确定标题
HOUR=$(date +%H)
if [ "$HOUR" = "09" ]; then
    SLOT="开盘报"
elif [ "$HOUR" = "11" ]; then
    SLOT="午盘报"
elif [ "$HOUR" = "15" ]; then
    SLOT="收盘报"
    # 收盘时同步触发 Hermes 策略优化
    TRIGGER_HERMES=1
else
    SLOT="持仓报"
fi

PENDING_FILE="$PENDING_DIR/portfolio-$(date +%Y-%m-%d)-$SLOT.md"

mkdir -p "$PENDING_DIR"
mkdir -p "$HUNTER_DIR/logs"

echo "=== $SLOT $(date '+%Y-%m-%d %H:%M:%S') ===" >> $LOG

# 生成持仓报告
cd $HUNTER_DIR
timeout 25 python3 "$SCRIPT" "$SLOT" >> $LOG 2>&1

if [ $? -eq 0 ] && [ -f "$REPORT_FILE" ]; then
    cp "$REPORT_FILE" "$PENDING_FILE"
    echo "$SLOT 已生成并加入待发送" >> $LOG
else
    echo "$SLOT 报告生成失败" >> $LOG
fi

# 收盘时同步触发 Hermes 策略优化
if [ "$TRIGGER_HERMES" = "1" ]; then
    echo "收盘触发 Hermes 策略优化..." >> $LOG
    # Hermes 策略优化脚本由其自身 cron 在 15:30 触发，这里只记录
fi
