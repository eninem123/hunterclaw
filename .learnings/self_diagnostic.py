#!/usr/bin/env python3
"""
猎手系统每日自检 - 盘前诊断
每天 09:25 自动运行，检查各项系统状态
"""
import os
import json
import sys
import subprocess
import requests
from datetime import datetime

WORKSPACE = "/root/.openclaw/workspace"
LOG_DIR = f"{WORKSPACE}/.learnings"
os.makedirs(LOG_DIR, exist_ok=True)

PASS = "✅"
FAIL = "❌"
REPORT = []

def log(msg):
    print(f"[自检] {msg}")

def check(name, fn):
    try:
        ok, detail = fn()
        status = PASS if ok else FAIL
        REPORT.append(f"{status} {name}: {detail}")
        return ok
    except Exception as e:
        REPORT.append(f"{FAIL} {name}: 异常 {type(e).__name__}: {e}")
        return False

# ========== 检查项 ==========

def check_signal_queue():
    """信号队列：无 pending 错误信号"""
    path = "/root/.hermes/猎手模拟交易/信号队列"
    if not os.path.exists(path):
        return False, "信号队列文件不存在"
    with open(path) as f:
        lines = [l for l in f if '"status": "pending"' in l and not l.strip().startswith('#')]
    return len(lines) == 0, f"pending信号 {len(lines)} 条"

def check_pending_confirm():
    """待确认目录：无过期错误信号"""
    path = "/root/.hermes/猎手模拟交易/pending_confirm"
    if not os.path.exists(path):
        return True, "目录不存在（正常）"
    files = [f for f in os.listdir(path) if f.endswith('.json')]
    return len(files) == 0, f"待确认文件 {len(files)} 个"

def check_portfolio_data():
    """持仓数据：JSON 格式正常"""
    path = f"{WORKSPACE}/猎手模拟交易/持仓.json"
    if not os.path.exists(path):
        return False, "持仓文件不存在"
    with open(path) as f:
        data = json.load(f)
    cash = data.get('cash', 0)
    positions = data.get('positions', [])
    return True, f"现金 {cash} | 持仓 {len(positions)} 只"

def check_data_source():
    """数据源：新浪财经 API 可用"""
    try:
        r = requests.get(
            "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData",
            params={"symbol": "sz000001", "scale": "240", "datalen": "1", "ma": "no"},
            timeout=5
        )
        ok = r.status_code == 200 and len(r.json()) > 0
        return ok, "正常" if ok else f"返回异常 {r.status_code}"
    except Exception as e:
        return False, f"API异常 {type(e).__name__}"

def check_evo_cache():
    """进化系统：数据缓存正常"""
    cache_dir = f"{WORKSPACE}/猎手模拟交易/evo-trader/data/quotes"
    if not os.path.exists(cache_dir):
        return False, "缓存目录不存在"
    files = [f for f in os.listdir(cache_dir) if f.endswith('.csv')]
    now = datetime.now().timestamp()
    recent = [f for f in files if now - os.path.getmtime(os.path.join(cache_dir, f)) < 3*86400]
    return len(recent) > 0, f"最近缓存 {len(recent)} 个文件"

def check_cron_jobs():
    """Cron 任务：关键任务存在"""
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    cron_content = result.stdout or ""
    checks = [
        ("进化系统", "run_evolve.sh" in cron_content),
        ("猎手信号", "hunter_signal_executor" in cron_content),
        ("每日学习", "daily_push" in cron_content),
        ("自我诊断", "self_diagnostic" in cron_content),
    ]
    failed = [n for n, ok in checks if not ok]
    return len(failed) == 0, f"{'全部正常' if not failed else '缺失: ' + ', '.join(failed)}"

def check_signal_validation():
    """信号校验：四重门逻辑正常"""
    sys.path.insert(0, '/root/.hermes/hermes-agent/scripts')
    try:
        from signal_writer import pre_write_validation
        # 正常信号应该通过
        ok, _ = pre_write_validation('buy', '000001', 11.0, 1000)
        # 错误信号应该被拦截
        bad_ok, bad_err = pre_write_validation('buy', '600519', 1800.0, 100)
        return ok and not bad_ok, "四重门正常" if (ok and not bad_ok) else f"校验失效"
    except Exception as e:
        return False, f"导入异常 {e}"

# ========== 执行 ==========

if __name__ == "__main__":
    print("=" * 50)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"猎手系统盘前自检 {now}")
    print("=" * 50)

    checks = [
        ("信号队列无pending", check_signal_queue),
        ("待确认目录无过期", check_pending_confirm),
        ("持仓数据正常", check_portfolio_data),
        ("新浪API可用", check_data_source),
        ("进化缓存正常", check_evo_cache),
        ("Cron任务完整", check_cron_jobs),
        ("信号校验四重门", check_signal_validation),
    ]

    results = []
    for name, fn in checks:
        results.append(check(name, fn))

    for r in REPORT:
        print(r)

    passed = sum(results)
    total = len(results)
    print()
    print(f"📊 自检结果: {passed}/{total} 通过")

    # 写日志
    log_file = f"{LOG_DIR}/self_diagnostic.log"
    with open(log_file, 'a') as f:
        f.write(f"\n=== {datetime.now()} ===\n")
        f.write(f"结果: {passed}/{total} 通过\n")
        f.write('\n'.join(REPORT) + '\n')

    if passed < total:
        print(f"{FAIL} 有 {total - passed} 项失败，请检查")
        sys.exit(1)
    else:
        print(f"{PASS} 所有检查通过")
        sys.exit(0)
