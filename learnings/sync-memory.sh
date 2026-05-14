#!/bin/bash
# IMA学习结果同步到MEMORY.md
# 将IMA获取的知识同步到猎手系统

SYNC_FILE="/root/.openclaw/workspace/learnings/ima-learner.sh"
MEMORY_FILE="/root/.openclaw/memory/MEMORY.md"

# 添加同步标记
echo '' >> "$MEMORY_FILE"
echo '--- IMA知识库学习同步 ---' >> "$MEMORY_FILE"
echo "同步时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$MEMORY_FILE"
echo '来源: 熊猫交易学社、行业报告' >> "$MEMORY_FILE"
