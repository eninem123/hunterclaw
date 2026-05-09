#!/bin/bash
QUERY="$1"
if [ -z "$QUERY" ]; then
    echo "用法: ./ask_hermes.sh \"你的问题\""
    exit 1
fi
RESPONSE=$(curl -s -X POST http://localhost:8642/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$QUERY\", \"stream\": false}" \
  --max-time 30)
if [ $? -eq 0 ]; then
    echo "$RESPONSE"
    echo "[$(date '+%Y-%m-%d %H:%M')] Q: $QUERY" >> ~/.openclaw/workspace/shared/hermes_log.md
    echo "$RESPONSE" >> ~/.openclaw/workspace/shared/hermes_log.md
    echo "---" >> ~/.openclaw/workspace/shared/hermes_log.md
else
    echo "Hermes API调用失败"
fi
