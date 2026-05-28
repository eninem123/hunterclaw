#!/bin/bash
# OpenClaw watchdog v3 - safe kill + dual config check + git protect
cd /root/.openclaw

RESULT=$(python3 -c "
import json
changed = []

# Check openclaw.json
with open('openclaw.json') as f:
    c = json.load(f)
if c.get('agents',{}).get('defaults',{}).get('model',{}).get('primary','') != 'mimo/mimo-v2.5':
    c['agents']['defaults']['model']['primary'] = 'mimo/mimo-v2.5'
    changed.append('openclaw.json:primary')
if c.get('agents',{}).get('defaults',{}).get('model',{}).get('fallbacks',[]) not in (['mimo/mimo-v2-flash'],['mimo/mimo-v2-flash','mimo/mimo-v2.5','custom_zhipu/glm-4.7']):
    c['agents']['defaults']['model']['fallbacks'] = ['mimo/mimo-v2-flash','mimo/mimo-v2.5','custom_zhipu/glm-4.7']
    changed.append('openclaw.json:fallbacks')
if 'deepseek' in c.get('models',{}).get('providers',{}):
    del c['models']['providers']['deepseek']
    changed.append('openclaw.json:deepseek_removed')
if changed:
    with open('openclaw.json','w') as f:
        json.dump(c, f, indent=2, ensure_ascii=False)

# Check agents/main/agent/models.json
mpath = 'agents/main/agent/models.json'
try:
    with open(mpath) as f:
        m = json.load(f)
    if 'deepseek' in m.get('providers',{}):
        del m['providers']['deepseek']
        changed.append('models.json:deepseek_removed')
    if 'mimo' in m.get('providers',{}):
        old_url = m['providers']['mimo'].get('baseUrl','')
        if 'token-plan' not in old_url:
            m['providers']['mimo']['baseUrl'] = 'https://token-plan-cn.xiaomimimo.com/v1'
            m['providers']['mimo']['apiKey'] = 'tp-czmhb86n2j7nlx1b717du0e76khpm558ntajjl2158j2u084'
            changed.append('models.json:mimo_url_fixed')
    # Ensure NO other provider references deepseek
    for key in list(m.get('providers',{}).keys()):
        if 'deepseek' in key.lower():
            del m['providers'][key]
            changed.append(f'models.json:{key}_removed')
    if changed and any('models.json' in x for x in changed):
        with open(mpath,'w') as f:
            json.dump(m, f, indent=2, ensure_ascii=False)
except Exception as e:
    changed.append(f'models.json:ERROR:{e}')

if changed:
    print('FIXED:' + ','.join(changed))
else:
    print('OK')
")

if [[ "$RESULT" == FIXED* ]]; then
    echo "[$(date)] watchdog: $RESULT" >> /tmp/openclaw-watchdog.log
    # v3: safe kill - get exact PID, don't use pkill which may kill SSH
    PID=$(pgrep -f 'openclaw.*gateway.*10535' 2>/dev/null | head -1)
    if [[ -n "$PID" ]]; then
        # Kill the process tree under this PID only
        kill -9 "$PID" 2>/dev/null
        # Wait for process to die
        sleep 2
        # Verify it's dead
        if kill -0 "$PID" 2>/dev/null; then
            echo "[$(date)] watchdog: PID $PID still alive, sending SIGKILL to group" >> /tmp/openclaw-watchdog.log
            kill -9 -"$(ps -o pgid= -p "$PID" | tr -d ' ')" 2>/dev/null || true
            sleep 2
        fi
    fi
    # Restart
    nohup openclaw gateway --port 10535 >> /tmp/openclaw-gateway.log 2>&1 &
    NEW_PID=$!
    echo "[$(date)] watchdog: openclaw restarted as PID $NEW_PID" >> /tmp/openclaw-watchdog.log
    # Verify new process is alive
    sleep 3
    if kill -0 "$NEW_PID" 2>/dev/null; then
        echo "[$(date)] watchdog: new process alive" >> /tmp/openclaw-watchdog.log
    else
        echo "[$(date)] watchdog: WARNING new process died immediately" >> /tmp/openclaw-watchdog.log
    fi
fi

# Also check: is openclaw gateway running at all? If not, start it.
PID=$(pgrep -f 'openclaw.*gateway.*10535' 2>/dev/null | head -1)
if [[ -z "$PID" ]]; then
    nohup openclaw gateway --port 10535 >> /tmp/openclaw-gateway.log 2>&1 &
    echo "[$(date)] watchdog: openclaw was dead, started new process" >> /tmp/openclaw-watchdog.log
fi
