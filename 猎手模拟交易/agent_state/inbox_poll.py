#!/usr/bin/env python3
import json, subprocess, sys, os
from datetime import datetime

sys.path.insert(0, "/tmp")
import agent_comm as ac

POLL_LOG = "/tmp/inbox_poll.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(POLL_LOG, "a") as f:
        f.write(line + chr(10))

def trigger_lobster(pending_tasks):
    try:
        for t in pending_tasks[:3]:
            tid = t[0] if isinstance(t, (list, tuple)) else t.get("task_id", t)
            try:
                ac.task_update(tid, "in_progress")
                log(f"LOBSTER: marked {tid} in_progress")
            except Exception as e:
                log(f"LOBSTER: task_update {tid} error: {e}")
    except Exception as e:
        log(f"LOBSTER: trigger error: {e}")

def trigger_hermes(pending_tasks):
    try:
        task_ids = []
        for t in pending_tasks[:3]:
            tid = t[0] if isinstance(t, (list, tuple)) else t.get("task_id", t)
            task_ids.append(tid)
        prompt = "执行待处理任务:" + ",".join(task_ids) + "。python3 /root/hermes-agent/agent_comm.py inbox hermes"
        result = subprocess.run(["/root/hermes-agent/venv/bin/hermes", "chat", "-q", prompt], capture_output=True, text=True, timeout=60)
        log("HERMES: trigger done, output=" + result.stdout[:80])
    except subprocess.TimeoutExpired:
        log("HERMES: trigger timeout 60s")
    except Exception as e:
        log(f"HERMES: trigger error: {e}")

def main():
    for agent in ["lobster", "hermes"]:
        try:
            unread = ac.recv_msg(agent)
            pending = ac.task_list(agent, "pending")
            uc = len(unread) if unread else 0
            pc = len(pending) if pending else 0
            if uc > 0 or pc > 0:
                log(f"{agent.upper()}: {uc} unread, {pc} pending -> triggering")
                if agent == "lobster" and pc > 0:
                    trigger_lobster(pending)
                elif agent == "hermes" and pc > 0:
                    trigger_hermes(pending)
        except Exception as e:
            log(f"{agent.upper()}: poll error: {e}")

if __name__ == "__main__":
    main()
