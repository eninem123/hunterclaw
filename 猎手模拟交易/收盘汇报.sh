#!/bin/bash
# 猎手模拟交易 - 每日收盘持仓汇报
# 每个交易日 15:30 自动运行

WORKSPACE="/root/.openclaw/workspace"
HUNTER_DIR="$WORKSPACE/猎手模拟交易"
REPORT_FILE="$HUNTER_DIR/持仓报告.md"
PENDING_FILE="$WORKSPACE/pending-summaries/portfolio-report-$(date +%Y-%m-%d).md"
LOG="$HUNTER_DIR/logs/cron-report.log"

mkdir -p "$HUNTER_DIR/logs"
mkdir -p "$WORKSPACE/pending-summaries"

echo "=== 收盘汇报 $(date '+%Y-%m-%d %H:%M:%S') ===" >> $LOG

# 生成持仓报告
cd $HUNTER_DIR
timeout 25 python3 gen_report.py >> $LOG 2>&1

if [ $? -eq 0 ] && [ -f "$REPORT_FILE" ]; then
    # 复制到待发送目录
    cp "$REPORT_FILE" "$PENDING_FILE"
    echo "报告已生成并加入待发送: $PENDING_FILE" >> $LOG
    
    # 如果是交易日下午，也触发立即发送（不等22:00）
    DAY=$(date +%w)
    HOUR=$(date +%H)
    if [ "$DAY" -ge 1 ] && [ "$DAY" -le 5 ] && [ "$HOUR" -eq 15 ]; then
        echo "交易日下午，立即触发发送..." >> $LOG
        # 通知主会话有报告待发送
        touch "$WORKSPACE/pending-summaries/.trigger-send"
    fi
else
    echo "报告生成失败" >> $LOG
fi

echo "完成 $(date)" >> $LOG
