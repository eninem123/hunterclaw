#!/bin/bash
# 猎手模拟交易 - 每日多时报
# 每个交易日 09:30 / 11:30 / 13:00 / 14:00 / 14:30 / 14:55 / 15:05 / 21:00

WORKSPACE="/root/.openclaw/workspace"
HUNTER_DIR="$WORKSPACE/猎手模拟交易"
REPORT_FILE="$HUNTER_DIR/持仓报告.md"
SCRIPT="$HUNTER_DIR/持仓报告_心跳.py"
LOG="$HUNTER_DIR/logs/cron-report.log"
PENDING_DIR="$WORKSPACE/pending-summaries"
MINUTE=$(date +%M)

# 根据时间确定时段标题
if [ "$1" = "09" ]; then
    SLOT="开盘报"
elif [ "$1" = "11" ]; then
    SLOT="午盘报"
elif [ "$1" = "13" ]; then
    SLOT="下午开盘报"
elif [ "$1" = "14" ] && [ "$MINUTE" = "00" ]; then
    SLOT="下午2点报"
elif [ "$1" = "14" ] && [ "$MINUTE" = "30" ]; then
    SLOT="下午2点半报"
elif [ "$1" = "14" ] && [ "$MINUTE" = "55" ]; then
    SLOT="收盘前撤退检查"
elif [ "$1" = "15" ]; then
    SLOT="收盘报"
else
    SLOT="持仓报"
fi

PENDING_FILE="$PENDING_DIR/portfolio-$(date +%Y-%m-%d)-$SLOT.md"

mkdir -p "$PENDING_DIR"
mkdir -p "$HUNTER_DIR/logs"

echo "=== $SLOT $(date '+%Y-%m-%d %H:%M:%S') ===" >> $LOG

cd $HUNTER_DIR
timeout 25 python3 "$SCRIPT" "$SLOT" >> $LOG 2>&1

if [ $? -eq 0 ] && [ -f "$REPORT_FILE" ]; then
    cp "$REPORT_FILE" "$PENDING_FILE"
    echo "$SLOT 已加入待发送: $PENDING_FILE" >> $LOG
else
    echo "$SLOT 报告生成失败" >> $LOG
fi
