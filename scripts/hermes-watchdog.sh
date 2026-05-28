#!/bin/bash
# Watchdog v3 - 只守护2个服务: 龙虾openclaw + 爱马仕
LOCK=/tmp/hermes-watchdog.lock
[ -f "$LOCK" ] && kill -0 $(cat $LOCK) 2>/dev/null && exit 0
echo $$ > $LOCK; trap "rm -f $LOCK" EXIT
LOG=/tmp/hermes-watchdog.log
OC=$(pgrep -c -f "openclaw.*gateway.*10535" 2>/dev/null || echo 0)
[ "$OC" -eq 0 ] && { echo "[$(date)] openclaw挂了" >> $LOG; cd /root && nohup openclaw gateway --port 10535 &>/tmp/ocgw.log &; }
HC=$(pgrep -c -f "/root/hermes-agent/venv/bin/python -m hermes_cli.main gateway" 2>/dev/null || echo 0)
[ "$HC" -eq 0 ] && { echo "[$(date)] 爱马仕挂了" >> $LOG; cd /root/hermes-agent && nohup ./venv/bin/python -m hermes_cli.main gateway run --replace &>/tmp/hermes.log &; }
echo "[$(date)] wd3: oc=$OC h=$HC" >> $LOG
