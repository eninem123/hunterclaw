#!/bin/bash
# Agent健康检查 - 每10分钟 (v2: 5/28增强版)
python3 -c "
import sqlite3,redis,time,subprocess,urllib.request

r=redis.Redis(host=\"localhost\",port=6379,decode_responses=True)
db=sqlite3.connect(\"/opt/agent_state/agent.db\")

# 1. 检查xuequ-api
try:
    urllib.request.urlopen(\"http://localhost:8890/\",timeout=5)
    r.set(\"service:xuequ-api\",\"up\")
except:
    r.set(\"service:xuequ-api\",\"down\")
    subprocess.run([\"systemctl\",\"restart\",\"xuequ-api\"])
    r.set(\"service:xuequ-api\",\"restarted\")

# 2. 检查OpenClaw Gateway
try:
    resp=urllib.request.urlopen(\"http://localhost:10535/health\",timeout=5)
    if b\"ok\" in resp.read():
        r.set(\"service:openclaw-gateway\",\"up\")
    else:
        r.set(\"service:openclaw-gateway\",\"degraded\")
except:
    r.set(\"service:openclaw-gateway\",\"down\")
    # 不自动重启gateway，避免杀SSH

# 3. 检查Hermes进程
result=subprocess.run([\"pgrep\",\"-f\",\"hermes-agent\"],capture_output=True,text=True)
if result.stdout.strip():
    r.set(\"service:hermes\",\"up\")
else:
    r.set(\"service:hermes\",\"down\")

# 4. 检查OpenClaw Agent进程
result=subprocess.run([\"pgrep\",\"-f\",\"openclaw-agent\"],capture_output=True,text=True)
if result.stdout.strip():
    r.set(\"service:openclaw-agent\",\"up\")
else:
    r.set(\"service:openclaw-agent\",\"down\")

# 5. 检查Redis本身
r.ping()

# 6. 磁盘检查
import os
stat=os.statvfs(\"/\")
disk_pct=int(stat.f_blocks-stat.f_bfree)*100//stat.f_blocks
r.set(\"system:disk_pct\",str(disk_pct))
if disk_pct>85:
    print(f\"WARNING: disk at {disk_pct}%\")

print(f\"healthcheck OK {time.strftime(\"%H:%M\")} disk={disk_pct}%\")
"
