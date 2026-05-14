#!/bin/bash
# 强制同步记忆到 main.sqlite
LOG_FILE="/root/.openclaw/logs/memory_sync.log"
SQLITE_FILE="/root/.openclaw/memory/main.sqlite"

echo "==== $(date) ====" >> "$LOG_FILE"

python3 -c "
import sqlite3
import os
sqlite_file = \"$SQLITE_FILE\"
try:
    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()
    cursor.execute(\"SELECT COUNT(*) FROM files\")
    print(f\"Files: {cursor.fetchone()[0]}\")
    cursor.execute(\"SELECT COUNT(*) FROM chunks\")
    print(f\"Chunks: {cursor.fetchone()[0]}\")
    cursor.execute(\"PRAGMA wal_checkpoint(TRUNCATE)\")
    print(f\"Checkpoint: {cursor.fetchone()}\")
    conn.close()
except Exception as e:
    print(f\"Error: {e}\")
" >> "$LOG_FILE" 2>&1

touch "$SQLITE_FILE"
echo "Sync complete at $(date)" >> "$LOG_FILE"
