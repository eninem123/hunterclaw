#!/usr/bin/env python3
"""福田教育局学区页面定时监控 T16
每日检查福田教育局网站学区政策更新，变化时通知
"""
import urllib.request
import json
import os
import hashlib
from datetime import datetime

STATE_FILE = '/opt/agent_state/data/xuequ_monitor_state.json'
LOG_FILE = '/opt/agent_state/data/xuequ_monitor.log'
URLS = [
    'https://www.szftedu.cn/jyfw/jyxf/zxzs/',
    'https://www.szftedu.cn/jyfw/jyxf/xxzs/',
]

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def fetch_hash(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        content = resp.read()
        return hashlib.md5(content).hexdigest()
    except Exception as e:
        log(f'FETCH ERROR {url}: {e}')
        return None

def main():
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
    
    changed = []
    for url in URLS:
        h = fetch_hash(url)
        if h is None:
            continue
        old = state.get(url)
        if old and old != h:
            changed.append(url)
            log(f'CHANGED: {url}')
        state[url] = h
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    if changed:
        log(f'ALERT: {len(changed)} page(s) changed! Check: ' + ' | '.join(changed))
    else:
        log('OK: no changes detected')

if __name__ == '__main__':
    main()
