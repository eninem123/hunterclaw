#!/bin/bash
# 猎手模拟交易 - 每日多时报
# 每个交易日 09:30 / 11:30 / 15:05 / 21:00 自动运行

WORKSPACE="/root/.openclaw/workspace"
HUNTER_DIR="$WORKSPACE/猎手模拟交易"
REPORT_FILE="$HUNTER_DIR/持仓报告.md"
LOG="$HUNTER_DIR/logs/cron-report.log"

# 根据时段生成不同文件名
HOUR=$(date +%H)
if [ "$HOUR" = "09" ]; then
    SLOT="开盘"
elif [ "$HOUR" = "11" ]; then
    SLOT="午盘"
elif [ "$HOUR" = "15" ]; then
    SLOT="收盘"
else
    SLOT="晚间"
fi

PENDING_FILE="$WORKSPACE/pending-summaries/portfolio-$(date +%Y-%m-%d)-$SLOT.md"

mkdir -p "$WORKSPACE/pending-summaries"
mkdir -p "$HUNTER_DIR/logs"

echo "=== $SLOT汇报 $(date '+%Y-%m-%d %H:%M:%S') ===" >> $LOG

# 生成持仓报告
cd $HUNTER_DIR
timeout 25 python3 gen_report.py >> $LOG 2>&1

if [ $? -eq 0 ] && [ -f "$REPORT_FILE" ]; then
    # 在文件头部加时段标签
    {
        echo "# 【$SLOT汇报】猎手模拟交易持仓报告"
        echo ""
        cat "$REPORT_FILE"
    } > "$PENDING_FILE"
    echo "$SLOT报告已生成: $PENDING_FILE" >> $LOG
else
    echo "报告生成失败" >> $LOG
fi
