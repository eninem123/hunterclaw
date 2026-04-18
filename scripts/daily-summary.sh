#!/bin/bash
# OpenClaw + Hermes 每日总结脚本 - 22:00 执行
# 汇总两个agent的工作，写入 pending 目录，由 heartbeat 发送

WORKSPACE="/root/.openclaw/workspace"
HERMES_DIR="/root/.hermes"
TODAY=$(date +%Y-%m-%d)
HUNTER_DIR="$WORKSPACE/猎手模拟交易"
MEMORY_FILE="$WORKSPACE/memory/$TODAY.md"
PENDING_DIR="$WORKSPACE/pending-summaries"
SUMMARY_FILE="$PENDING_DIR/$TODAY-summary.md"

mkdir -p "$PENDING_DIR"

# OpenClaw 今日内容
if [ -f "$MEMORY_FILE" ]; then
  MEMORY_CONTENT=$(cat "$MEMORY_FILE")
else
  MEMORY_CONTENT="（今日暂无内存记录）"
fi

GIT_COMMITS=$(cd $WORKSPACE && git log --oneline --since="00:00" --until="23:59" 2>/dev/null | head -10 || echo "（无git提交）")

# Hermes 今日内容
if [ -f "$HUNTER_DIR/推演结果.md" ]; then
  HUNTER_CONTENT=$(cat "$HUNTER_DIR/推演结果.md")
else
  HUNTER_CONTENT="（今日暂无推演结果）"
fi

if [ -f "$HUNTER_DIR/策略优化建议.md" ]; then
  STRATEGY_CONTENT=$(tail -30 "$HUNTER_DIR/策略优化建议.md")
else
  STRATEGY_CONTENT="（今日暂无策略分析）"
fi

# 组合总结
cat > $SUMMARY_FILE << EOF
🌙 【每日工作总结】$TODAY
━━━━━━━━━━━━━━━━━━━━

🦞 【OpenClaw 工作】
$MEMORY_CONTENT

📊 Git提交：
$GIT_COMMITS

━━━━━━━━━━━━━━━━━━━━

🔮 【Hermes 工作】
📊 猎手模拟交易：
$HUNTER_CONTENT

📈 策略优化：
$STRATEGY_CONTENT

━━━━━━━━━━━━━━━━━━━━
自动生成 $(date "+%H:%M")
EOF

echo "Summary written to $SUMMARY_FILE at $(date)" >> $WORKSPACE/logs/daily-summary.log
